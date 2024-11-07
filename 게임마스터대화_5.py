from operator import itemgetter
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, Runnable
from langchain_community.chat_models import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import json

# GameMaster 모델 정의
class Game_master(BaseModel):
    npcMsg: str = Field(description="게임 마스터의 대사")

# JsonOutputParser 설정
outputparser_Game_master_speach = JsonOutputParser(pydantic_object=Game_master)

# ChatOpenAI 모델 초기화
llm = ChatOpenAI(model_name="gpt-4", temperature=1)

# 대화형 프롬프트 생성
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """당신은 친절한 TRPG 게임마스터입니다.
                    플레이어의 질문에 친절하고 구체적으로 답변해주세요. 
                    특히 플레이어가 조언을 구하는 경우, 상황에 맞는 구체적인 조언을 제공하세요. 
                    전략적인 조언이나 행동을 추천해줄 때는 플레이어가 현재 직면한 문제나 상황을 고려하여 실질적인 도움을 주는 방식으로 설명하세요.
                    **시나리오 정보**:
                    - 시나리오 제목: {title}
                    - 시나리오 설명: {detail}
                    - 게임 승리 목표: {mainQuest}
                    - 게임 보조 목표: {subQuest}
                    - 등장 NPC: {charParts}
                    - 등장 장소: {worldParts}
         
                    **게임 진행 규칙**:
                    1. 플레이어가 시나리오의 목표와 관계없는 엉뚱한 행동이나 대화를 시도할 경우, 자연스럽고 논리적으로 이를 거절하거나 유도하세요.
                    2. 플레이어가 설정된 장소({worldParts}에 포함되지 않은 장소)로 가려 할 경우, 해당 장소가 접근 불가한 이유를 설명하고, 대체 가능한 장소를 제안하세요. 예를 들어, 특정 장소가 폐쇄되었거나 출입이 제한된 지역임을 알리며, 대신 방문할 수 있는 장소를 제시하세요.
                    3. 게임 마스터와 전투하는 상황은 발생할 수 없습니다.

                    **플레이어의 최근 행적**:
                    지금까지 플레이어가 선택하거나 수행한 주요 행적은 다음과 같습니다: {history}
                    플레이어의 행적을 참고하여, 선택의 연속성과 일관성을 반영하여 응답하세요.

                    **다이스 판정 결과**:
                    - 현재 다이스 판정 결과는 **"{success_or_failure}"** 입니다. 만약 "없음"일 경우, 이 항목을 무시해도 됩니다. 결과에 맞춰 적절하게 게임의 진행을 유도하세요.
                    - 현재 다이스 판정에서 사용된 능력치는 **"{bonus}"** 입니다. 만약 "없음"일 경우, 이 항목을 무시해도 됩니다.
                    - 예를 들어, 성공이라면 게임마스터는 긍정적인 반응을 통해 플레이어의 행동에 힘을 실어주거나, 유리한 상황으로 흐르게 유도할 수 있습니다.
                    - 실패라면, 게임의 난이도를 조금 올리거나, 상황이 복잡해지도록 만들어 플레이어가 도전에 직면하도록 하세요.

                    위 규칙에 따라 플레이어가 몰입할 수 있도록 자연스럽게 이야기를 이끌어주세요.
                    출력은 다음과 같이 해야 합니다:
                    {{
                       "npcMsg": "게임마스터의 대사"
                    }}
                    """),
        MessagesPlaceholder(variable_name="game_master_chat_history"),
        ("user", "#Format: {format_instructions}\n\n# player_talk: {player_talk}, charParts: {charParts}, mainQuest: {mainQuest}, title: {title}, detail: {detail}, subQuest: {subQuest}, worldParts: {worldParts}, success_or_failure:{success_or_failure}, bonus:{bonus}")
    ]
)

prompt_gamemaster_talk_out = prompt.partial(format_instructions=outputparser_Game_master_speach.get_format_instructions())

# 메모리 생성
gm_memory = ConversationBufferMemory(return_messages=True, memory_key="game_master_chat_history")

# 대화 체인 정의
class MyConversationChain(Runnable):

    def __init__(self, llm, prompt, memory, input_key="input", memory_limit=50):
        self.prompt = prompt
        self.memory = memory
        self.input_key = input_key
        self.memory_limit = memory_limit
        self.chain = (
            RunnablePassthrough.assign(
                game_master_chat_history=RunnableLambda(self.memory.load_memory_variables)
                | itemgetter(memory.memory_key)
            )
            | self.prompt
            | llm
            | outputparser_Game_master_speach
        )

    def invoke(self, query, configs=None, **kwargs):
        # 필요한 변수를 포함한 딕셔너리 생성
        query_data = {
            "player_talk": query.get("player_talk", "unknown player talk"),
            "mainQuest": query.get("mainQuest", "scenario mainQuest"),
            "subQuest": query.get("subQuest", "scenario subQuest"),
            "title": query.get("title", "scenario title"),
            "detail": query.get("detail", "scenario detail"),
            "worldParts": query.get("worldParts", "scenario worldParts"),
            "charParts": query.get("charParts", "scenario charParts"),
            "history": query.get("history", "history"),
            "success_or_failure": query.get("success_or_failure", "success or failure"),
            "bonus": query.get("bonus", "bonus"),
            "format_instructions": "Provide a JSON response"
        }

        # 메모리 한도 초과 시 초기화
        if len(self.memory.chat_memory.messages) > self.memory_limit:
            self.memory.clear()  # 메모리 초기화
            print(f"메모리가 {self.memory_limit}개의 메시지를 초과하여 초기화되었습니다.")
        
        # 체인 실행 및 응답 처리
        answer = self.chain.invoke(query_data)

        # 메모리에 대화 기록 저장
        self.memory.save_context(
            inputs={"human": json.dumps(query_data, ensure_ascii=False)},
            outputs={"ai": json.dumps(answer, ensure_ascii=False)}
        )
        
        return answer

# 대화 체인 인스턴스 생성
conversation_chain = MyConversationChain(llm=llm, prompt=prompt, memory=gm_memory)

# 대화 함수 정의
def game_master_talking(userMsg, charParts, mainQuest, subQuest, title, detail, worldParts, diceResult, bonus, history):
    query = {
        "player_talk": userMsg,
        "charParts": charParts,
        "mainQuest": mainQuest,
        "subQuest": subQuest,
        "title": title,
        "detail": detail,
        "worldParts": worldParts,
        "success_or_failure": diceResult,
        "bonus": bonus,
        "history": history
    }

    # 대화 실행
    response = conversation_chain.invoke(query)
    
    # 응답 처리
    if isinstance(response, dict):
        response_dict = response
    else:
        try:
            response_dict = json.loads(response)
        except json.JSONDecodeError:
            print("응답이 JSON 형식이 아닙니다.")
            response_dict = {}

    return response

