"""Implementation of NLP model abstract classes"""
from abc import ABC, abstractmethod
import string


class NLPModel(ABC):
    """A base class for models to implement"""

    @abstractmethod
    def __init__(self):
        """
        This is a base abstract class which all models will implement.

        Args:
            None

        Returns:
            A Model

        """

    @abstractmethod
    def get_vector(self, text: string):
        """
        Runs the model in the file and outputs a 3 length vector to send to spotify

        Args:
            text: The text to get the vector for.

        Returns:
            A length 3 dictionary which has
            {'danceability': float, 'energy': float, 'valence': float}.

        """

    def do_nothing(self):
        """Do nothing"""
