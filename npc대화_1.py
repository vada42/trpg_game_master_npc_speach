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
    use_roll: str = Field(description="상황에 따라 주사위 판정이 필요한지 불필요한지 판단")
    statue: str = Field(description="필요 주사위 보정치")
    npc: str = Field(description="등장 npc")
    object: str = Field(description="등장하는 물건")
    npc_speach: str = Field(description="npc의 대사")
    situation: str = Field(description="현재 상황 분류")
    situation_record: str = Field(description="게임마스터가 플레이어에게 해줄 수 있는 말")
    talk_start_end: str = Field(description="대화의 시작, 중간, 끝 중 하나")
    mainquest_verdict: str = Field(description="게임 승리 목표 성공유무 판정")
    subquest_verdict: str = Field(description="게임 보조 목표 성공유무 판정")

outputparser_npc_talk = JsonOutputParser(pydantic_object=npc_talk)

# LLM 및 프롬프트 설정
llm = ChatOpenAI(model_name="gpt-4o", temperature=0)

# 대화형 프롬프트 정의
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """당신은 TRPG 게임 세계에서 등장하는 {npc}을 연기하는 배우입니다. 
        {player}와 자연스럽고 몰입감 있는 상호작용을 하세요. 
        해당 배역에 맞춰 연기해 주십시오. 

        - **대화의 시작, 중간, 끝을 명확하게 구분하고, 각 단계에 맞춰 자연스럽게 대화를 이끌어 가세요.**
        - **시작**: 플레이어가 첫 질문이나 요청을 했을 때, NPC의 첫 반응을 신중하게 선택하세요. NPC의 성격(친절, 적대적, 중립 등), 현재 상황, NPC가 처한 배경 등을 고려해 초기 반응을 정하세요. 플레이어에게 적절한 정보를 제공하거나, 다음 대화로 자연스럽게 이어질 수 있는 길을 만드세요.
        - **중간**: 대화가 진행되면서 플레이어의 추가 질문이나 요구 사항에 따라 NPC의 반응을 심화시키세요. NPC의 의도를 드러내거나, 플레이어와의 관계를 발전시킬 수 있는 기회를 활용하세요. 정보 제공, 도움 제공, 갈등 유발, 협박 등의 반응을 NPC의 성격에 맞춰 진행하세요.
        - **끝**: 대화의 마지막 부분에서는 NPC가 대화를 마무리하며 플레이어에게 필요한 마지막 정보를 제공하거나, 상황에 따라 대화를 끝낼 이유를 제시하세요. 더 이상의 상호작용이 필요하지 않다면, 자연스럽게 대화를 끝내는 방향으로 유도하세요.

        - **주사위 판정 유무**:
        상황에 따라 플레이어의 행동에 주사위 판정이 필요한지 불필요한지 명확히 판단하세요. 전투 상황이나 NPC에게 피해를 주는 행동이 있을 때는 주사위 판정이 필요하며, 일상적인 대화나 상호작용에서는 대부분 불필요합니다. 만약 주사위 판정이 필요하다면, '힘', '민첩', '지능' 중 적절한 보정치를 선택하세요.

        출력 형식은 다음과 같습니다:
        {{
            "use_roll": "필요" 또는 "불필요",
            "statue": "힘", "민첩", "지능 중 하나 (필요할 때만)",
            "npc": "{npc}",
            "player": "{player}",
            "object": "등장하는 물건",
            "talk_start_end": "시작", "중간", "끝 중 하나",
            "npc_speach": "npc의 대사",
            "situation": "일상", "전투", "탐색 중 하나",
            "situation_record": "게임마스터가 플레이어에게 전달하는 상황 설명"
        }}

        - **게임 목표 달성 시 대화 반영**:
        - 만약 플레이어가 **메인 퀘스트({mainQuest})를 달성했다면**, NPC는 그 상황을 인지하고 이에 맞는 대사를 출력하세요. 예를 들어, 메인 퀘스트가 달성되었다는 사실을 칭찬하거나, 플레이어에게 축하의 말을 건네세요. 그에 따라 '게임 승리'를 출력하세요.
        - 만약 플레이어가 **서브 퀘스트({subQuest})를 달성했다면**, NPC는 그 상황을 반영하여 대사를 출력하세요. 예를 들어, NPC가 플레이어에게 추가적인 보상을 주거나, 서브 퀘스트 완료를 축하하는 반응을 보여야 합니다. 그에 따라 '게임 보조 목표 달성'을 출력하세요.

        **추가적인 규칙**:
        1. **플레이어의 선택에 따른 유연한 대화 진행**: 대화가 자연스럽게 흐르도록 하고, 플레이어의 선택이나 행동에 따라 대화를 유연하게 조정하세요. 대화가 예측 불가능한 방향으로 흘러가더라도 NPC는 상황을 논리적으로 대응하며 이어갈 수 있어야 합니다.
        2. **대화의 목적 파악**: 플레이어가 질문을 하거나 요청을 할 때, NPC는 그 목적을 정확히 파악하고, 관련된 정보나 조언을 제공하세요. 만약 NPC가 직접 도움을 줄 수 없다면, 상황에 맞는 다른 NPC나 장소로 연결해 주세요.
        3. **NPC의 감정과 태도 반영**: NPC의 성격(예: 냉정함, 친절함, 적대적 태도)을 대화에 반영하고, 플레이어가 NPC와의 상호작용에서 영향을 미칠 수 있도록 하세요. 예를 들어, 적대적인 NPC는 정보를 제공하기 전에 협박하거나, 플레이어의 태도에 따라 변할 수 있습니다.
        4. **상호작용 종료**: 대화가 끝날 때는 NPC가 더 이상 제공할 정보나 도움이 없음을 명확히 하세요. 이때, 대화를 자연스럽게 종료하거나, 플레이어에게 다른 목표나 선택지를 제시하세요. NPC가 도움을 줄 수 없는 경우에는 그 이유를 논리적으로 설명하세요.
        5. **NPC의 행동 논리 강화**: NPC가 왜 그런 행동을 했는지, 왜 그런 대답을 하는지를 플레이어에게 설명할 수 있도록 하세요. NPC의 동기와 목표를 명확히 하여, NPC의 말과 행동이 일관되게 보이도록 연기하세요.

        **상황별 특수 규칙**:
        - **일상 상황**: 플레이어와 NPC가 일상적인 대화를 나눌 때는 NPC가 편안하고 자연스럽게 대화를 이어나가도록 하고, 중요한 정보는 그 과정에서 자연스럽게 드러나야 합니다.
        - **전투 상황**: 전투 상황에서는 NPC가 플레이어의 적대적 행동에 따라 즉각적으로 반응하며, 필요할 경우 주사위 판정을 요청하고 그 결과에 따라 대화나 행동을 조정하세요.
        - **탐색 상황**: 탐색 중이라면 NPC는 플레이어에게 탐색과 관련된 힌트를 제공하거나, 중요한 장소나 아이템에 대한 정보를 줄 수 있습니다.

        게임 목표는 {mainQuest}입니다. 플레이어가 {mainQuest}를 달성했다면 '게임 승리'를 출력하세요.
        플레이어가 {subQuest}를 달성했다면 '게임 보조 목표 달성'을 출력하세요.
        """),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "#Format: {format_instructions}\n\n#npc: {npc}, player: {player}, player_talk: {player_talk}, history: {history}, mainQuest:{mainQuest}, subQuest:{subQuest}")
    ] 
)

prompt_npc_talk_out = prompt.partial(format_instructions=outputparser_npc_talk.get_format_instructions())

# 메모리 생성
memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")

# 대화 체인 정의
class MyConversationChain(Runnable):

    def __init__(self, llm, prompt, memory, input_key="input"):
        self.prompt = prompt
        self.memory = memory
        self.input_key = input_key
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
            "player": query.get("player", "player name"),
            "player_talk": query.get("player_talk", "unknown player talk"),
            "history" : query.get("history", "conversation record"),
            "mainQuest" : query.get("mainQuest", "mainQuest_verdict"),
            "subQuest" : query.get("subQuest", "subQuest_verdict"),
            "format_instructions": "Provide a JSON response"
        }

        # 체인 실행 및 응답 처리
        answer = self.chain.invoke(query_data)

        # 응답에서 talk_start_end가 "끝"이면 메모리 초기화
        if isinstance(answer, dict) and answer.get("talk_start_end") == "끝":
            self.memory.clear()  # 메모리 초기화

        # 메모리에 대화 기록 저장
        self.memory.save_context(
            inputs={"human": json.dumps(query_data, ensure_ascii=False)},
            outputs={"ai": json.dumps(answer, ensure_ascii=False)}
        )
        return answer

# 대화 체인 인스턴스 생성
conversation_chain = MyConversationChain(llm=llm, prompt=prompt, memory=memory)

# 대화 기록 리스트
dialogues = []

# 대화 함수 정의
def talking(npc, player, player_talk, mainQuest, subQuest):
    query = {
        "npc": npc,
        "player": player,
        "player_talk": player_talk,
        "history": dialogues,
        "mainQuest":mainQuest,
        "subQuest":subQuest
    }

    # 대화 실행
    response = conversation_chain.invoke(query)
    
    # 대화 기록 업데이트
    contents = [message.content for message in memory.chat_memory.messages]

    # 응답 처리
    if isinstance(response, dict):
        response_dict = response
    else:
        try:
            response_dict = json.loads(response)
        except json.JSONDecodeError:
            print("응답이 JSON 형식이 아닙니다.")
            response_dict = {}

    # 대화 기록 추가
    if "npc_speach" in response_dict and "player_talk" in query:
        dialogues.append({
            "player_talk": query["player_talk"],
            "npc_speach": response_dict["npc_speach"]
        })

    # 메모리에서 대화 기록 불러오기
    for message in memory.chat_memory.messages:
        content = message.content
        try:
            content_dict = json.loads(content)
            if "player_talk" in content_dict and "npc_speach" in content_dict:
                dialogues.append({
                    "player_talk": content_dict["player_talk"],
                    "npc_speach": content_dict["npc_speach"]
                })
        except json.JSONDecodeError:
            continue

    return response