from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile, Body, APIRouter
from fastapi.responses import JSONResponse, FileResponse
import shutil
from typing import List, Optional
import os
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from fastapi import FastAPI, Form
from npc대화_6 import npc_talking, memory
from 게임마스터대화_5 import game_master_talking, gm_memory
from 히스토리생성 import create_history
from 해석모듈_6 import haesuck
import logging
from 키워드필터링 import filter_text_by_keywords
from create_End_detail import create_end_quest_judgment
from create_npc_detail import create_npc_detail

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI()

# 시나리오, 히스토리, 대화 캐시 초기화
scenario_cache = {}
talking_cache = {}

@app.get('/')
def open():
    return {"message": "opening"}

# 라우터 정의
startScenario_router = APIRouter(prefix="/startScenario", tags=["방생성"])
create_NPC_detail_router = APIRouter(prefix="/create_NPC_detail", tags=["npc_detail 생성"])
create_end_detail_router = APIRouter(prefix="/create_end_detail", tags=["end_detail 생성"])
startDailog_router = APIRouter(prefix="/startDailog", tags=["대화 시작"])
analyzeUserMsg_router = APIRouter(prefix="/analyzeUserMsg", tags=["해석모듈"])
responseDailog_router = APIRouter(prefix="/responseDailog", tags=["NPC 답변"])
responseDice_router = APIRouter(prefix="/responseDice", tags=["주사위 결과에 따른 NPC 답변"])
endDailog_router = APIRouter(prefix="/endDailog", tags=["대화 종료 및 히스토리 생성"])
endScenario_router = APIRouter(prefix="/endScenario", tags=["방 삭제"])

#-----------------------------------------------------------------------------------------------------
# 방 생성 엔드포인트
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
            "history": []
        }
    print(scenario_cache)
    return {"message": "start_Scenario", "data": scenario_cache[scenario.sessionID]}

#-----------------------------------------------------------------------------------------------------
# NPC 상세 정보 생성 엔드포인트
class create_NPC_detail(BaseModel):
    sessionID: int

@create_NPC_detail_router.post('/')
async def create_NPC_detail(request: create_NPC_detail):
    sessionID = request.sessionID
    cached_scenario = scenario_cache.get(sessionID)
    
    if not cached_scenario:
        return {'message': '시나리오를 찾을 수 없습니다.', 'status_code': 404}
    
    detail = cached_scenario.get("detail")
    charParts = cached_scenario.get("charParts")
    
    # 특정 캐릭터 이름에 따라 detail 텍스트 필터링
    filtered_detail = filter_text_by_keywords(detail, charParts)

    charParts_dic = create_npc_detail(filtered_detail, charParts)
    
    # charParts_dic을 sessionID에 맞는 시나리오에 추가
    cached_scenario["charParts_dic"] = charParts_dic
    scenario_cache[sessionID] = cached_scenario
    
    return {'message': '생성 완료', 'charParts_dic': charParts_dic}

#-----------------------------------------------------------------------------------------------------
# 엔딩 상세 정보 생성 엔드포인트
class create_End_detail(BaseModel):
    sessionID: int

@create_end_detail_router.post('/')
async def create_End_detail(request: create_End_detail):
    sessionID = request.sessionID
    cached_scenario = scenario_cache.get(sessionID)
    
    if not cached_scenario:
        return {'message': '시나리오를 찾을 수 없습니다.', 'status_code': 404}

    mainQuest = cached_scenario.get("mainQuest")
    subQuest = cached_scenario.get("subQuest")
    detail = cached_scenario.get("detail")

    # 메인 퀘스트와 서브 퀘스트 관련 텍스트 필터링
    relevant_detail_text = create_end_quest_judgment(detail, mainQuest, subQuest)
    
    # end_detail을 sessionID에 맞는 시나리오에 추가
    cached_scenario["end_detail"] = relevant_detail_text
    scenario_cache[sessionID] = cached_scenario

    return {'message': 'end_detail 생성 완료', 'end_detail': relevant_detail_text}

#-----------------------------------------------------------------------------------------------------
# 대화 시작 엔드포인트
class startDialog(BaseModel):
    sessionID: int
    location: Optional[str] = None
    npcName: Optional[str] = None
    history: Optional[List[str]] = Field(default_factory=list)

    @field_validator("history", mode='before')
    def limit_history_to_last_three(cls, value):
        return value[-3:] if value else []

@startDailog_router.post('/')
async def start_Dialog(request: startDialog):
    userMsg = f"{request.npcName} 에게 인사하기"
    talking_cache[request.sessionID] = {
        "location": request.location,
        "npcName": request.npcName,
        "userMsg": userMsg,
        "history": request.history,
        "dialog_history": []
    }
    return {"message": "Dialog started", "data": talking_cache[request.sessionID]}

#-----------------------------------------------------------------------------------------------------
# 해석 모듈 엔드포인트
class analyzeUserMsg(BaseModel):
    userMsg: str
    sessionID: int

@analyzeUserMsg_router.post('/')
async def analyze_UserMsg(request: analyzeUserMsg):
    sessionID = request.sessionID
    userMsg = request.userMsg

    cached_scenario = scenario_cache.get(sessionID)
    if cached_scenario is None:
        return JSONResponse(status_code=404, content={"message": "시나리오를 찾을 수 없습니다."})

    talk = {
        "player_talk": userMsg
    }
    return haesuck(talk)

#-----------------------------------------------------------------------------------------------------
# NPC 답변 엔드포인트
class responseDailog(BaseModel):
    sessionID: int
    userMsg: str
    
    # userMsg가 비었을 경우 기본값 설정
    @field_validator("userMsg", mode='before')
    def set_default_userMsg(cls, value):
        if not value or not value.strip():
            return "인사하기"
        return value

@responseDailog_router.post('/')
async def response_Dailog(request: responseDailog):
    sessionID = request.sessionID
    userMsg = request.userMsg
    diceResult = getattr(request, "diceResult", "없음")
    bonus = getattr(request, "bonus", "없음")

    cached_scenario = scenario_cache.get(sessionID)
    if not cached_scenario:
        return JSONResponse(status_code=404, content={"message": "시나리오를 찾을 수 없습니다."})
    talking_data = talking_cache.get(sessionID)
    if not talking_data:
        return JSONResponse(status_code=404, content={"message": "대화 기록을 찾을 수 없습니다."})
    
    location = talking_data.get("location")
    npcName = talking_data.get("npcName")
    history = talking_data.get("history", [])
    dialog_history = talking_data.get("dialog_history")
    
    # npc_detail 가져오기
    charParts_dic = cached_scenario.get("charParts_dic", {})
    if npcName in charParts_dic:
        npc_detail = "\n".join(charParts_dic[npcName])
    else:
        npc_detail = "상세 정보 없음"

    if npcName == '게임마스터':
        gm_result = game_master_talking(
            userMsg=userMsg,
            charParts=cached_scenario.get("charParts"),
            mainQuest=cached_scenario.get("mainQuest"),
            subQuest=cached_scenario.get("subQuest"),
            title=cached_scenario.get("title"),
            detail=cached_scenario.get("detail"),
            worldParts=cached_scenario.get("worldParts"),
            diceResult=diceResult,
            bonus=bonus,
            history=history
        )
        return gm_result

    else:
        npc_result, single_dialog_history = npc_talking(
            npcName=npcName,
            userMsg=userMsg,
            detail=npc_detail,
            location=location,
            diceResult=diceResult,
            bonus=bonus,
            history=history
        )
        print(npc_result)
        talking_cache[sessionID]["dialog_history"].append(single_dialog_history)
        return npc_result

#-----------------------------------------------------------------------------------------------------
# 주사위 결과에 따른 NPC 답변 엔드포인트
class responseDice(BaseModel):
    sessionID: int
    userMsg: str
    diceResult: Optional[str] = "없음"
    bonus: Optional[str] = "없음"

@responseDice_router.post('/')
async def response_Dice(request: responseDice):
    sessionID = request.sessionID
    userMsg = request.userMsg
    diceResult = request.diceResult
    bonus = request.bonus

    cached_scenario = scenario_cache.get(sessionID)
    if not cached_scenario:
        return JSONResponse(status_code=404, content={"message": "시나리오를 찾을 수 없습니다."})
    
    talking_data = talking_cache.get(sessionID)
    if not talking_data:
        return JSONResponse(status_code=404, content={"message": "대화 기록을 찾을 수 없습니다."})

    location = talking_data.get("location")
    npcName = talking_data.get("npcName")
    history = talking_data.get("history", [])
    dialog_history = talking_data.get("dialog_history")

    # npc_detail 가져오기
    charParts_dic = cached_scenario.get("charParts_dic", {})
    if npcName in charParts_dic:
        npc_detail = "\n".join(charParts_dic[npcName])
    else:
        npc_detail = "상세 정보 없음"

    if npcName == '게임마스터':
        gm_result = game_master_talking(
            userMsg=userMsg,
            charParts=cached_scenario.get("charParts"),
            mainQuest=cached_scenario.get("mainQuest"),
            subQuest=cached_scenario.get("subQuest"),
            title=cached_scenario.get("title"),
            detail=cached_scenario.get("detail"),
            worldParts=cached_scenario.get("worldParts"),
            diceResult=diceResult,
            bonus=bonus,
            history=history
        )
        return gm_result

    else:
        npc_result, single_dialog_history = npc_talking(
            npcName=npcName,
            userMsg=userMsg,
            detail=npc_detail,
            location=location,
            diceResult=diceResult,
            bonus=bonus,
            history=history
        )
        print(npc_result)
        talking_cache[sessionID]["dialog_history"].append(single_dialog_history)
        return npc_result

#-----------------------------------------------------------------------------------------------------
# 대화 종료 및 히스토리 생성 엔드포인트
class endDailog(BaseModel):
    sessionID: int

@endDailog_router.post('/')
async def end_Dailog(request: endDailog):
    sessionID = request.sessionID
    talking_data = talking_cache.get(sessionID)
    if not talking_data:
        return JSONResponse(status_code=404, content={"message": "대화 기록을 찾을 수 없습니다."})

    history_text = "\n".join(talking_data.get("dialog_history"))
    cached_scenario = scenario_cache.get(sessionID)
    if cached_scenario is None:
        return JSONResponse(status_code=404, content={"message": "시나리오를 찾을 수 없습니다."})

    mainQuest = cached_scenario.get("mainQuest")
    subQuest = cached_scenario.get("subQuest")
    detail = cached_scenario.get("end_detail")

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
        logging.exception("히스토리 생성 중 오류 발생")
        return JSONResponse(status_code=500, content={"message": "내부 서버 오류", "details": str(e)})

#-----------------------------------------------------------------------------------------------------
# 방 삭제 엔드포인트
class endScenario(BaseModel):
    sessionID: int

@endScenario_router.post('/')
async def end_Scenario(request: endScenario):
    sessionID = request.sessionID
    if sessionID in scenario_cache:
        scenario_cache.pop(sessionID)
        return {"message": f"end_Scenario 실행: {sessionID} 방 삭제"}
    return JSONResponse(status_code=404, content={"message": "해당 sessionID의 방이 존재하지 않습니다."})

#-----------------------------------------------------------------------------------------------------
# 메인 FastAPI 앱에 라우터 추가
app.include_router(startScenario_router)
app.include_router(create_NPC_detail_router)
app.include_router(create_end_detail_router)
app.include_router(startDailog_router)
app.include_router(analyzeUserMsg_router)
app.include_router(responseDailog_router)
app.include_router(responseDice_router)
app.include_router(endDailog_router)
app.include_router(endScenario_router)
