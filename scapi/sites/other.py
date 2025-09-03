from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from ..utils.types import (
    CheckAnyPayload
)
from ..utils.common import (
    UNKNOWN,
    MAYBE_UNKNOWN,
)

if TYPE_CHECKING:
    from ..utils.client import HTTPClient

class UsernameStatus(Enum):
    valid="valid username"
    exist="username exists"
    invalid="invalid username"
    bad="bad username"

async def check_username(client:"HTTPClient",username:str) -> MAYBE_UNKNOWN[UsernameStatus]:
    """
    ユーザー名が利用可能か確認する。

    Args:
        client (HTTPClient): 通信に使用するHTTPClient
        username (str): 確認したいユーザー名

    Returns:
        MAYBE_UNKNOWN[UsernameStatus]:
    """
    response = await client.get(f"https://api.scratch.mit.edu/accounts/checkusername/{username}")
    data:CheckAnyPayload = response.json()
    msg = data.get("msg")
    if msg in UsernameStatus:
        return UsernameStatus(data.get("msg"))
    else:
        return UNKNOWN
    
class PasswordStatus(Enum):
    valid="valid password"
    invalid="invalid password"
    
async def check_password(client:"HTTPClient",password:str) -> MAYBE_UNKNOWN[PasswordStatus]:
    """
    パスワードが使用可能か確認する。

    Args:
        client (HTTPClient): 通信に使用するHTTPClient
        password (str): 確認したいパスワード

    Returns:
        MAYBE_UNKNOWN[PasswordStatus]:
    """
    response = await client.post(f"https://api.scratch.mit.edu/accounts/checkpassword/",json={"password":password})
    data:CheckAnyPayload = response.json()
    msg = data.get("msg")
    if msg in PasswordStatus:
        return PasswordStatus(data.get("msg"))
    else:
        return UNKNOWN

class EmailStatus(Enum):
    vaild="valid email"
    invaild="Scratch is not allowed to send email to this address."

async def check_email(client:"HTTPClient",email:str) -> MAYBE_UNKNOWN[EmailStatus]:
    """
    メールアドレスが利用可能か確認する。

    Args:
        client (HTTPClient): 通信に使用するHTTPClient
        email (str): 確認したいメールアドレス

    Returns:
        MAYBE_UNKNOWN[EmailStatus]:
    """
    response = await client.get(f"https://scratch.mit.edu/accounts/check_email/",params={"email":email})
    data:CheckAnyPayload = response.json()[0]
    msg = data.get("msg")
    if msg in EmailStatus:
        return EmailStatus(data.get("msg"))
    else:
        return UNKNOWN