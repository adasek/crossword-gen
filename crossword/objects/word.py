from .charlist import CharList
from .language import split
import numpy as np

class Word(CharList):
    id = 1

    def __init__(self, word_string, description="", language='cs', index=None, word_list=None, word_concept_id=None, score=None):
        if isinstance(word_string, list):
            word_as_list = word_string
        else:
            word_as_list = split(word_string.lower(), locale_code=language)
        CharList.__init__(self, word_as_list)
        self.use = 1  # probability it will be used
        self.id = Word.id
        if description is None:
            print(f"Description none {word_string}")
        self.description = description
        self.score = score
        self.word_list = word_list
        self.word_concept_id = word_concept_id
        self.index = index
        Word.id += 1

    def get_score(self):
        if self.score is not None:
            return self.score
        if self.word_list is None:
            return 0
        word_row = self.word_list.words_df.loc[self.word_list.words_df['word_concept_id'] == self.word_concept_id]
        if 'score' in word_row.columns and not np.isnan(word_row.iloc[0]['score']):
            self.score = word_row.iloc[0]['score']
            return word_row.iloc[0]['score']
        else:
            self.score = 0
            return 0

    def set_score_in_stone(self):
        self.score = None
        self.score = self.get_score()
        self.word_list = None
