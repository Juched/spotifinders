from abc import ABC, abstractmethod


class NLPModel(ABC):
    @abstractmethod
    def get_vector(self):
        pass
