from enum import Enum
from typing import Optional, TypeAlias, Union

import numpy as np
import numpy.typing as npt
import pandas as pd

from .cross import Cross
from .mask import Mask
from .word import Word
from .word_list import WordList

Coordinates = tuple[int, int]
JsonValue: TypeAlias = Union[str, int, float, bool, None,
list['JsonValue'], Coordinates, dict[str, 'JsonValue'], Optional[list[str]]]


class Direction(Enum):
    """Direction enum for WordSpace orientation."""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class WordSpace:
    """Single line of characters in crossroad that will be filled with a word."""

    counter: int = 1

    def __init__(self, start: Coordinates, length: int, direction: Direction) -> None:
        """Construct WordSpace without any word."""
        # Specific to word list
        self.failed_words_index_list: list[int] = []

        self.crosses: list[Cross] = []
        self.occupied_by: Optional[Word] = None
        self.possibility_matrix: Optional[npt.NDArray[np.int32]] = None
        self.start: Coordinates = start
        self.length: int = length
        self.direction: Direction = direction

    def reset_failed_words(self) -> None:
        """Reset failed words and invalidate cache."""
        self.failed_words_index_list = []

    def build_possibility_matrix(self, word_list: WordList) -> None:
        """Build possibility matrix for word selection."""
        # possible_words number for letter x cross
        self.possibility_matrix = np.zeros(
            shape=(len(self.crosses), len(word_list.alphabet)),
            dtype=np.int32
        )
        self.update_possibilities(word_list)

    def update_possibilities(self, word_list: WordList) -> None:
        """Update possibility matrix based on current state."""
        if self.possibility_matrix is None:
            raise ValueError("Possibility matrix not initialized")

        unbounded_crosses = self._get_unbounded_crosses()

        cross_char_indices = [self._index_of_cross(cross) for cross in unbounded_crosses]
        mask, chars = self._mask_current()
        candidate_char_vectors = word_list.candidate_char_vectors(mask,
                                                                  chars,
                                                                  self.failed_words_index_list,
                                                                  cross_char_indices)

        for candidate_char_vector, cross in zip(candidate_char_vectors, unbounded_crosses):
            cross_index = self.crosses.index(cross)
            self.possibility_matrix[cross_index] = candidate_char_vector

    def bind(self, word: Word) -> list['WordSpace']:
        """Add the word into WordSpace.

        Returns:
            List of affected WordSpaces that need updates.

        Raises:
            ValueError: If word is None or length doesn't match.
        """
        if word is None:
            raise ValueError("Won't bind None")

        if word.length != self.length:
            raise ValueError(
                f"Length of word does not correspond with WordSpace: "
                f"{word} {word.length} != {self.length}"
            )

        affected = []
        for cross in self.crosses:
            if not cross.bound_value():
                affected.append(cross.other(self))
        self.occupied_by = word
        return affected

    def unbind(self) -> list['WordSpace']:
        """Remove bound word from WordSpace.

        Returns:
            List of affected WordSpaces that need updates.
        """
        affected = [self]
        self.occupied_by = None
        for cross in self.crosses:
            if not cross.bound_value():
                affected.append(cross.other(self))
        return affected

    def solving_priority(self) -> int:
        """Calculate solving priority for this WordSpace."""
        unbounded_crosses = self._get_unbounded_crosses()
        if len(unbounded_crosses) == 0:
            # This is a must-have word!
            return 0

        data = self._count_candidate_crossings()
        # By returning the minimum, crosses with fewer candidates will be prioritized.
        return min(data)

    def find_best_option(self, word_list: WordList, randomize: float = 0.0) -> Optional[Word]:
        """Find the single best word option."""
        best_options = self._find_best_options(word_list)

        if best_options is not None:
            sorted_options: pd.DataFrame = best_options.sort_values(by='score', ascending=False)

            if randomize > 0.0:
                index_to_take = min(np.random.poisson(lam=2), sorted_options.shape[0] - 1)
            else:
                index_to_take = 0
            word_split_column_index: int = sorted_options.columns.get_loc('word_split')  # type: ignore
            value: Word = sorted_options.iat[index_to_take, word_split_column_index]  # type: ignore
            return value
        return None

    def spaces(self) -> list[Coordinates]:
        """Return set of positions that this word goes through."""
        spaces = []
        if self.direction == Direction.HORIZONTAL:
            for x in range(self.start[0], self.start[0] + self.length):
                spaces.append((x, self.start[1]))
        elif self.direction == Direction.VERTICAL:
            for y in range(self.start[1], self.start[1] + self.length):
                spaces.append((self.start[0], y))
        else:
            raise ValueError(f"Unknown WordSpace type: {self.direction}")
        return spaces

    def add_cross(self, other_word_space: 'WordSpace') -> None:
        """Add a cross with another WordSpace.

        Raises:
            ValueError: If cross is not in spaces or already present.
        """
        new_cross = Cross(self, other_word_space)
        if new_cross.coordinates not in self.spaces():
            raise ValueError("Tried to add cross not in spaces")
        if new_cross in self.crosses:
            raise ValueError("Tried to add already present cross")
        self.crosses.append(new_cross)

    def my_char_on_cross(self, cross: Cross) -> Optional[str]:
        """Get character at cross position if word is bound."""
        if not self.occupied_by:
            return None
        return self.occupied_by[self._index_of_cross(cross)]

    def is_horizontal(self) -> bool:
        """Check if WordSpace is horizontal."""
        return self.direction == Direction.HORIZONTAL

    def is_vertical(self) -> bool:
        """Check if WordSpace is vertical."""
        return self.direction == Direction.VERTICAL

    def char_at(self, x: int, y: int) -> str:
        """Get character at specific coordinates."""
        if (x, y) not in self.spaces():
            raise ValueError(f"Coordinates {x}, {y} not in WordSpace {self.spaces()}")
        if not self.occupied_by:
            raise ValueError(f"WordSpace {self} is not occupied by any word")
        return self.occupied_by[self.spaces().index((x, y))]

    def max_possibilities_on_cross(self, cross: Cross) -> int:
        """Get a maximum number of crossing words once a specific char is bound to the cross."""
        assert self.possibility_matrix is not None
        possibilities: npt.NDArray[np.int32] = self.possibility_matrix[self.crosses.index(cross)]
        return int(np.max(possibilities))

    def to_json(self, export_occupied_by: bool = False) -> dict[str, JsonValue]:
        """Convert to JSON representation."""
        return {
            'start': self.start,
            'length': self.length,
            'direction': self.direction.value,
            'occupied_by': (
                self.occupied_by.to_json()
                if self.occupied_by is not None and export_occupied_by
                else None
            ),
            'meaning': (
                self.occupied_by.description
                if self.occupied_by is not None
                else None
            )
        }

    def id(self) -> str:
        """Generate unique ID for this WordSpace."""
        return f"{self.direction.value}_{self.start[0]}_{self.start[1]}_{self.length}"

    def _index_of_cross(self, cross: Cross) -> int:
        """Get zero-based char index of cross."""
        return cross.cross_index(self)

    def _bindable(self, word_list: WordList) -> pd.DataFrame:
        """List all words that can be filled to WordSpace at this moment."""
        mask, chars = self._mask_current()
        return word_list.words(mask, chars, failed_indices=self.failed_words_index_list)

    def _mask_current(self, add_cross: Optional[Cross] = None, add_char: str = '') -> tuple[Mask, Word]:
        """Return currently bound mask, optionally with one more bounded char."""
        mask_list = [False] * self.length
        char_list: list[Optional[str]] = [None] * self.length

        for cross in self.crosses:
            if cross.bound_value():
                index = self._index_of_cross(cross)
                mask_list[index] = True
                char_list[index] = cross.bound_value()

        if add_cross:
            index = self._index_of_cross(add_cross)
            mask_list[index] = True
            char_list[index] = add_char

        return Mask(mask=mask_list), Word([ch for ch in char_list if ch is not None])

    def _count_candidate_crossings(self) -> list[int]:
        """Count candidate crossings"""
        return [cross.other(self).max_possibilities_on_cross(cross) for cross in self.crosses if
                not cross.bound_value()]

    def _get_unbounded_crosses(self) -> list[Cross]:
        """List crosses that don't have certain Char bound.

        Will return empty list if word is bound to this WordSpace.
        """
        return [cross for cross in self.crosses if not cross.bound_value()]

    def _get_half_bound_and_unbound_crosses(self) -> list[Cross]:
        """List crosses that have at least one word bounded."""
        return [cross for cross in self.crosses if cross.is_half_bound_or_unbound()]

    def _find_best_options(self, word_list: WordList) -> Optional[pd.DataFrame]:
        """Find best word options with scores.

        Returns:
            DataFrame with best word options and their scores, or None if no options.
        """
        unbounded_crosses = self._get_half_bound_and_unbound_crosses()

        words_dataframe = self._bindable(word_list)

        # Create score matrix by mapping characters to scores
        score_matrix = np.zeros(
            shape=(words_dataframe.shape[0], len(unbounded_crosses)),
            dtype=np.float32
        )

        for cross_index, cross in enumerate(unbounded_crosses):
            other_word_space = cross.other(self)
            assert other_word_space.possibility_matrix is not None

            char_index = cross.cross_index(self)
            other_cross_index = other_word_space.crosses.index(cross)
            possibilities: npt.NDArray[np.int32] = other_word_space.possibility_matrix[other_cross_index]
            # The word_split_char_{char_index} column contains indices of alphabet chars,
            # that will be used as indices to possibilities (alphabet-length vector of distinct char counts)
            score_matrix[:, cross_index] = possibilities[
                words_dataframe[f"word_split_char_{char_index}"]]  # type: ignore

        # Any character has score 0 -> don't consider it
        positive_mask = (score_matrix > 0).all(axis=1)  # type: ignore

        # Calculate total scores (sum across crosses for each word)
        total_scores = score_matrix.sum(axis=1)  # type: ignore

        if total_scores.size > 30:  # type: ignore
            threshold = np.percentile(total_scores, 95)  # type: ignore
            best_mask = (total_scores >= threshold) & positive_mask  # type: ignore
        else:
            best_mask = positive_mask

        positive_words_with_score = pd.DataFrame({
            'word_split': words_dataframe['word_split'].values[best_mask],  # type: ignore
            'score': total_scores[best_mask]  # type: ignore
        })  # type: ignore

        sorted_scores = positive_words_with_score.sort_values(by='score', ascending=False)
        return sorted_scores.head(1) if not sorted_scores.empty else None

    def __str__(self) -> str:
        describing_string = (
            f"{self.direction.value.capitalize()} WordSpace starting at {self.start} "
            f"of length {self.length}"
        )
        if self.occupied_by:
            describing_string += f" occupied by {self.occupied_by}"
        return describing_string

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WordSpace):
            return False
        return (self.start == other.start and
                self.length == other.length and
                self.direction == other.direction)

    def __hash__(self) -> int:
        return hash((self.start, self.length, self.direction))
