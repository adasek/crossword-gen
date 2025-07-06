import hashlib
from functools import lru_cache
from typing import Iterator

import numpy as np
import numpy.typing as npt
import pandas as pd

from .language import alphabet
from .mask import Mask
from .word import Word


class WordList:
    """Data structure to effectively find suitable words"""
    counter = 1

    def __init__(self, words_df: pd.DataFrame, language: str):
        self.words_df = words_df
        hash_array: pd.Series = pd.util.hash_pandas_object(self.words_df, index=True)  # type: ignore
        self.dataframe_hash = hashlib.md5(hash_array.values.tobytes()).hexdigest()  # type: ignore

        self.alphabet = alphabet(language)

        self.words_df['word_split'] = None

        self.words_structure: dict[str, set[int]] = {}
        self.word_indices_by_length_set: dict[int, set[int]] = {}

        char_to_index: dict[str, int] = dict((ch, idx) for idx, ch in self.alphabet_with_index())

        for word_index_hashable, row in self.words_df.iterrows():  # type: ignore
            word_index: int = int(word_index_hashable)  # type: ignore
            word_properties: dict[str, int | float | str] = row.to_dict()  # type: ignore

            word = Word(str(word_properties['word_label_text']),
                        str(word_properties['word_description_text']),
                        index=word_index,
                        language=language,
                        score=float(word_properties['score']) if 'score' in word_properties else None,
                        word_list=self,
                        word_concept_id=word_properties['word_concept_id'])

            word_len = len(word)
            if word_len not in self.word_indices_by_length_set:
                self.word_indices_by_length_set[word_len] = set()
            self.word_indices_by_length_set[word_len].add(word_index)
            for char_index, char in enumerate(word):
                key = f"{word_len}_{char_index}_{char}"
                if key not in self.words_structure:
                    self.words_structure[key] = set()
                self.words_structure[key].add(word_index)

            self.words_df.at[word_index, 'word_split'] = word  # type: ignore
            for index, char in enumerate(word):
                if f'word_split_char_{index}' not in self.words_df.columns:
                    split_vector: list[str | None] = [None] * self.words_df.shape[0]
                    char_indices: list[int] = list(char_to_index.values())
                    self.words_df[f'word_split_char_{index}'] = pd.Categorical(split_vector,
                                                                               categories=char_indices)
                self.words_df.at[word_index, f'word_split_char_{index}'] = char_to_index.get(char, None)  # type: ignore

    def use_score_vector(self, score_vector):
        """ Use a score vector to update the words DataFrame with scores. """
        self.words_df.drop([x for x in ['score'] if x in self.words_df.columns], axis=1, inplace=True)
        self.words_df = self.words_df.join(score_vector, on='word_concept_id', how='left', rsuffix='_right')

    def alphabet_with_index(self) -> Iterator[tuple[int, str]]:
        """ Returns an iterator of tuples (index, character) for the alphabet."""
        return enumerate(self.alphabet, start=0)

    def words(self, mask: Mask, chars: Word, failed_indices: list[int] | None = None) -> pd.DataFrame:
        """ Returns a DataFrame of words that match the given mask and characters, excluding failed indices."""
        return self.words_df.take(self.words_indices_without_failed(mask, chars, failed_indices))

    def words_indices_without_failed(
            self,
            mask: Mask,
            chars: Word,
            failed_indices: list[int] | None = None
    ) -> npt.NDArray[np.int32]:
        """ Returns indices of words that match the given mask and characters, excluding failed indices."""
        if failed_indices is None:
            failed_indices = []
        if len(failed_indices) == 0:
            return self.words_indices(mask, chars)

        word_indices = self.words_indices(mask, chars)
        bitmap = np.isin(word_indices, failed_indices)
        return word_indices[bitmap]

    @lru_cache(maxsize=10000)  # type: ignore
    def words_indices(self, mask: Mask, chars: Word) -> npt.NDArray[np.int32]:
        """ Returns indices of words that match the given mask and characters. """
        if mask.length not in self.word_indices_by_length_set:
            raise ValueError(f"No word suitable for the given space (length {mask.length})")

        word_index_set = self.words_indices_sets(mask, chars)

        return np.fromiter(word_index_set, dtype=np.int32, count=len(word_index_set))

    def words_indices_sets(self, mask: Mask, chars: Word) -> set[int]:
        """
        Returns a set of word indices that match the given mask and characters.
        """
        if mask.bind_count() == 0:
            return self.word_indices_by_length_set[mask.length]

        mask_indexes = [mask_index for mask_index, is_masked in enumerate(mask.mask) if is_masked]
        single_letter_sets: list[set[int]] = [
            self.words_structure.get(f"{mask.length}_{mask_index}_{char}", set())
            for mask_index, char in zip(mask_indexes, chars)
        ]
        return set.intersection(*single_letter_sets)

    def candidate_char_vectors(self, mask: Mask, chars: Word, failed_indices: list[int],
                               cross_char_indices: list[int]) -> list[npt.NDArray[np.int32]]:
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
            counts: npt.NDArray[np.int32] = np.bincount(
                words_subset[column_name],  # type: ignore
                minlength=len(self.alphabet)
            )  # type: ignore
            candidate_vectors.append(counts)
        return candidate_vectors

    def __hash__(self) -> int:
        return hash(self.dataframe_hash)
