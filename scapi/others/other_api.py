from typing import Literal, TypedDict
from . import common
import asyncio
import urllib.parse

async def check_username(username:str,clientsession:common.ClientSession) -> str:
    r = await clientsession.get(f"https://api.scratch.mit.edu/accounts/checkusername/{username}")
    return r.json().get("msg","")

async def check_password(password:str,clientsession:common.ClientSession) -> str:
    r = await clientsession.post(f"https://api.scratch.mit.edu/accounts/checkusername/",json={"password":password})
    return r.json().get("msg","")

class total_site_stats_data(TypedDict):
    PROJECT_COUNT:int
    USER_COUNT:int
    STUDIO_COMMENT_COUNT:int
    PROFILE_COMMENT_COUNT:int
    STUDIO_COUNT:int
    COMMENT_COUNT:int
    PROJECT_COMMENT_COUNT:int
    _TS:float

async def total_site_stats(clientsession:common.ClientSession) -> total_site_stats_data:
    return (await clientsession.get("https://scratch.mit.edu/statistics/data/daily/")).json()

class monthly_site_traffic_data(TypedDict):
    pageviews:int
    users:int
    sessions:int
    _TS:float

async def monthly_site_traffic(clientsession:common.ClientSession) -> monthly_site_traffic_data:
    r = (await clientsession.get("https://scratch.mit.edu/statistics/data/monthly-ga/")).json()
    return {
        "_TS":r.get("_TS",0),
        "pageviews":int(r.get("pageviews",0)),
        "users":int(r.get("users",0)),
        "sessions":int(r.get("sessions",0))
    }

graph_data=list[tuple[int,int]]

class monthly_activity_data(TypedDict):
    _TS:float
    comment_data:dict[Literal["Project Comments","Studio Comments","Profile Comments"],graph_data]
    activity_data:dict[Literal["New Projects","New Users","New Comments"],graph_data]
    active_user_data:dict[Literal["Project Creators","Comment Creators"],graph_data]
    project_data:dict[Literal["New Projects","Remix Projects"],graph_data]
    age_distribution_data:dict[Literal["Registration age of Scratchers"],graph_data]
    country_distribution:dict[Literal["Registration age of Scratchers"],graph_data]

def data_to_graph(data:list[dict[Literal["values"],list[dict[Literal["x","y"],int]]]],key_data:list[str]) -> dict[str, graph_data]:
    r:dict[str,graph_data] = {}
    for i in range(len(key_data)):
        r[key_data[i]] = []
        for d in data[i]["values"]:
            r[key_data[i]].append((d["x"],d["y"]))
    return r


async def monthly_activity(clientsession:common.ClientSession) -> monthly_activity_data:
    data = (await clientsession.get("https://scratch.mit.edu/statistics/data/monthly/")).json()
    r:monthly_activity_data = {"_TS":data.get("_TS")}
    r["comment_data"] = data_to_graph(data["comment_data"],["Project Comments","Studio Comments","Profile Comments"])
    r["activity_data"] = data_to_graph(data["activity_data"],["New Projects","New Users","New Comments"])
    r["active_user_data"] = data_to_graph(data["active_user_data"],["Project Creators","Comment Creators"])
    r["project_data"] = data_to_graph(data["project_data"],["New Projects","Remix Projects"])
    r["country_distribution"] = data["country_distribution"]
    r["age_distribution_data"] = data_to_graph(data["age_distribution_data"],["Registration age of Scratchers"])
    return r

async def translation(language:str,text:str,clientsession:common.ClientSession) -> str:
    text = urllib.parse.quote(text,safe="")
    r = await clientsession.get(f"https://translate-service.scratch.mit.edu/translate?language={language}&text={text}")
    return r.json().get("result","")

async def tts(language:str,text:str,type:Literal["male","female"],clientsession:common.ClientSession) -> bytes:
    text = urllib.parse.quote(text,safe="")
    r = await clientsession.get(f"https://synthesis-service.scratch.mit.edu/synth?locale={language}&gender={type}&text={text}")
    return r.data