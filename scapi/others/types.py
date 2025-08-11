from typing import TypedDict


DecodedSessionID = TypedDict(
    "DecodedSessionID",{
        "token":str,
        "username":str,
        "login-ip":str,
        "_auth_user_id":str
    }
)