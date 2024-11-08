<img src="https://capsule-render.vercel.app/api?type=Venom&color=timeAuto&height=300&section=header&text=GPT%20NPC_Dialogue_generator&fontSize=60" />

<div style="text-align: left;"> 
    <h2 style="border-bottom: 1px solid #d8dee4; color: #282d33;">  </h2>  
    <div style="font-weight: 700; font-size: 15px; text-align: left; color: #282d33;">  </div> 
    </div>
    <div style="text-align: left;">
    <h2 style="border-bottom: 1px solid #d8dee4; color: #282d33;"> 🛠️ Tech Stacks </h2> <br> 
    <div  align= "center"> <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=Python&logoColor=white">
          <img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=PyTorch&logoColor=white">
        <img src="https://img.shields.io/badge/chatGPT-74aa9c?style=for-the-badge&logo=openai&logoColor=white">
    </div>
</div>
    
    
# trpg_game_master_npc_speach

<div style="text-align: left;">
start_Scenario:새로운 게임 시나리오를 시작하는 엔드포인트
방 생성 및 시나리오 정보 저장(scenario_cache)
사용자에게 sessionID와 시나리오 정보를 받는다 받는 시나리오 정보는
title : 제목,
genere : 장르,
mainQuest : 게임 주요목표(승리조건),
subQuest : 게임 보조 목표,
detail : 전체적인 시나리오 내용,
charParts : 시나리오 내 등장인물
worldParts : 시나리오 에서 등장하는 장소
players : 플레이어
이다
scenario_cache 에 사용자에게 받은 시나리오정보와 추가로 history를 생성 후 저장
history는 플레이어의 행적(시나리오를 진행하면서 플레이어가 한 행동, 대화)이 들어간다.
scenario_cache 내부
사용자에게 받은 sessionID:{
	title : 제목,
	genere : 장르,
	mainQuest : 게임 주요목표(승리조건),
	subQuest : 게임 보조 목표,
	detail : 전체적인 시나리오 내용,
	charParts : 시나리오 내 등장인물 +['게임마스터']
	worldParts : 시나리오 에서 등장하는 장소
	players : 플레이어
	history : []
}




startDialog: NPC와의 대화를 시작하는 엔드포인트
npc와 대화가 시작되는 신호가 오면 talking_cache에 sessionID, 플레이어 현재 장소(location), 대화대상(npcName), 플레이어행적(history)을 사용자에게 받아서 저장한다

history는 리스트 형식으로 뒤에서 3번째 까지만 받아온다
talking_cache 에 사용자에게 받은 정보와 추가로 dialog_history 생성 후 저장
dialog_history는 플레이어와 npc의 대화내용이다
talking_cache 내부
사용자에게 받은 sessionID:{
	location : 플레이어 현재 장소,
	npcName : 대화대상,
	players : 플레이어
	history : scenario_cache[sessionID]에서 뒤에서 3개만
	dialog_history: 플레이어와 npc의 대화내용
}




analyze_UserMsg: 사용자의 메시지를 해석하는 엔드포인트
플레이어의 대사.행동(userMsg)에서 '진행', '다이스', '전투' 로 분류한다
다이스로 분류될경우 주사위 펀정이 필요하다는 뜻이고 주사위보정치를 선택해준다




response_Dailog: NPC가 사용자 대사에 대한 답변을 제공하는 엔드포인트
플레이어의 대사.행동(userMsg)을 사용자로부터 받는다.
현재 장소(location), 대화대상(npcName), 플레이어행적(history)을 talking_cache에서 받아온다.
받아온 정보들을 토대로 npc의 대사를 생성, 반환한다
만약 플레이어의 대사.행동(userMsg)이 비어있다면 자동으로 "인사하기" 문구를 저장시킨다.
대화대상(npcName)이 '게임마스터'라면 게임마스터와의 대화하고 그렇지 않으면 해당대화대상과 대화한다
사용자와 대화대상(npcName) 간 나눈대화를 talking_cache 안에 dialog_history에 저장한다




responseDice: 주사위 결과에 따른 NPC 답변을 제공하는 엔드포인트
플레이어의 대사.행동(userMsg)을 사용자로부터 받는다.
추가로 사용자의 주사위판정결과(diceResult), 주사위보정치(bonus)를 사용자에게 받는다
현재 장소(location), 대화대상(npcName), 플레이어행적(history)을 talking_cache에서 받아온다.
받아온 정보들을 토대로 npc의 대사를 생성, 반환한다
만약 플레이어의 대사.행동(userMsg)이 비어있다면 자동으로 "인사하기" 문구를 저장시킨다.
대화대상(npcName)이 '게임마스터'라면 게임마스터와의 대화하고 그렇지 않으면 해당대화대상과 대화한다
사용자와 대화대상(npcName) 간 나눈대화를 talking_cache 안에 dialog_history에 저장한다



end_Dailog: 대화를 종료하고 요약을 생성하는 엔드포인트
사용자에게서 대화종료신호를 받으면 이제까지의 대화(dialog_history)를 통해 요약본을 만든다.
추가로 scenario_cache 안에 있는 mainQuest : 게임 주요목표(승리조건), subQuest : 게임 보조 목표를 받아와서 
목표달성이 됬는지를 판정한다. 요약본이 만들어지고난 후 대화버퍼를 초기화시킨다.



end_Scenario: 게임 세션을 종료하고 캐시를 정리하는 엔드포인트
사용자에게 sessionID를 받으면 scenario_cache에서 sessionID값에 해당되는 정보들을 삭제한다
</div>
