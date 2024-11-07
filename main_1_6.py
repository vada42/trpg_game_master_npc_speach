from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile, Body, APIRouter
from fastapi.responses import JSONResponse, FileResponse
import shutil
from typing import List, Optional
import os
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from fastapi import FastAPI, Form
from npc대화_5 import npc_talking, memory
from 게임마스터대화_5 import game_master_talking, gm_memory
from 히스토리생성 import create_history
from 해석모듈_5 import haesuck
import logging

# powershell-> ngrok http --domain=boss-goblin-tolerant.ngrok-free.app 8080
# uvicorn main_1_6:app --reload --port 8080 

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI()

# 시나리오, 히스토리, 대화 캐시 초기화
scenario_cache = {}
history = {}
talking_cache = {}

@app.get('/')
def open():
    return {"message": "opening"}




# "방생성" 라우터 생성
startScenario_router = APIRouter(prefix="/startScenario", tags=["방생성"])
# "대화시작" 라우터 생성
startDailog_router = APIRouter(prefix="/startDailog", tags=["대화 시작 (npc에게 말검)"])
# "해석모듈" 라우터 생성
analyzeUserMsg_router = APIRouter(prefix="/analyzeUserMsg", tags=["해석모듈"])
# "시나리오" 라우터 생성
responseDailog_router = APIRouter(prefix="/responseDailog", tags=["유저의 대사에 대해 npc 답변"])
# "시나리오" 라우터 생성
responseDice_router = APIRouter(prefix="/responseDice", tags=["(유저의 대사+ dice결과) 에 대해 npc 답변"])
# "시나리오" 라우터 생성
endDailog_router = APIRouter(prefix="/endDailog", tags=["대화 끝, 쌓인 대화 요약해서 히스토리로 만들기, 대사 캐시 삭제"])
# "시나리오" 라우터 생성
endScenario_router = APIRouter(prefix="/endScenario", tags=["방 삭제"])




# 시나리오 정보를 위한 데이터 구조 정의
class startScenario(BaseModel):
    sessionID: int
    title: str
    genre: str
    mainQuest: str
    subQuest: List[str]
    detail: str
    charParts: List[str]
    worldParts: List[str]
    players: List[str]

@startScenario_router.post('/')
async def start_Scenario(scenario: startScenario):
    # 시나리오 정보가 없으면 캐시에 저장
    if scenario.sessionID not in scenario_cache:
        scenario_cache[scenario.sessionID] = {
            "title": scenario.title,
            "genre": scenario.genre,
            "mainQuest": scenario.mainQuest,
            "subQuest": scenario.subQuest,
            "detail": scenario.detail,
            "charParts": scenario.charParts + ["게임마스터"],
            "worldParts": scenario.worldParts,
            "players": scenario.players,
            "history" :[]
        }
    print(scenario_cache)
    return {"message": "start_Scenario", "data": scenario_cache[scenario.sessionID]}







class startDialog(BaseModel):
    sessionID: int
    location: Optional[str] = None
    npcName: Optional[str] = None
    history: Optional[List[str]] = Field(default_factory=list)

    # 첫 요청 이후 history를 마지막 3개 항목으로 제한
    @field_validator("history", mode='before')
    def limit_history_to_last_three(cls, value):
        return value[-3:] if value else []

    # # userMsg가 비었을 경우 기본값 설정
    # @field_validator("userMsg", mode='before')
    # def set_default_userMsg(cls, value, values):
    #     if not value or not value.strip():
    #         npc_name = values.get("npcName", "NPC")
    #         return f"{npc_name} 에게 인사하기"
    #     return value

@startDailog_router.post('/')
async def start_Dialog(dialog: startDialog):
    # 캐시에 첫 대화 정보를 추가
    userMsg = f"{dialog.npcName} 에게 인사하기"
    talking_cache[dialog.sessionID] = {
        "location": dialog.location,
        "npcName": dialog.npcName,
        "userMsg": userMsg,
        "history": dialog.history, # 최근 3개의 기록은 이미 validator에서 처리
        "dialog_history": []
    }
    return {"message": "Dialog started", "data": talking_cache[dialog.sessionID]}




class analyzeUserMsg(BaseModel):
    userMsg: str
    sessionID: int

@analyzeUserMsg_router.post('/')
async def analyze_UserMsg(request: analyzeUserMsg):
    sessionID = request.sessionID
    userMsg = request.userMsg

    # 캐시된 시나리오 정보 로드
    cached_scenario = scenario_cache.get(sessionID)
    if cached_scenario is None:
        return JSONResponse(status_code=404, content={"message": "시나리오를 찾을 수 없습니다."})

    scenario_recorded = history.get(sessionID, [])
    npcName = talking_cache.get(sessionID, {}).get("npcName")
    talk = {
        "charParts": cached_scenario.get("charParts"),
        "mainQuest": cached_scenario.get("mainQuest"),
        "title": cached_scenario.get("title"),
        "detail": cached_scenario.get("detail"),
        "subQuest": cached_scenario.get("subQuest"),
        "worldParts": cached_scenario.get("worldParts"),
        "player_talk": userMsg,
        "scenario_recorded": scenario_recorded
    }
    return haesuck(talk)



class responseDailog (BaseModel):
    sessionID: int
    userMsg: str
    

    # userMsg가 비었을 경우 기본값 설정
    @field_validator("userMsg")
    def set_default_userMsg(cls, value, values: ValidationInfo):
        if not value.strip():
            npc_name = values.data.get("npcName", "NPC")
            return f"{npc_name} 에게 인사하기"
        return value

@responseDailog_router.post('/')
async def response_Dailog(request: responseDailog ):
    sessionID = request.sessionID
    userMsg = request.userMsg
    diceResult = '없음'
    bonus = '없음'

    # 캐시된 시나리오 정보 로드
    cached_scenario = scenario_cache.get(sessionID)
    if cached_scenario is None:
        return JSONResponse(status_code=404, content={"message": "시나리오를 찾을 수 없습니다."})
    
     # 캐시된 대화 정보 로드
    talking_data = talking_cache.get(sessionID)
    if not talking_data:
        return JSONResponse(status_code=404, content={"message": "대화 기록을 찾을 수 없습니다."})

    location = talking_data.get("location")
    npcName = talking_data.get("npcName")
    history = talking_data.get("history", [])
    dialog_history = talking_data.get("dialog_history")


    if npcName == '게임마스터':
        gm_result = game_master_talking(
            userMsg=userMsg,
            charParts=cached_scenario.get("charParts"),
            mainQuest=cached_scenario.get("mainQuest"),
            subQuest=cached_scenario.get("subQuest"),
            title=cached_scenario.get("title"),
            detail=cached_scenario.get("detail"),
            worldParts=cached_scenario.get("worldParts"),
            diceResult=talking_cache[sessionID]["diceResult"],
            bonus=talking_cache[sessionID]["bonus"],
            history=history
        )
        return gm_result

    else:
        npc_result, single_dialog_history = npc_talking(
            npcName=npcName,
            userMsg=userMsg,
            detail=cached_scenario.get("detail"),
            location=location,
            diceResult=diceResult,
            bonus=bonus
        )
        print(npc_result)
        talking_cache[sessionID]["dialog_history"].append(single_dialog_history)
        return npc_result
    



class responseDice(BaseModel):
    sessionID: int
    userMsg: str
    diceResult: Optional[str] = "없음"
    bonus: Optional[str] = "없음"

    # userMsg가 비었을 경우 기본값 설정
    @field_validator("userMsg")
    def set_default_userMsg(cls, value, values: ValidationInfo):
        if not value.strip():
            npc_name = values.data.get("npcName", "NPC")
            return f"{npc_name} 에게 인사하기"
        return value

@responseDice_router.post('/')
async def response_Dice(request: responseDice):
    sessionID = request.sessionID
    userMsg = request.userMsg
    diceResult = request.diceResult
    bonus = request.bonus

    # 캐시된 시나리오 정보 로드
    cached_scenario = scenario_cache.get(sessionID)
    if cached_scenario is None:
        return JSONResponse(status_code=404, content={"message": "시나리오를 찾을 수 없습니다."})
    
     # 캐시된 대화 정보 로드
    talking_data = talking_cache.get(sessionID)
    if not talking_data:
        return JSONResponse(status_code=404, content={"message": "대화 기록을 찾을 수 없습니다."})

    location = talking_data.get("location")
    npcName = talking_data.get("npcName")
    history = talking_data.get("history", [])
    dialog_history = talking_data.get("dialog_history")

    # 시나리오 정보 로드
    cached_scenario = scenario_cache.get(sessionID)
    if cached_scenario is None:
        return JSONResponse(status_code=404, content={"message": f"scenario_cache에 {sessionID} 이름의 방이 없음. 세션 ID 확인 필요"})

    if npcName == '게임마스터':
        gm_result = game_master_talking(
            userMsg=userMsg,
            charParts=cached_scenario.get("charParts"),
            mainQuest=cached_scenario.get("mainQuest"),
            subQuest=cached_scenario.get("subQuest"),
            title=cached_scenario.get("title"),
            detail=cached_scenario.get("detail"),
            worldParts=cached_scenario.get("worldParts"),
            diceResult=talking_cache[sessionID]["diceResult"],
            bonus=talking_cache[sessionID]["bonus"],
            history=history
        )
        return gm_result

    else:
        npc_result, single_dialog_history = npc_talking(
            npcName=npcName,
            userMsg=userMsg,
            detail=cached_scenario.get("detail"),
            location=location,
            diceResult=diceResult,
            bonus=bonus
        )
        print(npc_result)
        talking_cache[sessionID]["dialog_history"].append(single_dialog_history)
        return npc_result







class endDailog (BaseModel):
    sessionID: int

@endDailog_router.post('/')
async def end_Dailog (request: endDailog ):
    sessionID = request.sessionID
     # 캐시된 대화 정보 로드
    talking_data = talking_cache.get(sessionID)
    if not talking_data:
        return JSONResponse(status_code=404, content={"message": "대화 기록을 찾을 수 없습니다."})
    history_text = "\n".join(talking_data.get("dialog_history"))
    cached_scenario = scenario_cache.get(sessionID)

    if cached_scenario is None:
        return JSONResponse(status_code=404, content={"message": "시나리오를 찾을 수 없습니다."})

    mainQuest = cached_scenario.get("mainQuest")
    subQuest = cached_scenario.get("subQuest")
    detail = cached_scenario.get("detail")
    try:
        result = create_history(
            history=history_text,
            detail=detail,
            mainQuest=mainQuest,
            subQuest=subQuest
        )
        memory.clear()
        gm_memory.clear()
        if sessionID in talking_cache:
            talking_cache[sessionID].clear()
            print(talking_cache[sessionID])

        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "내부 서버 오류", "details": str(e)})



class endScenario  (BaseModel):
    sessionID: int

@endScenario_router.post('/')
async def end_Scenario  (request: endScenario  ):
    sessionID = request.sessionID
    scenario_cache[sessionID].clear()
    return {"message": f" end_Scenario 실행  {sessionID} 방 삭제" }



# 메인 FastAPI 앱에 라우터 추가
app.include_router(startScenario_router)

app.include_router(startDailog_router)

app.include_router(analyzeUserMsg_router)

app.include_router(responseDailog_router)

app.include_router(responseDice_router)

app.include_router(endDailog_router)

app.include_router(endScenario_router)
