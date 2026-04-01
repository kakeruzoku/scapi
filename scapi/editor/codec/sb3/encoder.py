
from .types import SB3Project
from ...model.project import EditorProject


def load_from_project_json(data: SB3Project) -> EditorProject:
    return EditorProject()  # TODO
