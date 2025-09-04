from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Literal

from ..utils.types import (
    CheckAnyPayload,
    TranslatePayload,
    TranslateSupportedPayload
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
    
async def translation(client:"HTTPClient",language:str,text:str) -> str:
    """
    テキストを翻訳する。

    Args:
        client (HTTPClient): 使用するHTTPClient
        language (str): 翻訳先の言語コード
        text (str): 翻訳するテキスト

    Returns:
        str: 翻訳されたテキスト
    """
    response = await client.get(
        "https://translate-service.scratch.mit.edu/translate",
        params={
            "language":language,
            "text":text
        }
    )
    data:TranslatePayload = response.json()
    return data.get("result")

async def get_supported_translation_language(client:"HTTPClient") -> dict[str,str]:
    """
    翻訳でサポートされているテキストを取得する。

    Args:
        client (HTTPClient): 使用するHTTPClient

    Returns:
        dict[str,str]: 対応している言語の言語コードと名前のペア
    """
    response = await client.get("https://translate-service.scratch.mit.edu/supported")
    data:TranslateSupportedPayload = response.json()
    return {i.get("code"):i.get("name") for i in data.get("result")}

async def tts(client:"HTTPClient",language:str,type:Literal["male","female"],text:str) -> bytes:
    """
    読み上げ音声を取得する。

    Args:
        client (HTTPClient): 使用するHTTPClient
        language (str): 使用する言語 (en-US形式)
        type (Literal["male","famale"])]: 話す声の種類
        text (str): 話す内容

    Returns:
        bytes:
    """
    response = await client.get(
        "https://synthesis-service.scratch.mit.edu/synth",
        params={
            "locale":language,
            "gender":type,
            "text":text
        }
    )
    return response.data