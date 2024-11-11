from operator import itemgetter
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, Runnable
from langchain_community.chat_models import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import json

# NPC 대사 정보 모델 정의
class npc_talk(BaseModel):
    npcMsg: str = Field(description="npc의 대사")

outputparser_npc_talk = JsonOutputParser(pydantic_object=npc_talk)

# LLM 및 프롬프트 설정
llm = ChatOpenAI(model_name="gpt-4o", temperature=1)

# 대화형 프롬프트 정의
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """당신은 TRPG 게임 세계에서 {location}에 거주하는 {npc}을 연기하는 배우입니다. 
        {npc} 에게 시나리오는 {detail} 입니다
        플레이어와 자연스럽고 몰입감 있는 상호작용을 하세요. 
        해당 배역에 맞춰 연기해 주십시오. 

        이제까지의 대화 기록을 반영해서 답변해주세요: {chat_history}
        
        **추가적인 규칙**:
        1. **플레이어의 선택에 따른 유연한 대화 진행**: 대화가 자연스럽게 흐르도록 하고, 플레이어의 선택이나 행동에 따라 대화를 유연하게 조정하세요. 대화가 예측 불가능한 방향으로 흘러가더라도 NPC는 상황을 논리적으로 대응하며 이어갈 수 있어야 합니다.
        2. **대화의 목적 파악**: 플레이어가 질문을 하거나 요청을 할 때, NPC는 그 목적을 정확히 파악하고, 관련된 정보나 조언을 제공하세요. 만약 NPC가 직접 도움을 줄 수 없다면, 상황에 맞는 다른 NPC나 장소로 연결해 주세요.
        3. **NPC의 감정과 태도 반영**: NPC의 성격(예: 냉정함, 친절함, 적대적 태도)을 대화에 반영하고, 플레이어가 NPC와의 상호작용에서 영향을 미칠 수 있도록 하세요.
        4. **상호작용 종료 및 거절 표현**: 대화가 끝날 때는 NPC가 더 이상 제공할 정보나 도움이 없음을 명확히 하세요. 또한, 플레이어가 NPC 역할에 맞지 않는 질문이나 행동을 요청할 경우, 이를 논리적이고 친절하게 거절하세요.
        5. **NPC의 행동 논리 강화**: NPC가 왜 그런 행동을 했는지, 왜 그런 대답을 하는지를 플레이어에게 설명할 수 있도록 하세요.

        **다이스 판정 결과**:
        - 현재 다이스 판정 결과는 **"{success_or_failure}"** 입니다. 
            - **성공**: 다이스 판정이 성공일 경우, {npc}는 플레이어에게 우호적인 태도를 보이거나, 추가적인 정보나 도움을 제공하는 등 협력적인 반응을 보입니다. 예를 들어, {npc}는 플레이어의 능력을 인정하고, 칭찬이나 격려를 통해 신뢰를 심어줄 수 있습니다.
            - **실패**: 다이스 판정이 실패일 경우, {npc}는 플레이어에게 다소 냉담하거나 주저하는 반응을 보일 수 있으며, 실패한 상황에 따른 불이익을 암시할 수 있습니다. 예를 들어, {npc}는 신뢰를 완전히 주지 않거나, 추가적인 노력을 요구할 수 있습니다. 실패를 만회할 수 있는 다른 방법이나 힌트를 {npc}가 제시하도록 하세요.
            - **없음**: 다이스 판정 결과가 "없음"일 경우, 다이스 판정 결과를 고려하지 않고, 기본 상호작용을 유지하며 플레이어의 행동에 논리적으로 반응하세요.
        
        **플레이어의 최근 행적**:
                    지금까지 플레이어가 선택하거나 수행한 주요 행적은 다음과 같습니다: {history}
                    플레이어의 행적을 참고하여, 선택의 연속성과 일관성을 반영하여 응답하세요.
            
        - 현재 다이스 판정에서 사용된 능력치는 **"{bonus}"** 입니다.
            - **없음**: 능력치가 "없음"일 경우, 능력치의 사용을 고려하지 않고, 자연스럽게 상호작용을 이어가세요.
            - 특정 능력치가 사용된 경우, 성공 시 해당 능력치의 중요성을 칭찬하거나 강조하고, 실패 시 그 능력치를 향상할 필요가 있음을 NPC가 시사할 수 있습니다.

        위 규칙에 따라 몰입감 있고 일관된 NPC의 반응을 보여주세요.
        출력은 다음과 같이 해야 합니다:
                    {{
                       "npcMsg": "{npc}의 대사"
                    }}
        """),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "#Format: {format_instructions}\n\n#npc: {npc}, location: {location}, player_talk: {player_talk}, detail: {detail}, success_or_failure:{success_or_failure}, bonus:{bonus}, history:{history}")
    ] 
)

prompt_npc_talk_out = prompt.partial(format_instructions=outputparser_npc_talk.get_format_instructions())

# 메모리 생성
memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")

# 대화 체인 정의
class MyConversationChain(Runnable):

    def __init__(self, llm, prompt, memory, input_key="input", memory_limit=50):
        self.prompt = prompt
        self.memory = memory
        self.input_key = input_key
        self.memory_limit = memory_limit
        self.chain = (
            RunnablePassthrough.assign(
                chat_history=RunnableLambda(self.memory.load_memory_variables)
                | itemgetter(memory.memory_key)
            )
            | self.prompt
            | llm
            | outputparser_npc_talk
        )

    def invoke(self, query, configs=None, **kwargs):
        # 필요한 변수를 포함한 딕셔너리 생성
        query_data = {
            "npc": query.get("npc", "unknown npc"),
            "player_talk": query.get("player_talk", "unknown player talk"),
            "detail": query.get("detail", "applicable scenario"),
            "location": query.get("location", "Current Player Location"),
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
conversation_chain = MyConversationChain(llm=llm, prompt=prompt, memory=memory)

def npc_talking(npcName, userMsg, detail, location, diceResult, bonus, history):
    query = {
        "npc": npcName,
        "player_talk": userMsg,
        "detail": detail,
        "location": location,
        "success_or_failure": diceResult,
        "bonus": bonus,
        "history": history
    }

    # 대화 실행
    response = conversation_chain.invoke(query)
    print(response)

    # 응답 처리
    if isinstance(response, dict):
        # 이미 사전 타입일 경우 직접 'npcMsg' 추출
        response_text = response.get("npcMsg", "응답에 오류가 있습니다.")
    else:
        try:
            # 문자열일 경우 JSON 로드 후 'npcMsg' 추출
            response_dict = json.loads(response)
            response_text = response_dict.get("npcMsg", "응답에 오류가 있습니다.")
        except json.JSONDecodeError:
            print("응답이 JSON 형식이 아닙니다.")
            response_text = "응답 처리 중 오류가 발생했습니다."

            
    # 메모리에 저장된 대화 내역을 문자열로 저장
    dialog_history = "\n".join(
        f"User: {message.content}"
        for message in conversation_chain.memory.chat_memory.messages
    )

    return response, dialog_history

