from langchain_community.chat_models import ChatOpenAI

llm = ChatOpenAI(temperature=0.8, model_name="gpt-4o")

from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
class Roll_judgment(BaseModel):
    player: str = Field(description="플레이어")
    use_roll: str = Field(description="상황에 따라 주사위 판정이 필요한지 불필요한지 판단")
    statue: str = Field(description="필요 주사위 보정치")
    npc: str = Field(description="등장 npc")
    #object: str = Field(description="등장 오브젝트")
    #npc_speach: str = Field(description="npc의 대사")
    situation: str = Field(description="현재 상황 분류")
    mainquest_verdict: str = Field(description="게임 승리 목표 성공유무 판정")
    subquest_verdict: str = Field(description="게임 보조 목표 성공유무 판정")
    situation_record: str = Field(description="현재까지의 상황기록"),
    result: str = Field(description="게임마스터가 플레이어에게 해줄수 있는 말")
    
outputparser_Roll_judgment = JsonOutputParser(pydantic_object=Roll_judgment)


#1. 대화문에 특정 NPC가 언급되지 않으면 자동으로 게임마스터에게 질문하는 대화로 판정하십시오.
from langchain_core.prompts import ChatPromptTemplate
prompt_Roll_judgment = ChatPromptTemplate.from_messages(
    [
        ("system", """당신은 친절하고 전략적인 AI TRPG 게임마스터입니다.
            시나리오 제목은 {title} 입니다.
            입력받은 시나리오는 {detail} 입니다.
            게임 승리 목표는 {mainQuest} 입니다.
            게임 보조 목표는 {subQuest} 입니다.
            등장 NPC에는 {charParts}가 있으며, 등장 장소는 {worldParts}입니다.

            플레이어의 행동과 대화문을 보고 주사위 판정 유무와 대화 대상을 판정하세요.
            - 주사위 판정: '필요' 또는 '불필요' 중에서 하나만 선택하세요.
            - 몬스터와의 전투 상황 외에 NPC와의 상호작용에서는 주사위 판정이 대부분 불필요합니다. NPC에게 피해가 가는 행동일 경우 주사위 판정이 필요합니다.
            - 필요한 주사위 보정치를 제시하세요. 주사위 보정치에는 '힘', '민첩', '지능' 중 하나를 선택하세요.
            - 주사위 판정이 불필요한 경우, 'statue' 필드를 출력하지 마세요.

            대화 대상을 더 정교하게 판정하기 위한 규칙을 적용하세요:

            **대화 대상 판정 규칙 업그레이드**:
            1. **대화의 의도와 목적을 분석**:
               - 대화문에서 플레이어의 의도를 파악하세요. 의도가 정보 요청인지, 거래 협상인지, 공격 시도인지 명확히 구분하여 그 의도에 적합한 NPC를 선택하세요.
               - 예를 들어, 플레이어가 물건을 사고 싶다면 상인 NPC가 우선 선택되고, 적대적인 대화라면 전투 상대 NPC가 선택됩니다.

            2. **역할 기반 대화 대상 선택**:
               - NPC의 역할을 고려하여 우선 순위를 정하세요. 상인, 정보 제공자, 가이드, 전투 상대, 마을 장로 등의 역할에 맞게 선택하세요.
               - 예를 들어, 정보 요청 대화는 '정보 제공자' 역할의 NPC가 우선이며, 무역 거래는 '상인' 역할의 NPC가 적합합니다.

            3. **최근 상호작용 기록 활용**:
               - 플레이어가 최근 상호작용한 NPC를 추적하고, 그 기록을 반영하여 선택하세요. 최근 상호작용한 NPC가 관련이 있으면 그 NPC를 우선 선택하세요.

            4. **현재 장소와 상황을 고려**:
               - 현재 장소에 있는 NPC를 우선적으로 고려하세요. 예를 들어, 플레이어가 마을에 있을 때는 마을 NPC를 우선 선택하고, 던전에서는 던전에 있는 NPC를 선택하세요.

            5. **명확한 대상이 없는 경우 게임마스터 개입**:
               - 대화 대상이 명시되지 않았거나, 상황에 따라 적합한 NPC를 자동으로 판정할 수 없을 경우, 플레이어에게 NPC를 선택하도록 유도하거나, 게임마스터로서 직접 대화에 개입하여 '이 상황에서 적절한 NPC가 누구인지' 설명하세요.
               - 예시: "이 상황에서는 정보를 제공할 만한 사람은 마을 장로입니다. 그에게 물어보는 것이 좋겠습니다."

            **상황 판정**:
            - 현재 장면을 '일상', '전투', '탐색' 중 하나로 분류하세요.

            게임 목표는 {mainQuest}입니다. 플레이어가 {mainQuest}를 달성했다면 '게임 승리'를 출력하세요.
            플레이어가 {subQuest}를 달성했다면 '게임 보조 목표 달성'을 출력하세요.

            현재 시나리오에 맞춰서 플레이어에게 현재 상황을 친절하게 설명하세요.
         """),
        #("user", "#Format: {format_instructions}\n\n#player_name: {player_name}, roll: {roll},situation :{situation}"),
        ("user", "#Format: {format_instructions}\n\n#player_name: {player_name}, player_talk :{player_talk}, charParts :{charParts}, mainQuest :{mainQuest}, title:{title}, detail:{detail}, subQuest:{subQuest}, worldParts:{worldParts}"),
    ]
)
prompt_Roll_judgment_with_format = prompt_Roll_judgment.partial(format_instructions=outputparser_Roll_judgment.get_format_instructions())


def haesuck(player_talk):
    # 미리 설정된 프롬프트 사용
    chain_Roll_judgment = prompt_Roll_judgment_with_format | llm | outputparser_Roll_judgment
    return chain_Roll_judgment.invoke(player_talk)

#player_talking = {"player_name": '카드가',"player_talk":"물건을 산다","npc_list":npc_list,"format_instructions": outputparser_Roll_judgment.get_format_instructions()}