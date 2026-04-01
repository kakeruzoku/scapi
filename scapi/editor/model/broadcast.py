

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .project import EditorProject


@dataclass(slots=True, kw_only=True)
class Broadcast:
    name: str
    _project: "EditorProject"

    @property
    def project(self) -> "EditorProject":
        return self._project
