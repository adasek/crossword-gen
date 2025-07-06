from dataclasses import dataclass, field

from .charlist import CharList
from .word import Word


@dataclass(frozen=True)
class Mask:
    """
    Immutable mask representing a word space binding status (bound/unbound characters).
    """
    mask: list[bool]
    length: int = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "length", len(self.mask))

    def __hash__(self):
        return hash(self.mask_string())

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.mask == other.mask

    def __str__(self):
        return self.mask_string()

    def mask_string(self) -> str:
        """
        Get the mask as a string representation, e.g. X...X
        :return:
        """
        mask_string = ""
        for applied in self.mask:
            if applied:
                mask_string += "X"
            else:
                mask_string += "."
        return mask_string

    def is_fully_bound(self):
        """
        Returns True if all positions in the mask are bound
        """
        return False not in self.mask

    def bind_count(self):
        """
        Returns the number of bound characters in the mask.
        """
        return self.mask.count(True)

    def apply_word(self, word: Word) -> CharList:
        """
        Applies the mask to a word, returning a CharList of characters that are not crossed out.
        """
        applied = []

        for crossed, char in zip(self.mask, word):
            if crossed:
                applied.append(char)
        return CharList(applied)
