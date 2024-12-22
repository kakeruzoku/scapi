import requests as sync_req


"""
async def get_csrf_token(ClientSession:Requests) -> str:
    cs = aiohttp.ClientSession()
    return (await cs.get(
        "https://scratch.mit.edu/csrf_token/",headers={
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36"
        },cookies={}
    )).headers["set-cookie"]#.split("scratchsessionsid=")[1].split(";")[0]
"""
def get_csrf_token_sync() -> str:
    return sync_req.get(
        "https://scratch.mit.edu/csrf_token/"
    ).headers["set-cookie"].split(";")[3][len(" Path=/, scratchcsrftoken="):]