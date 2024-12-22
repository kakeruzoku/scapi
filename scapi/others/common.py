import datetime
import aiohttp
from multidict import CIMultiDictProxy, CIMultiDict
from . import error as exceptions
import json


headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36",
    "x-csrftoken": "a",
    "x-requested-with": "XMLHttpRequest",
    "referer": "https://scratch.mit.edu",
}

def create_ClientSession(inp:"Requests|None"=None) -> "Requests":
    return Requests(
        header=headers,
    ) if inp is None else inp

class Response:
    def __init__(self,status:int,text:str,headers:CIMultiDictProxy[str]) -> None:
        self.status_code:int = status
        self.text:str = text
        self.headers:CIMultiDict[str] = headers.copy()
    
    def json(self):
        return json.loads(self.text)

class Requests(aiohttp.ClientSession):

    def __init__(self,header:dict) -> None:
        super().__init__()
        self._header = header
        self._cookie = {}
    
    async def check(self,response:Response) -> None:
        if response.status_code in [403,401]:
            raise exceptions.Unauthorized(response.status_code,response)
        if response.status_code in [429]:
            raise exceptions.TooManyRequests(response.status_code,response)
        if response.status_code in [404]:
            raise exceptions.HTTPNotFound(response.status_code,response)
        if response.status_code // 100 == 4:
            raise exceptions.BadRequest(response.status_code,response)
        if response.status_code // 100 == 5:
            raise exceptions.ServerError(response.status_code,response)
        if response.text == '{"code":"BadRequest","message":""}':
            raise exceptions.BadResponse(response.status_code,response)

    
    async def get(
        session,url,*,
        data=None,json=None,timeout=None,params=None,
        header=None,cookie=None,check=True
    ) -> Response:
        if session.closed: raise exceptions.SessionClosed
        if header is None: header = session._header.copy()
        if cookie is None: cookie = session._cookie.copy()
        try:
            async with super().get(
                url,data=data,json=json,timeout=timeout,params=params,headers=header,cookies=cookie
            ) as response:
                r = Response(response.status,await response.text(),response.headers)
        except Exception as e:
            raise exceptions.HTTPFetchError(e)
        if check: await session.check(r)
        return r
    
    
    async def post(
        session,url,*,
        data=None,json=None,timeout=None,params=None,
        header=None,cookie=None,check=True
    ) -> Response:
        if session.closed: raise exceptions.SessionClosed
        if header is None: header = session._header.copy()
        if cookie is None: cookie = session._cookie.copy()
        try:
            async with super().post(
                url,data=data,json=json,timeout=timeout,params=params,headers=header,cookies=cookie
            ) as response:
                r = Response(response.status,await response.text(),response.headers)
        except Exception as e:
            raise exceptions.HTTPFetchError(e)
        if check: await session.check(r)
        return r
    
    
    async def put(
        session,url,*,
        data=None,json=None,timeout=None,params=None,
        header=None,cookie=None,check=True
    ) -> Response:
        if session.closed: raise exceptions.SessionClosed
        if header is None: header = session._header.copy()
        if cookie is None: cookie = session._cookie.copy()
        try:
            async with super().put(
                url,data=data,json=json,timeout=timeout,params=params,headers=header,cookies=cookie
            ) as response:
                r = Response(response.status,await response.text(),response.headers)
        except Exception as e:
            raise exceptions.HTTPFetchError(e)
        if check: await session.check(r)
        return r
    
    async def delete(
        session,url,*,
        data=None,json=None,timeout=None,params=None,
        header=None,cookie=None,check=True
    ) -> Response:
        if session.closed: raise exceptions.SessionClosed
        if header is None: header = session._header.copy()
        if cookie is None: cookie = session._cookie.copy()
        try:
            async with super().delete(
                url,data=data,json=json,timeout=timeout,params=params,headers=header,cookies=cookie
            ) as response:
                r = Response(response.status,await response.text(),response.headers)
        except Exception as e:
            raise exceptions.HTTPFetchError(e)
        if check: await session.check(r)
        return r



async def api_iterative(
        session:Requests,
        url:str,
        *,
        limit:int|None=None,
        offset:int=0,
        max_limit=40,
        add_params:dict={}
    ) -> list[dict]:
    """
    APIを叩いてリストにして返す
    """
    if offset < 0:
        raise ValueError("offset parameter must be >= 0")
    if limit < 0:
        raise ValueError("limit parameter must be >= 0")
    if limit is None:
        limit = max_limit
    
    api_data = []
    for i in range(offset,offset+limit,max_limit):
        r = await session.get(
            url,timeout=10,
            params=dict(limit=max_limit,offset=i,**add_params)
        )
        jsons = r.json()
        if not isinstance(jsons,list):
            raise exceptions.HTTPError
        api_data.extend(jsons)
        if len(jsons) < max_limit:
            break
    return api_data[:limit]



def split_int(raw:str, text_before:str, text_after:str) -> int|None:
    try:
        return int(raw.split(text_before)[1].split(text_after)[0])
    except Exception:
        return None
    
def split(raw:str, text_before:str, text_after:str) -> str:
    return raw.split(text_before)[1].split(text_after)[0]
    
def to_dt(text:str,default:datetime.datetime|None=None) -> datetime.datetime|None:
    try:
        return datetime.datetime.fromisoformat(f'{text.replace("Z","")}+00:00')
    except Exception:
        return default
    
def no_data_checker(obj) -> None:
    if obj is None:
        raise exceptions.NoDataError

empty_project_json = {
    'targets': [
        {
            'isStage': True,
            'name': 'Stage',
            'variables': {
                '`jEk@4|i[#Fk?(8x)AV.-my variable': [
                    'my variable',
                    0,
                ],
            },
            'lists': {},
            'broadcasts': {},
            'blocks': {},
            'comments': {},
            'currentCostume': 0,
            'costumes': [
                {
                    'name': '',
                    'bitmapResolution': 1,
                    'dataFormat': 'svg',
                    'assetId': '14e46ec3e2ba471c2adfe8f119052307',
                    'md5ext': '14e46ec3e2ba471c2adfe8f119052307.svg',
                    'rotationCenterX': 0,
                    'rotationCenterY': 0,
                },
            ],
            'sounds': [],
            'volume': 100,
            'layerOrder': 0,
            'tempo': 60,
            'videoTransparency': 50,
            'videoState': 'on',
            'textToSpeechLanguage': None,
        },
    ],
    'monitors': [],
    'extensions': [],
    'meta': {
        'semver': '3.0.0',
        'vm': '2.3.0',
        'agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    },
}

BIG = 99999999