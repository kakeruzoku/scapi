from abc import ABC, abstractmethod
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from . import project

class Base(ABC):

    #@abstractmethod
    def deepcopy(self):
        pass

    #@abstractmethod
    def to_sb3(self):
        pass

    #@abstractmethod
    def to_sb2(self):
        pass