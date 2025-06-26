from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .word_space import WordSpace

class Cross:
    def __init__(self, word_space1: WordSpace, word_space2: WordSpace):
        self.word_space_horizontal: WordSpace | None = None
        self.word_space_vertical: WordSpace | None = None
        self.index_in_horizontal: int = 0
        self.index_in_vertical: int = 0
        self.coordinates: tuple[int, int] | None = None

        if word_space1.type == 'horizontal' and word_space2.type == 'vertical':
            self.word_space_horizontal = word_space1
            self.word_space_vertical = word_space2
        elif word_space1.type == 'vertical' and word_space2.type == 'horizontal':
            self.word_space_vertical = word_space1
            self.word_space_horizontal = word_space2
        else:
            raise ValueError("Bad types")

        # Compute coordinates
        cross_coordinates = set(self.word_space_vertical.spaces()).intersection(
            set(self.word_space_horizontal.spaces()))
        if len(cross_coordinates) > 1:
            raise ValueError("Non Euclidian crossword")
        if len(cross_coordinates) == 0:
            raise ValueError("Incoherent cross")

        self.coordinates = cross_coordinates.pop()
        self.index_in_horizontal = self.word_space_horizontal.spaces().index(self.coordinates)
        self.index_in_vertical = self.word_space_vertical.spaces().index(self.coordinates)

    def id(self):
        return f"C_{self.coordinates[0]}_{self.coordinates[1]}"

    def cross_index(self, word_space: WordSpace) -> int:
        if word_space == self.word_space_vertical:
            return self.index_in_vertical
        elif word_space == self.word_space_horizontal:
            return self.index_in_horizontal
        else:
            raise Exception("Bad call of cross_index", self, word_space, self.word_space_horizontal,
                            self.word_space_vertical)

    def other(self, word_space):
        if word_space == self.word_space_vertical:
            return self.word_space_horizontal
        elif word_space == self.word_space_horizontal:
            return self.word_space_vertical
        else:
            raise Exception("Bad call of other", self, word_space, self.word_space_horizontal, self.word_space_vertical)

    def bound_value(self):
        return self.bound_value_left() or self.bound_value_right()

    def bound_value_left(self) -> str | None:
        return self.word_space_horizontal.my_char_on_cross(self)

    def bound_value_right(self) -> str | None:
        return self.word_space_vertical.my_char_on_cross(self)

    def is_fully_bound(self) -> bool:
        return self.bound_value_left() is not None and self.bound_value_right() is not None

    def is_half_bound(self) -> bool:
        return (not self.is_fully_bound()) and \
            (self.bound_value_left() is not None or self.bound_value_right() is not None)

    def is_half_bound_or_unbound(self) -> bool:
        return not self.is_fully_bound()

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.coordinates == other.coordinates

    def __hash__(self):
        return hash(self.coordinates)

    def __str__(self):
        return f"Cross at {self.coordinates} between {self.word_space_horizontal} and {self.word_space_vertical}"
