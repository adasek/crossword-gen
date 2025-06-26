import copy

import numpy as np

from .charlist import CharList
from .language import split


class Word(CharList):

    def __init__(self, word_string: list[str] | str, description: str="", language: str='cs', index: int=-1,
                 word_list=None, word_concept_id=None, score=None):
        if isinstance(word_string, list):
            word_as_list = word_string
        else:
            word_as_list = split(word_string.lower(), locale_code=language)
        CharList.__init__(self, word_as_list)
        self.use = 1  # probability it will be used
        if description is None:
            raise ValueError(f"Description cannot be None for word {word_string}")
        self.description = description
        self.score = score
        self.word_list = word_list
        self.word_concept_id = word_concept_id
        self.index = index

    def get_score(self):
        if self.score is not None:
            return self.score
        if self.word_list is None:
            return 0
        word_row = self.word_list.words_df.loc[self.word_list.words_df['word_concept_id'] == self.word_concept_id]
        if 'score' in word_row.columns and not np.isnan(word_row.iloc[0]['score']):
            self.score = word_row.iloc[0]['score']
        else:
            self.score = 0
        return self.score

    def __deepcopy__(self, memo: dict[int, object]):
        # Create a new instance without calling __init__
        cls = self.__class__
        result = cls.__new__(cls)

        # Add the new object to memo before recursion to handle self-references
        memo[id(self)] = result

        for key, value in self.__dict__.items():
            if key in ['word_list']:
                setattr(result, key, value)
            else:
                # Recursively deepcopy other attributes
                setattr(result, key, copy.deepcopy(value, memo))

        return result
