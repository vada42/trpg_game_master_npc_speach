from langchain_community.chat_models import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

# ChatOpenAI 모델 설정
llm = ChatOpenAI(temperature=0, model_name="gpt-4o")

# Output Parser 클래스 정의
class Roll_judgment(BaseModel):
    bonus: str = Field(description="필요 주사위 보정치")
    event: str = Field(description="현재 상황 분류")

outputparser_Roll_judgment = JsonOutputParser(pydantic_object=Roll_judgment)

# ChatPromptTemplate 설정
prompt_Roll_judgment = ChatPromptTemplate.from_messages(
    [
        ("system", """당신은 친절하고 전략적인 AI TRPG 게임마스터입니다.

             - **주사위 판정 유무**:
                    상황에 따라 플레이어의 행동에 주사위 판정이 필요한지 불필요한지 명확히 판단하세요.
                    전투 상황이나 NPC에게 피해를 주는 행동이 있을 때는 주사위 판정이 필요하며, 일상적인 대화나 상호작용에서는 대부분 불필요합니다.
                    만약 주사위 판정이 필요하다면, '생명력', '힘', '손재주' 중 적절한 보정치를 선택하세요.
                    만약 주사위 판정이 필요하지 않으면, '없음'을 선택하세요.

             - **상황 분류 지침**:
                    - 현재 상황을 '진행', '다이스', 또는 '전투' 중 하나로 분류하여 응답하세요.
                    - 기본적으로 '진행' 상황을 선택하세요.
                    - 플레이어의 행동이 주사위 판정이 필요한 경우 상황을 '다이스'로 분류하고, 필요한 경우 보정치(`health`, `strength`, `dex` 중 하나)를 판단해 주세요.
                    - 플레이어의 행동이 전투 상황으로 이어지면, '전투'로 분류하고 적절한 전투 반응을 보여주세요.
         
        """),
        ("user", "#Format: {format_instructions}\n\nplayer_talk: {player_talk}")
    ]
)

# format_instructions 적용
prompt_Roll_judgment_with_format = prompt_Roll_judgment.partial(format_instructions=outputparser_Roll_judgment.get_format_instructions())

# 함수 정의
def haesuck(talk):
    # 미리 설정된 프롬프트 사용
    chain_Roll_judgment = prompt_Roll_judgment_with_format | llm | outputparser_Roll_judgment
    result = chain_Roll_judgment.invoke(talk)
    
    # result가 Pydantic 모델인 경우 .dict()를 사용해 필터링하고, 딕셔너리인 경우 그대로 필터링
    if isinstance(result, Roll_judgment):
        output = {k: v for k, v in result.dict().items() if v}
    elif isinstance(result, dict):
        output = {k: v for k, v in result.items() if v}
    else:
        output = {}

    return output

#player_talking = {"player_name": '카드가',"player_talk":"물건을 산다","npc_list":npc_list,"format_instructions": outputparser_Roll_judgment.get_format_instructions()}


#현재 대화 대상은{npc}입니다.
#            플레이어가 시나리오에 맞지않는 엉뚱한 행동이나 대화를 하게 되면, 자연스럽고 논리적으로 거절해주세요.
#            플레이어가 시나리오에 포함되지 않은 장소({worldParts}에 없는 장소)로 가려는 경우,
#            해당 장소가 접근 불가한 이유를 들어 자연스럽고 논리적으로 거절하세요.
#            예를 들어, 그 장소가 폐쇄되었거나 출입이 제한된 지역임을 설명하고, 대체 장소를 제안하세요.
#mainquest_verdict: str = Field(description="게임 승리 목표 성공유무 판정")
#subquest_verdict: str = Field(description="게임 보조 목표 성공유무 판정")
#- **게임 목표**:
#                - 주요 목표: {mainQuest} (달성 시 '주요목표 달성'을 선언하고, 달성되지 않은 경우 '진행중'으로 표시하세요.)
#                - 보조 목표: {subQuest} (달성 시 '보조목표 달성'을 선언하고, 달성되지 않은 경우 '진행중'으로 표시하세요.)