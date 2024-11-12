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
<br/>
<br/>
<br/>
main_1_9.py, npc대화_6.py, 게임마스터대화_5.py, 히스토리생성.py, 해석모듈_6.py, 키워드필터링.py, create_End_detail.py, create_npc_detail.py<br/>
를 사용하십시오
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<img width="844" alt="image" src="https://github.com/user-attachments/assets/5c4f29d6-44da-431a-a819-f0e91828e7d9">
<br/>
start_Scenario:새로운 게임 시나리오를 시작하는 엔드포인트<br/>
방 생성 및 시나리오 정보 저장(scenario_cache)<br/>
사용자에게 sessionID와 시나리오 정보를 받는다 받는 시나리오 정보는
```
title : 제목,
genere : 장르,
mainQuest : 게임 주요목표(승리조건),
subQuest : 게임 보조 목표,
detail : 전체적인 시나리오 내용,
charParts : 시나리오 내 등장인물
worldParts : 시나리오 에서 등장하는 장소
players : 플레이어
```
<br/>
<br/>
scenario_cache 에 사용자에게 받은 시나리오정보와 추가로 history를 생성 후 저장<br/>
history는 플레이어의 행적(시나리오를 진행하면서 플레이어가 한 행동, 대화)이 들어간다.<br/>
scenario_cache 내부

```
사용자에게 받은 sessionID:{
	title : 제목,
	genere : 장르,
	mainQuest : 게임 주요목표(승리조건),
	subQuest : 게임 보조 목표,
	detail : 전체적인 시나리오 내용,
	charParts : 시나리오 내 등장인물 +['게임마스터'],
	worldParts : 시나리오 에서 등장하는 장소,
	players : 플레이어,
	history : []
}
```
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<img width="787" alt="image" src="https://github.com/user-attachments/assets/11e6b89e-781a-4d6e-b4e9-b421dfbd5838">
<br/>
create_NPC_detail:
npc 와 대화할때 전체 시나리오(detail)을 전부 사용하면 입력 초과가 생길수 있기 때문에 전체 시나리오에서 해당 npc 와 관련된 부분만 따로 추출해서(create_NPC_detail) 사용한다<br/>
추출후 생성된 char_dic은 scenario_cache 내부에 들어간다

```
사용자에게 받은 sessionID:{
	title : 제목,
	genere : 장르,
	mainQuest : 게임 주요목표(승리조건),
	subQuest : 게임 보조 목표,
	detail : 전체적인 시나리오 내용,
	charParts : 시나리오 내 등장인물 +['게임마스터'],
	worldParts : 시나리오 에서 등장하는 장소,
	players : 플레이어,
	history : [],
	char_dic:{
	왕자 : [왕자_detail_1, 왕자_detail_2,왕자_detail_3,...],
	마왕 : [마왕_detail_1, 마왕_detail_2,마왕_detail_3,...],
	상인 : [상인_detail_1, 상인_detail_2,상인_detail_3,...],
				.
				.
				.
	}
}
```

<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<img width="766" alt="image" src="https://github.com/user-attachments/assets/1d659166-1c42-4197-9609-f5f2e85a60ff">
<br/>
create_end_detail:
end_dailog 를 실행할때 전체 시나리오를 전부 사용하는 것은 과용이기 때문에 전체 시나리오에서 mainquest 와 subquest가 관련된 부분만 따로 추출해서(create_end_detail) 사용한다<br/>
추출후 생성된 end_detail scenario_cache 내부에 들어간다

```
사용자에게 받은 sessionID:{
	title : 제목,
	genere : 장르,
	mainQuest : 게임 주요목표(승리조건),
	subQuest : 게임 보조 목표,
	detail : 전체적인 시나리오 내용,
	charParts : 시나리오 내 등장인물 +['게임마스터'],
	worldParts : 시나리오 에서 등장하는 장소,
	players : 플레이어,
	history : [],
	char_dic:{
	왕자 : [왕자_detail_1, 왕자_detail_2,왕자_detail_3,...],
	마왕 : [마왕_detail_1, 마왕_detail_2,마왕_detail_3,...],
	상인 : [상인_detail_1, 상인_detail_2,상인_detail_3,...],
				.
				.
				.
	},
	end_detail: end_dailog를 실행할때 사용할 detail
}
```

<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<img width="836" alt="start_Dialog" src="https://github.com/user-attachments/assets/503fa82d-7953-47bc-ab5d-6b0f39fe1f3d">
<br/>
startDialog: NPC와의 대화를 시작하는 엔드포인트<br/>
npc와 대화가 시작되는 신호가 오면 talking_cache에 sessionID, 플레이어 현재 장소(location), 대화대상(npcName), 플레이어행적(history)을 사용자에게 받아서 저장한다<br/>
history는 리스트 형식으로 뒤에서 3번째 까지만 받아온다<br/>
talking_cache 에 사용자에게 받은 정보와 추가로 dialog_history 생성 후 저장<br/>
dialog_history는 플레이어와 npc의 대화내용이다

```
talking_cache 내부
사용자에게 받은 sessionID:{
	location : 플레이어 현재 장소,
	npcName : 대화대상,
	userMsg : 플레이어 대사
	history : scenario_cache[sessionID]에서 뒤에서 3개만
	dialog_history: 플레이어와 npc의 대화내용
}
```

<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<img width="716" alt="analyze_UserMsg" src="https://github.com/user-attachments/assets/b5f97d3a-b05a-429f-a572-b15888a34495">
<br/>
analyze_UserMsg: 사용자의 메시지를 해석하는 엔드포인트<br/>
플레이어의 대사.행동(userMsg)에서 '진행', '다이스', '전투' 로 분류한다<br/>
다이스로 분류될경우 주사위 펀정이 필요하다는 뜻이고 주사위보정치를 선택해준다<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<img width="781" alt="image" src="https://github.com/user-attachments/assets/31766329-c43e-4877-abfc-9505e4836d43">
<br/>
response_Dailog: NPC가 사용자 대사에 대한 답변을 제공하는 엔드포인트<br/>
플레이어의 대사.행동(userMsg)을 사용자로부터 받는다.<br/>
현재 장소(location), 대화대상(npcName), 플레이어행적(history)을 talking_cache에서 받아온다.<br/>
미리 생성했던 char_dic 에서 대화대상(npcName)에 맞는 npc_detail들을 가져온다<br/>
받아온 정보들을 토대로 npc의 대사를 생성, 반환한다<br/>
만약 플레이어의 대사.행동(userMsg)이 비어있다면 자동으로 "인사하기" 문구를 저장시킨다.<br/>
대화대상(npcName)이 '게임마스터'라면 게임마스터와의 대화하고 그렇지 않으면 해당대화대상과 대화한다<br/>
사용자와 대화대상(npcName) 간 나눈대화를 talking_cache 안에 dialog_history에 저장한다<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<img width="900" alt="image" src="https://github.com/user-attachments/assets/1f410ed2-bb1d-403b-89b8-ce9fc81771b7">
<br/>
responseDice: 주사위 결과에 따른 NPC 답변을 제공하는 엔드포인트<br/>
플레이어의 대사.행동(userMsg)을 사용자로부터 받는다.<br/>
추가로 사용자의 주사위판정결과(diceResult), 주사위보정치(bonus)를 사용자에게 받는다<br/>
현재 장소(location), 대화대상(npcName), 플레이어행적(history)을 talking_cache에서 받아온다.<br/>
미리 생성했던 char_dic 에서 대화대상(npcName)에 맞는 npc_detail들을 가져온다<br/>
받아온 정보들을 토대로 npc의 대사를 생성, 반환한다<br/>
만약 플레이어의 대사.행동(userMsg)이 비어있다면 자동으로 "인사하기" 문구를 저장시킨다.<br/>
대화대상(npcName)이 '게임마스터'라면 게임마스터와의 대화하고 그렇지 않으면 해당대화대상과 대화한다<br/>
사용자와 대화대상(npcName) 간 나눈대화를 talking_cache 안에 dialog_history에 저장한다<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<img width="889" alt="image" src="https://github.com/user-attachments/assets/6ec377ce-e289-4d66-851f-59fcba2c81cc">
<br/>
end_Dailog: 대화를 종료하고 요약을 생성하는 엔드포인트<br/>
사용자에게서 대화종료신호를 받으면 이제까지의 대화(dialog_history)를 통해 요약본을 만든다.<br/>
추가로 scenario_cache 안에 있는 end_detail(end_dailog를 실행할때 사용할 detail), mainQuest(게임 주요목표(승리조건)), subQuest(게임 보조 목표)를 받아와서 <br/>
목표달성이 됬는지를 판정한다. 요약본이 만들어지고난 후 대화버퍼를 초기화시킨다.<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<img width="734" alt="image" src="https://github.com/user-attachments/assets/3261be57-0ef2-4ffd-8385-22c1906269ad">
<br/>
end_Scenario: 게임 세션을 종료하고 캐시를 정리하는 엔드포인트<br/>
사용자에게 sessionID를 받으면 scenario_cache에서 sessionID값에 해당되는 정보들을 삭제한다<br/>
