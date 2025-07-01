import inspect
from enum import Enum
from typing import Any, Optional, Union

import numpy as np
import numpy.typing as npt
import pandas as pd

from .charlist import CharList
from .cross import Cross
from .mask import Mask
from .word import Word
from .word_list import WordList


class Direction(Enum):
    """Direction enum for WordSpace orientation."""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"

class WordSpace:
    """Single line of characters in crossroad that will be filled with a word."""

    counter: int = 1

    def __init__(self, start: tuple[int, int], length: int, direction: Direction) -> None:
        """Construct WordSpace without any word."""
        # Specific to word list
        self.failed_words_index_list: list[int] = []

        self.crosses: list[Cross] = []
        self.occupied_by: Optional[Word] = None
        self.possibility_matrix: Optional[npt.NDArray[np.int32]] = None
        self.start: tuple[int, int] = start
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
        unbounded_crosses = self.get_unbounded_crosses()

        cross_char_indices = [self.index_of_cross(cross) for cross in unbounded_crosses]
        candidate_char_vectors = word_list.candidate_char_vectors(*self.mask_current(), self.failed_words_index_list, cross_char_indices)

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
        """Remove binded word from WordSpace.

        Returns:
            List of affected WordSpaces that need updates.
        """
        affected = [self]
        self.occupied_by = None
        for cross in self.crosses:
            if not cross.bound_value():
                affected.append(cross.other(self))
        return affected

    def bindable(self, word_list: WordList) -> pd.DataFrame:
        """List all words that can be filled to WordSpace at this moment."""
        mask, chars = self.mask_current()
        return word_list.words(mask, chars, failed_indices=self.failed_words_index_list)

    def get_unbounded_crosses(self) -> list[Cross]:
        """List crosses that don't have certain Char bound.

        Will return empty list if word is bound to this WordSpace.
        """
        return [cross for cross in self.crosses if not cross.bound_value()]

    def get_half_bound_and_unbound_crosses(self) -> list[Cross]:
        """List crosses that have at least one word bounded."""
        return [cross for cross in self.crosses if cross.is_half_bound_or_unbound()]

    def solving_priority(
            self
    ) -> Union[int, float]:
        """Calculate solving priority for this WordSpace."""
        unbounded_crosses = self.get_unbounded_crosses()
        if len(unbounded_crosses) == 0:
            # This is a must have word!
            return 0

        data = self.count_candidate_crossings()
        # By returning the minimum, crosses with less candidates will be prioritized.
        return min(data)

    def count_candidate_crossings(self) -> list[int]:
        """Count candidate crossings"""
        return [cross.other(self).max_possibilities_on_cross(cross) for cross in self.crosses if not cross.bound_value()]


    def find_best_options(self, word_list: WordList) -> Optional[pd.DataFrame]:
        """Find best word options with scores.

        Returns:
            DataFrame with best word options and their scores, or None if no options.
        """
        unbounded_crosses = self.get_half_bound_and_unbound_crosses()

        words_dataframe = self.bindable(word_list)

        # Create score matrix by mapping characters to scores
        score_matrix = np.zeros(
            shape=(words_dataframe.shape[0], len(unbounded_crosses)),
            dtype=np.float32
        )

        for cross_index, cross in enumerate(unbounded_crosses):
            other_word_space = cross.other(self)
            char_index = cross.cross_index(self)
            other_cross_index = other_word_space.crosses.index(cross)
            possibilities = other_word_space.possibility_matrix[other_cross_index]
            # The word_split_char_{char_index} column contains indices of alphabet chars,
            # that will be used as indices to possibilities (alphabet-length vector of distinct char counts)
            score_matrix[:, cross_index] = possibilities[words_dataframe[f"word_split_char_{char_index}"]]

        # Any character has score 0 -> don't consider it
        positive_mask = (score_matrix > 0).all(axis=1)

        # Calculate total scores (sum across crosses for each word)
        total_scores = score_matrix.sum(axis=1)

        if total_scores.size > 30:
            threshold = np.percentile(total_scores, 95)
            best_mask = (total_scores >= threshold) & positive_mask
        else:
            best_mask = positive_mask

        positive_words_with_score = pd.DataFrame({
            'word_split': words_dataframe['word_split'].values[best_mask],
            'score': total_scores[best_mask]
        })

        sorted_scores = positive_words_with_score.sort_values(by='score', ascending=False)
        return sorted_scores.head(1) if not sorted_scores.empty else None

    def find_best_option(self, word_list: WordList) -> Optional[Word]:
        """Find the single best word option."""
        best_options = self.find_best_options(word_list)
        if best_options is not None:
            return best_options.sort_values(by='score', ascending=False).iloc[0]['word_split']
        return None

    def get_candidate_char_dict(self, word_list: WordList, cross: Cross) -> dict[str, int]:
        """Create a map {'a': [5, ...]} stating the number of words if the given cross is bound to such char.

        The numbers are according to the current binding.
        """
        cross_index = self.crosses.index(cross)

        if cross.is_half_bound() or cross.is_fully_bound():
            return {cross.bound_value(): 1}
        else:
            candidate_char_dict = {char: count for (char, count) in
                                   zip(word_list.alphabet, self.possibility_matrix[cross_index].tolist()) if count > 0}

            return candidate_char_dict

    def current_suitable_words_new_cache_key(self) -> str:
        """Generate new cache key for current suitable words."""
        return f"{self.mask_current()}_{len(self.failed_words_index_list)}"

    def spaces(self) -> list[tuple[int, int]]:
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

    def to_prolog(self) -> str:
        """Convert to Prolog representation."""
        crosses_string = ", ".join([c.id() for c in self.crosses])
        return f'word_space_fill("{self.mask()}", [{crosses_string}], "{self.id()}")'

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

    def mask(self) -> Mask:
        """Get the mask for this WordSpace."""
        return Mask(self.spaces(), self.crosses)

    def mask_current(self, add_cross: Optional[Cross] = None, add_char: str = '') -> tuple[Mask, Word]:
        """Return currently bound mask, optionally with one more bounded char."""
        mask_list = [False] * self.length
        char_list = [None] * self.length

        for cross in self.crosses:
            if cross.bound_value():
                index = self.index_of_cross(cross)
                mask_list[index] = True
                char_list[index] = cross.bound_value()

        if add_cross:
            index = self.index_of_cross(add_cross)
            mask_list[index] = True
            char_list[index] = add_char

        return Mask(mask_list), Word([ch for ch in char_list if ch is not None])

    def masks_all(self, threshold: int) -> list[Mask]:
        """All possible combinations of masks derived from the main mask."""
        mask = self.mask()
        if mask.bind_count() <= threshold:
            return mask.all_derivations()
        else:
            return [mask]

    def one_masks(self) -> list[Mask]:
        """All masks with 1 cross."""
        masks = []
        for cross in self.crosses:
            mask_list = [False] * self.length
            mask_list[cross.cross_index(self)] = True
            masks.append(Mask(mask_list))
        return masks

    def mask_with(self, cross: Cross, word_char: str) -> tuple[Mask, CharList]:
        """Current mask with appended given cross."""
        mask, chars = self.mask_current()
        new_index = self.index_of_cross(cross)
        mask_list = mask.mask
        char_list = []
        char_counter = 0

        for index, val in enumerate(mask_list):
            if index == new_index:
                if val:
                    raise ValueError("Assertion failed: position already masked")
                mask_list[index] = True
                char_list.append(word_char)
            else:
                if val:
                    char_list.append(chars[char_counter])
                    char_counter += 1

        return Mask(mask_list), CharList(char_list)

    def masks_prefix(self) -> list[Mask]:
        """Get prefix derivations of the mask."""
        return self.mask().prefix_derivations()

    def my_char_on_cross(self, cross: Cross) -> Optional[str]:
        """Get character at cross position if word is bound."""
        if not self.occupied_by:
            return None
        return self.occupied_by[self.index_of_cross(cross)]

    def index_of_cross(self, cross: Cross) -> int:
        """Get zero-based char index of cross."""
        return cross.cross_index(self)

    def is_horizontal(self):
        """Check if WordSpace is horizontal."""
        return self.direction == Direction.HORIZONTAL

    def is_vertical(self):
        """Check if WordSpace is vertical."""
        return self.direction == Direction.VERTICAL

    def apply_other_words(self) -> Word:
        """Apply characters from other words at cross positions."""
        applied = []
        for cross in self.crosses:
            applied.append(cross.other(self).my_char_on_cross(cross))
        return Word(applied)

    def char_at(self, x: int, y: int) -> Optional[str]:
        """Get character at specific coordinates."""
        if (x, y) not in self.spaces():
            return None
        if not self.occupied_by:
            return None
        return self.occupied_by[self.spaces().index((x, y))]

    def check_crosses(self) -> bool:
        """Check if all crosses have matching characters."""
        for cross in self.crosses:
            a = self.char_at(cross.coordinates[0], cross.coordinates[1])
            b = cross.other(self).char_at(cross.coordinates[0], cross.coordinates[1])
            if a != b:
                return False
        return True

    def good_mask(self) -> Mask:
        """Generate mask that covers good crosses and reset crosses good status."""
        mask = Mask(self.spaces(), [cross for cross in self.crosses if not cross.good])
        for cross in self.crosses:
            cross.good = True
        return mask

    def unbind_incompatible_crosswords(self) -> None:
        """Unbind crosswords that have incompatible characters."""
        for cross in self.crosses:
            other = cross.other(self)
            if (other.occupied_by and
                    other.char_at(cross.coordinates[0], cross.coordinates[1]) !=
                    self.char_at(cross.coordinates[0], cross.coordinates[1])):
                other.unbind()

    def max_possibilities_on_cross(self, cross: Cross) -> int:
        if self.possibility_matrix is None:
            raise ValueError("Possibility matrix not built")
        return int(self.possibility_matrix[self.crosses.index(cross)].max())


    def to_json(self, export_occupied_by: bool = False) -> dict[str, Any]:
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
        return f"{self.direction}_{self.start[0]}_{self.start[1]}_{self.length}"

    def __str__(self) -> str:
        describing_string = (
            f"{str(self.direction).capitalize()} WordSpace starting at {self.start} "
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
