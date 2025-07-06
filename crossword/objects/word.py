from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Optional

import numpy as np

from .charlist import CharList
from .language import split

if TYPE_CHECKING:
    from .word_list import WordList


class Word(CharList):
    """Represents a word with its characters, description, and associated metadata."""

    def __init__(self, word_string: list[str] | str, description: str = "", language: str = 'cs', index: int = -1,
                 word_list: Optional[WordList] = None, word_concept_id: Optional[int] = None,
                 score: Optional[float] = None):
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
        """
        Returns the score of the word.
         A cached value is used if available, otherwise score is taken from the word list.
         """
        if self.score is not None:
            return self.score
        if self.word_list is None:
            return 0.0
        word_row = self.word_list.words_df.loc[
            self.word_list.words_df['word_concept_id'] == self.word_concept_id
            ]  # type: ignore
        if 'score' in word_row.columns and not np.isnan(word_row.iloc[0]['score']):
            self.score = float(word_row.iloc[0]['score'])  # type: ignore
        else:
            self.score = 0.0
        return self.score

    def __deepcopy__(self, memo: dict[int, object]):
        # Create a new instance without calling __init__
        cls = self.__class__
        result = cls.__new__(cls)

        # Add the new object to memo before recursion to handle self-references
        memo[id(self)] = result

        for key, value in self.__dict__.items():  # type: ignore
            if key in ['word_list']:
                setattr(result, key, value)  # type: ignore
            else:
                # Recursively deepcopy other attributes
                setattr(result, key, copy.deepcopy(value, memo))  # type: ignore

        return result
