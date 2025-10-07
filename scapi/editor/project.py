from .common import Base
from .types import SB3Project

class Project(Base):
    def __init__(self):
        pass

    @classmethod
    def from_sb3(cls, data:SB3Project):
        project = cls()
        return project