from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile, Body, Form
from fastapi.responses import JSONResponse, FileResponse
import shutil
import os
from fastapi import FastAPI, Form
from 해석모듈 import haesuck
from npc대화_1 import talking
from 게임마스터대화_1 import game_master_talking

app = FastAPI()

# 시나리오 주요 정보 저장
scenario_cache = {}
scenario_record = []

@app.get('/')
def open():
    return {"message": "opening"}

@app.post('/first_gamemaster/')
async def first_gamemaster(
    title: str = Form(...),
    genre: str = Form(...),
    mainQuest: str = Form(...),
    subQuest: str = Form(...),
    detail: str = Form(...),
    charParts: str = Form(...),
    worldParts: str = Form(...),
    tag: str = Form(...),
    players: str = Form(...)):
    # 시나리오 캐시에 저장
    charParts_list = charParts.split(',')
    charParts_list.append('게임마스터')  # 게임마스터 추가
    worldParts_list = worldParts.split(',')
    subQuest_list = subQuest.split(',')
    tag_list = tag.split(',')

    # 시나리오 정보를 캐시에 저장
    scenario_cache.update({
        "title": title,
        "genre": genre,
        "mainQuest": mainQuest,
        "subQuest": subQuest_list,
        "detail": detail,
        "charParts": charParts_list,
        "worldParts": worldParts_list,
        "players": players
    })
    

    return scenario_cache

    

@app.post('/middle_gamemaster/')
async def middle_gamemaster(player_talk: str = Form(...)):
    # 캐시된 시나리오 정보를 가져옴
    middle_charParts = scenario_cache.get("charParts")
    middle_players = scenario_cache.get("players")
    middle_mainQuest = scenario_cache.get("mainQuest")
    middle_subQuest = scenario_cache.get("subQuest")
    middle_worldParts = scenario_cache.get("worldParts")
    middle_detail = scenario_cache.get("detail")
    middle_title = scenario_cache.get("title")

    talk = {
        "player_name": middle_players,
        "player_talk": player_talk,
        "charParts": middle_charParts,
        "mainQuest": middle_mainQuest,
        "title": middle_title,
        "detail": middle_detail,
        "subQuest": middle_subQuest,
        "worldParts": middle_worldParts,
        "scenario_record": scenario_record
    }

    # haesuck 모듈을 호출하여 결과를 받아옴
    result = haesuck(talk)

    # NPC가 게임마스터인지 확인
    if result['npc'] == '게임마스터':
        talk_to_game_master = {
            "player_talk": player_talk,
            "charParts": middle_charParts,
            "mainQuest": middle_mainQuest,
            "title": middle_title,
            "detail": middle_detail,
            "subQuest": middle_subQuest,
            "worldParts": middle_worldParts,
            "scenario_record": scenario_record
        }

        # 게임마스터의 반응 생성
        gm_result = game_master_talking(talk_to_game_master['player_talk'],
                                        talk_to_game_master['charParts'],
                                        talk_to_game_master['mainQuest'],
                                        talk_to_game_master['subQuest'],
                                        talk_to_game_master['title'],
                                        talk_to_game_master['detail'],
                                        talk_to_game_master['worldParts'],
                                        talk_to_game_master['scenario_record']
                                        )
        print(gm_result)

        # 상황 기록을 저장
        scenario_record.append(gm_result['situation_record'])
        print(scenario_record)

        return gm_result['game_master_speach']#{"result": gm_result['game_master_speach']}  # 게임마스터의 반응 반환
    
    else:
        # NPC와의 상호작용 처리
        npc_talk = {
            "npc": result['npc'],
            "player": middle_players,
            "player_talk": player_talk,
            "mainQuest":middle_mainQuest,
            "subQuest":middle_subQuest,
        }

        # NPC와의 대화를 처리하는 함수 호출
        npc_result = talking(npc_talk['npc'], npc_talk['player'], npc_talk['player_talk'],  npc_talk['mainQuest'], npc_talk['subQuest'])

        # 상황 기록을 저장
        scenario_record.append(npc_result['situation_record'])
        print(scenario_record)

        return {"npc_result": npc_result}  # NPC와의 대화 결과 반환
    
@app.post('/end_gamemaster/')
async def middle_gamemaster(player_talk: str = Form(...)):
    return scenario_record
