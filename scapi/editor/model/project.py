
from dataclasses import dataclass, field
from typing import Self, Sequence

from .broadcast import Broadcast
from .sprite import Stage, Sprite


@dataclass(slots=True, kw_only=True)
class EditorProject:
    _stage: Stage | None = None
    _sprites: list[Sprite] = field(default_factory=list)

    @property
    def stage(self) -> Stage:
        assert self._stage is not None
        return self._stage

    @classmethod
    def new(cls) -> Self:
        project = cls()
        project._stage = Stage(
            _project=project
        )
        return project

    # Sprites

    def _snapshot_sprites(self) -> Sequence[Sprite]:
        return self._sprites.copy()

    @property
    def sprites(self) -> Sequence[Sprite]:
        return self._snapshot_sprites()

    def get_sprite_by_name(self, name: str):
        for sprite in self._snapshot_sprites():
            if sprite.name == name:
                return sprite

    def _assert_duplicate_sprite_name(self, name: str):
        if self.get_sprite_by_name(name) is not None:
            raise ValueError(f"{name} is already exist.")

    def create_sprite(self, name: str):
        self._assert_duplicate_sprite_name(name)
        sprite = Sprite(
            _project=self,
            _name=name,
        )
        self._sprites.append(sprite)
        return sprite

    # TODO spriteの順番入れ替え Spriteに関数生やす？
