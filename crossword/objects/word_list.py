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

        char_to_index = dict((ch, idx) for idx, ch in self.alphabet_with_index())

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
                    self.words_df[f'word_split_char_{index}'] = pd.Categorical([None] * self.words_df.shape[0], categories=list(char_to_index.values()))
                self.words_df.at[word_index, f'word_split_char_{index}'] = char_to_index[char]

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

    def words(self, mask: Mask, chars: list[str], failed_indices: list[int] = []) -> pd.DataFrame:
        return self.words_df.take(self.words_indices_without_failed(mask, chars, failed_indices))

    def words_indices_without_failed(
            self,
            mask: Mask,
            chars: list[str],
            failed_indices: list[int] = []
    ) -> npt.NDArray[np.int32]:
        if len(failed_indices) == 0:
            return self.words_indices(mask, chars)
        else:
            word_indices = self.words_indices(mask, chars)
            mask = np.isin(word_indices, failed_indices)
            return word_indices[mask]

    @lru_cache(maxsize=None)
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
            single_letter_sets: list[set[int]] = [
                self.words_structure.get(f"{mask.length}_{mask_index}_{char}", set())
                for mask_index, char in zip(mask_indexes, chars)
            ]
            return set.intersection(*single_letter_sets)

    # todo: cache?
    # @lru_cache(maxsize=None)
    def candidate_char_vectors(self, mask: Mask, chars: list[str], failed_indices: list[int], cross_char_indices: list[int]) -> list[npt.NDArray[np.int32]]:
        """
        Returns a list of vectors representing the counts of characters in the alphabet for each cross character index.
        Each element corresponds to an alphabet index of a potentially assigned cross character
        """

        column_names = [f"word_split_char_{cross_char_index}" for cross_char_index in cross_char_indices]

        words_indices = self.words_indices_without_failed(mask, chars, failed_indices)
        words_subset = self.words_df[column_names].iloc[words_indices]
        candidate_vectors = []
        for column_name in column_names:
            # For categorical columns, value_counts preserves all categories
            counts = np.bincount(words_subset[column_name], minlength=len(self.alphabet))
            candidate_vectors.append(counts)
        return candidate_vectors

    def get_word_by_index(self, word_index: int):
        return self.words_by_index[word_index]

    def get_words_by_indices(self, word_indices: list):
        return [self.words_by_index[index] for index in word_indices if index in self.words_by_index]

    def __hash__(self):
        return hash(self.dataframe_hash)
