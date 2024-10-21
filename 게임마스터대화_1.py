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
    game_master_speach: str = Field(description="게임 마스터의 대사")
    situation_record: str = Field(description="현재까지의 상황 기록", default="")

# JsonOutputParser 설정
outputparser_Game_master_speach = JsonOutputParser(pydantic_object=Game_master)

# ChatOpenAI 모델을 초기화합니다.
llm = ChatOpenAI(model_name="gpt-4", temperature=0)

# 대화형 프롬프트 생성
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """당신은 친절한 TRPG 게임마스터입니다.
                    플레이어의 질문에 친절하고 구체적으로 답변해주세요. 
                    특히 플레이어가 조언을 구하는 경우, 상황에 맞는 구체적인 조언을 제공하세요. 
                    전략적인 조언이나 행동을 추천해줄 때는 플레이어가 현재 직면한 문제나 상황을 고려하여 실질적인 도움을 주는 방식으로 설명하세요.
                    시나리오 제목은 {title}입니다.
                    입력받은 시나리오는 {detail}입니다.
                    게임 승리 목표는 {mainQuest}입니다.
                    게임 보조 목표는 {subQuest}입니다.
                    등장 NPC에는 {charParts}이 있습니다.
                    등장 장소는 {worldParts}가 있습니다.

                    플레이어가 NPC의 역할에 맞지 않는 엉뚱한 행동이나 대화를 하게 되면, 자연스럽고 논리적으로 거절해주세요.
                    게임 마스터와는 전투를 할 수 없습니다.

                    이제까지 {scenario_record}가 있었습니다.
                    기록을 반영해서 답변해주세요.

                    게임 목표는 {mainQuest}입니다. 만약 플레이어의 행동이 {mainQuest}를 달성했다고 판정이 되면 '게임 승리'를 출력해야 합니다.
                    게임 보조 목표는 {subQuest}입니다. 만약 플레이어의 행동이 {subQuest}를 달성했다고 판정이 되면 '게임 보조 목표 달성'을 출력해야 합니다.

                    이제까지의 대화를 통해 상황을 요약해주세요.
                    출력은 다음과 같이 해야 합니다:
                    {{
                       "game_master_speach": "게임 마스터의 대사",
                       "situation_record": "게임 마스터가 플레이어에게 전달하는 상황 설명"
                    }}
        """),
        MessagesPlaceholder(variable_name="game_master_chat_history"),
        ("user", "#Format: {format_instructions}\n\n# player_talk: {player_talk}, charParts: {charParts}, mainQuest: {mainQuest}, title: {title}, detail: {detail}, subQuest: {subQuest}, worldParts: {worldParts}, scenario_record: {scenario_record}")
    ]
)


prompt_gamemaster_talk_out = prompt.partial(format_instructions=outputparser_Game_master_speach.get_format_instructions())

# 메모리 생성
memory = ConversationBufferMemory(return_messages=True, memory_key="game_master_chat_history")

# 대화 체인 정의
class MyConversationChain(Runnable):

    def __init__(self, llm, prompt, memory, input_key="input", memory_limit=100):
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
            "mainQuest": query.get("mainQuest", "senario mainQuest"),
            "subQuest": query.get("subQuest", "senario subQuest"),
            "title": query.get("title", "senario title"),
            "detail": query.get("detail", "senario detail"),
            "worldParts" : query.get("worldParts", "senario worldParts"),
            "charParts": query.get("charParts", "senario charParts"),
            "scenario_record" : query.get("scenario_record", "scenario_record"),
            "format_instructions": "Provide a JSON response"
        }
        if len(self.memory.chat_memory.messages) > self.memory_limit:
            self.memory.clear()  # 메모리 초기화
            print(f"메모리가 {self.memory_limit}개의 메시지를 초과하여 초기화되었습니다.")
        # 체인 실행 및 응답 처리
        answer = self.chain.invoke(query_data)

        # 응답에서 talk_start_end가 "끝"이면 메모리 초기화
        #if isinstance(answer, dict) and answer.get("talk_start_end") == "끝":
        #    self.memory.clear()  # 메모리 초기화

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
def game_master_talking(player_talk, charParts, mainQuest, subQuest, title, detail, worldParts, scenario_record):
    query = {
        "player_talk": player_talk,
        "charParts": charParts,
        "mainQuest": mainQuest,
        "subQuest": subQuest,
        "title": title,
        "detail": detail,
        "worldParts": worldParts,
        "scenario_record": scenario_record,
        "history": dialogues
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