import hashlib
from functools import lru_cache
from typing import Iterator

import numpy as np
import numpy.typing as npt
import pandas as pd

from .language import alphabet, split
from .mask import Mask
from .word import Word


class WordList:
    """Data structure to effectively find suitable words"""
    counter = 1

    def __init__(self, words_df: pd.DataFrame, language: str):
        self.words_df = words_df
        hash_array = pd.util.hash_pandas_object(self.words_df, index=True)
        self.dataframe_hash = hashlib.md5(hash_array.values.tobytes()).hexdigest()

        self.alphabet = alphabet(language)

        # Add column with word length into words_df
        self.words_df.insert(loc=len(self.words_df.columns),
                             column='word_length',
                             value=self.words_df.loc[:, 'word_label_text'].map(
                                 lambda word_str: len(split(word_str.lower(),
                                                            locale_code=language))))
        self.words_df['word_split'] = None

        self.words_structure = {}
        self.word_indices_by_length_set = {}
        self.words_by_index = {}

        for i in sorted(self.words_df.loc[:, 'word_length'].unique()):
            # self.words_df_by_length[i] = self.words_df.loc[self.words_df['word_length'] == i]
            # create X..  .X. ..X combinations
            self.word_indices_by_length_set[i] = set()
        for word_index, row in self.words_df.iterrows():
            word = split(row['word_label_text'].lower(), locale_code=language)
            word_len = len(word)
            self.word_indices_by_length_set[word_len].add(word_index)
            for char_index, char in enumerate(word):
                key = f"{word_len}_{char_index}_{char}"
                if key not in self.words_structure:
                    self.words_structure[key] = set()
                self.words_structure[key].add(word_index)

            if 'score' in row:
                word_score = row['score']
            else:
                word_score = None
            word = Word(row['word_label_text'], row['word_description_text'],
                        index=word_index,
                        language=language,
                        score=word_score,
                        word_list=self,
                        word_concept_id=row['word_concept_id'])
            self.words_by_index[word_index] = word
            self.words_df.at[word_index, 'word_split'] = word
            for index, char in enumerate(word):
                if f'word_split_char_{index}' not in self.words_df.columns:
                    self.words_df[f'word_split_char_{index}'] = None
                self.words_df.at[word_index, f'word_split_char_{index}'] = char

    def use_score_vector(self, score_vector):
        self.words_df.drop([x for x in ['score'] if x in self.words_df.columns], axis=1, inplace=True)
        self.words_df = self.words_df.join(score_vector, on='word_concept_id', how='left', rsuffix='_right')
        # for word_index, row in self.words_df.iterrows():
        #    self.words_by_index[word_index].score = row['score']

    def create_words_by_masks(self, words, possible_masks):
        words_by_masks = {}
        for index, word in enumerate(words):
            for mask in possible_masks:
                if mask.length == word.length:
                    chars = mask.apply_word(word)
                    if mask not in words_by_masks.keys():
                        words_by_masks[mask] = {}
                    if chars not in words_by_masks[mask].keys():
                        words_by_masks[mask][chars] = set()
                    words_by_masks[mask][chars].add(word)

        return words_by_masks

    def alphabet_with_index(self) -> Iterator[tuple[int, str]]:
        return enumerate(self.alphabet, start=0)

    def char_index(self, char: str) -> int:
        for index, ch in enumerate(self.alphabet):
            if ch == char:
                return index
        return -1

    @lru_cache(maxsize=None)
    def word_counts_with_addition(self, mask: Mask, mask_chars: list[str], cross_index: int) -> npt.NDArray[np.int32]:
        parent_mask_indices = self.words_indices(mask, mask_chars)
        letter_and_count = self.words_df.iloc[parent_mask_indices].groupby(f"word_split_char_{cross_index}").size()
        # expand the vector to the alphabet
        letter_to_index = dict((ch, idx) for idx, ch in self.alphabet_with_index())
        result = np.zeros((1, len(self.alphabet)), dtype=np.int32)
        for letter, count in letter_and_count.items():
            col = letter_to_index[letter]
            result[0, col] = count
        return result

    def words(self, mask: Mask, chars: list[str], failed_index: bool = None) -> pd.DataFrame:
        return self.words_df.take(self.words_indices_with_failed_index(mask, chars, failed_index))

    def words_indices_with_failed_index(self, mask: Mask, chars: list[str], failed_index: set[int] = set()) -> npt.NDArray[np.int32]:
        if len(failed_index) == 0:
            return self.words_indices(mask, chars)
        else:
            word_indices = self.words_indices(mask, chars)
            mask = np.isin(word_indices, list(failed_index))
            return word_indices[mask]

    @lru_cache(maxsize=512)
    def words_indices(self, mask: Mask, chars: list[str]) -> npt.NDArray[np.int32]:
        if mask.length not in self.word_indices_by_length_set:
            raise Exception(f"No word suitable for the given space (length {mask.length})")

        word_index_set = self.words_indices_sets(mask, chars)

        return np.fromiter(word_index_set, dtype=np.int32, count=len(word_index_set))

    def words_indices_sets(self, mask: Mask, chars: list[str]) -> set[int]:
        if mask.bind_count() == 0:
            return self.word_indices_by_length_set[mask.length]
        else:
            mask_indexes = [mask_index for mask_index, is_masked in enumerate(mask.mask) if is_masked]
            single_letter_sets: list[set[int]] = [self.words_structure.get(f"{mask.length}_{mask_index}_{char}", set()) for mask_index, char in zip(mask_indexes, chars)]
            return set.intersection(*single_letter_sets)

    def candidate_char_dict(self, words_indices: npt.NDArray[np.int32], char_index: int):
        # TODO: Make this faster opportunity: use np bincount, but the word_split_char should be numeric (indices of chars)
        return self.words_df[f"word_split_char_{char_index}"].iloc[words_indices].value_counts(sort=False).to_dict()

    def get_word_by_index(self, word_index: int):
        return self.words_by_index[word_index]

    def get_words_by_indices(self, word_indices: list):
        return [self.words_by_index[index] for index in word_indices if index in self.words_by_index]

    def __hash__(self):
        return hash(self.dataframe_hash)
