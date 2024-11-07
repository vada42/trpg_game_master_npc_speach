from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.chat_models import ChatOpenAI
from langchain_core.exceptions import OutputParserException
from pydantic import BaseModel, Field

# LLM 및 프롬프트 설정
llm = ChatOpenAI(model_name="gpt-4o", temperature=0.5)

# NPC 대사 정보 모델 정의
class CreateHistoryOutput(BaseModel):
    history: str = Field(description="생성된 요약본")
    mainQuest_judgment: str = Field(description="메인 퀘스트 달성여부")
    subQuest_judgment: list[str] = Field(description="각 서브퀘스트의 달성여부 리스트")

outputparser_create_history = JsonOutputParser(pydantic_object=CreateHistoryOutput)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """당신은 AI 작가입니다.
            당신은 들어오는 대화 기록({history})을 토대로 20자 내외로 요약해야 합니다.
            현재 시나리오는 {detail} 입니다.
            게임 승리 목표는 {mainQuest}입니다.
            게임 보조 목표는 여러 개의 서브퀘스트({subQuest})가 있습니다.
            
            - **게임 목표 달성 시**:
                - 플레이어가 메인 퀘스트({mainQuest})를 달성했으면 **메인 퀘스트 달성**으로 출력하고, 그렇지 않으면 **진행중**을 출력하세요.
                - 각 서브퀘스트에 대해 달성 여부를 개별적으로 판단합니다. 달성된 서브퀘스트는 "서브 퀘스트 '{{subQuest 항목}}' 달성"으로 출력하고, 진행 중인 퀘스트는 "서브 퀘스트 '{{subQuest 항목}}' 진행중"으로 출력하세요.
            출력은 다음과 같이 해야 합니다
            {{
                "history": "생성된 요약본",
                "mainQuest_judgment": "메인 퀘스트 달성여부",
                "subQuest_judgment": "각 서브퀘스트의 달성여부 리스트"
            }} 
         """),
        ("user", "#Format: {format_instructions}\n\n#history:{history}, detail:{detail}, mainQuest:{mainQuest}, subQuest:{subQuest}")
    ]
)

# format_instructions 값 설정
format_instructions = (
    "출력은 JSON 형식으로 제공되어야 하며, 다음과 같은 형식을 따릅니다:\n"
    "{\n"
    "    \"history\": \"생성된 요약본\",\n"
    "    \"mainQuest_judgment\": \"메인 퀘스트 달성여부\",\n"
    "    \"subQuest_judgment\": \"각 서브퀘스트의 달성여부 리스트\"\n"
    "}"
)

# 체인 정의
chain_create_history = prompt.partial(format_instructions=format_instructions) | llm | outputparser_create_history

def create_history(history, detail, mainQuest, subQuest):
    inputs = {
        "history": history,
        "detail": detail,
        "mainQuest": mainQuest,
        "subQuest": subQuest
    }

    try:
        result = chain_create_history.invoke(inputs)
        return result
    except OutputParserException as e:
        print("LLM에서 잘못된 JSON이 반환되었습니다. 텍스트 응답을 후처리합니다.")
        return {"error": "잘못된 JSON 형식의 응답", "response": str(e)}

