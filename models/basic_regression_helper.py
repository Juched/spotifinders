"""basic regression helper module"""

from collections import Counter
from typing import List


class Indexer:
    """Indexer class"""

    def __init__(self):
        self.objs_to_ints = {}
        self.ints_to_objs = {}

    def __repr__(self):
        return str([str(self.get_object(i)) for i in range(0, len(self))])

    def __str__(self):
        return self.__repr__()

    def __len__(self):
        return len(self.objs_to_ints)

    def get_object(self, index):
        """Get object from index"""
        if index not in self.ints_to_objs:
            return None

        return self.ints_to_objs[index]

    def contains(self, obj):
        """Check if indexer contains object"""
        return self.index_of(obj) != -1

    def index_of(self, obj):
        """Get index from object"""
        if obj not in self.objs_to_ints:
            return -1

        return self.objs_to_ints[obj]

    def add_and_get_index(self, obj, add=True):
        """Add object to indexer and return index, \
        additional param add determines whether object actually gets added"""
        if not add:
            return self.index_of(obj)
        if obj not in self.objs_to_ints:
            new_idx = len(self.objs_to_ints)
            self.objs_to_ints[obj] = new_idx
            self.ints_to_objs[new_idx] = obj
        return self.objs_to_ints[obj]


class UnigramFeatureExtractor:
    """Unigram Feature extractor class"""

    def __init__(self, indexer: Indexer):
        self._indexer = indexer

    def get_indexer(self) -> Indexer:
        """Get indexer"""
        return self._indexer

    def extract_features(
        self, sentence: List[str], add_to_indexer: bool = False
    ) -> Counter:
        """Extract features from sentence and return counter"""

        # Contains non-unique list of all unigrams parsed from the sentence
        unigram_list: List[str] = []

        for unigram in sentence:

            index = self._indexer.add_and_get_index(unigram.lower(), add_to_indexer)

            # If unigram didn't get added to the indexer (this occurs during the testing phase)
            if index != -1:
                unigram_list.append(unigram.lower())

        return Counter(unigram_list)
