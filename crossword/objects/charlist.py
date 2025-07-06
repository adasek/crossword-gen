"""
Module: charlist
Defines the CharList class for managing and manipulating lists of characters.
"""
from typing import Iterator


class CharList:
    """
    Represents a list of characters with utility methods for iteration,
    comparison, and serialization.
    """

    def __init__(self, char_list: list[str]):
        self.char_list = char_list
        self.length = len(self.char_list)
        self._iter_counter = 0

    def __iter__(self) -> Iterator[str]:
        self._iter_counter = 0
        return self

    def __next__(self) -> str:
        if self._iter_counter < self.length:
            result = self.char_list[self._iter_counter]
            self._iter_counter += 1
            return result
        raise StopIteration

    def __getitem__(self, index: int) -> str:
        return self.char_list[index]

    def __str__(self) -> str:
        return "".join(self.char_list)

    def __hash__(self) -> int:
        return hash("/".join(self.char_list))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CharList):
            return False
        return self.char_list == other.char_list

    def __add__(self, other: 'CharList') -> 'CharList':
        return CharList(self.char_list + other.char_list)

    def __len__(self) -> int:
        return self.length

    def to_json(self) -> list[str]:
        """
        Serializes the CharList to a JSON-compatible format.
        :return:
        """
        return self.char_list
