from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .word_space import WordSpace


class Cross:
    """Cross represents a cross between two word spaces in a crossword puzzle."""
    def __init__(self, word_space1: WordSpace, word_space2: WordSpace):
        self.word_space_horizontal: WordSpace | None = None
        self.word_space_vertical: WordSpace | None = None
        self.index_in_horizontal: int = 0
        self.index_in_vertical: int = 0
        self.coordinates: tuple[int, int] | None = None

        if word_space1.is_horizontal() and word_space2.is_vertical():
            self.word_space_horizontal = word_space1
            self.word_space_vertical = word_space2
        elif word_space1.is_vertical() and word_space2.is_horizontal():
            self.word_space_vertical = word_space1
            self.word_space_horizontal = word_space2
        else:
            raise ValueError("Bad word space directions")

        # Compute coordinates
        set_a = set(self.word_space_vertical.spaces())
        set_b = set(self.word_space_horizontal.spaces())
        cross_coordinates = set_a.intersection(set_b)
        if len(cross_coordinates) > 1:
            raise ValueError("Non Euclidian crossword")
        if len(cross_coordinates) == 0:
            raise ValueError("Incoherent cross")

        self.coordinates = cross_coordinates.pop()
        self.index_in_horizontal = self.word_space_horizontal.spaces().index(self.coordinates)
        self.index_in_vertical = self.word_space_vertical.spaces().index(self.coordinates)

    def cross_index(self, word_space: WordSpace) -> int:
        """Returns the character index in the word space that corresponds to this cross."""
        if word_space == self.word_space_vertical:
            return self.index_in_vertical
        if word_space == self.word_space_horizontal:
            return self.index_in_horizontal

        raise ValueError("Bad call of cross_index", self, word_space, self.word_space_horizontal,
                        self.word_space_vertical)

    def other(self, word_space: WordSpace) -> WordSpace:
        """Returns the other word space that is not equal to the given one."""

        if word_space == self.word_space_vertical:
            assert self.word_space_horizontal is not None, "Cross has no other word space"
            return self.word_space_horizontal
        if word_space == self.word_space_horizontal:
            assert self.word_space_vertical is not None, "Cross has no other word space"
            return self.word_space_vertical

        raise ValueError("Bad call of other", self, word_space, self.word_space_horizontal, self.word_space_vertical)

    def bound_value(self) -> str | None:
        """Returns the character that is bound to this cross, or None if it is unbound."""
        return self.bound_value_left() or self.bound_value_right()

    def bound_value_left(self) -> str | None:
        """Returns the character bound to this cross in the horizontal word space, or None if unbound."""
        if self.word_space_horizontal is None:
            return None
        return self.word_space_horizontal.my_char_on_cross(self)

    def bound_value_right(self) -> str | None:
        """Returns the character bound to this cross in the vertical word space, or None if unbound."""
        if self.word_space_vertical is None:
            return None
        return self.word_space_vertical.my_char_on_cross(self)

    def is_fully_bound(self) -> bool:
        """Returns True if both word spaces are bound to this cross."""
        return self.bound_value_left() is not None and self.bound_value_right() is not None

    def is_half_bound(self) -> bool:
        """Returns True if at least one of the word spaces is bound to this cross."""
        return (not self.is_fully_bound()) and \
            (self.bound_value_left() is not None or self.bound_value_right() is not None)

    def is_half_bound_or_unbound(self) -> bool:
        """Returns True if at least one of the word spaces is bound to this cross, or it is unbound."""
        return not self.is_fully_bound()

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.coordinates == other.coordinates

    def __hash__(self):
        return hash(self.coordinates)

    def __str__(self):
        return f"Cross at {self.coordinates} between {self.word_space_horizontal} and {self.word_space_vertical}"
