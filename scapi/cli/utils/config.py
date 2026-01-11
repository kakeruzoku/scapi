import aiofiles
from typing import Self
from pydantic import BaseModel

from .common import app_dir, console

config_path = app_dir / "config.json"


class Config(BaseModel):
    use_user_id: int | None = None
    use_proxy_id: int | None = None

    async def save(self):
        async with aiofiles.open(config_path, mode="w", encoding="utf-8") as f:
            await f.write(self.model_dump_json(indent=4))
        console.print("📄 Config saved.")

    @classmethod
    async def get_config(cls) -> Self:
        if not config_path.exists():
            return cls()

        async with aiofiles.open(config_path, mode="r", encoding="utf-8") as f:
            content = await f.read()
            try:
                return cls.model_validate_json(content)
            except Exception:
                # 破損している場合などはデフォルトを返すかエラーにするか検討が必要ですが、
                # ここでは安全のためにデフォルトを返すようにします
                return cls()
