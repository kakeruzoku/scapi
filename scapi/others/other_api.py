import requests as sync_req
from . import common
import asyncio

def get_csrf_token_sync() -> str:
    return sync_req.get(
        "https://scratch.mit.edu/csrf_token/"
    ).headers["set-cookie"].split(";")[3][len(" Path=/, scratchcsrftoken="):]

async def check_usernames(*usernames:list[str],clientsession:common.ClientSession|None=None) -> dict[str,str]:
    if len(usernames) == 0: return {}
    _if_close = False
    if clientsession is None: 
        clientsession = common.create_ClientSession()
        _if_close = True
    tasks = [asyncio.create_task(clientsession.get(f"https://api.scratch.mit.edu/accounts/checkusername/{un}")) for un in usernames]
    resp:list[common.Response] = await asyncio.gather(*tasks)
    r = {}
    for i in resp:
        jsons = i.json()
        r[jsons["username"]] = jsons["msg"]
    if _if_close:
        await clientsession.close()
    return r

async def _chack_pw(cs:common.ClientSession,password:str):
    r = await cs.post(f"https://api.scratch.mit.edu/accounts/checkpassword/",json={"password":password})
    return [password,r.json()["msg"]]

async def check_passwords(*passwords:list[str],clientsession:common.ClientSession|None=None) -> dict[str,str]:
    if len(passwords) == 0: return {}
    _if_close = False
    if clientsession is None: 
        clientsession = common.create_ClientSession()
        _if_close = True
    tasks = [asyncio.create_task(_chack_pw(clientsession,pw)) for pw in passwords]
    resp:list[list[str,str]] = await asyncio.gather(*tasks)
    r = {}
    for i in resp:
        r[i[0]] = i[1]
    if _if_close:
        await clientsession.close()
    return r