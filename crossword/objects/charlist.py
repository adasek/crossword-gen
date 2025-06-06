import json

class CharList:
    def __init__(self, char_list):
        self.char_list = char_list
        self.length = len(self.char_list)
        self._iter_counter = 0

    def __iter__(self):
        self._iter_counter = 0
        return self

    def __next__(self):
        if self._iter_counter < self.length:
            result = self.char_list[self._iter_counter]
            self._iter_counter += 1
            return result
        else:
            raise StopIteration

    def __getitem__(self, index):
        return self.char_list[index]

    def __str__(self):
        return "".join(self.char_list)

    def __hash__(self):
        return hash("/".join(self.char_list))

    def __eq__(self, other):
        return self.char_list == other.char_list

    def __add__(self, other):
        return CharList(self.char_list + other.char_list)

    def __len__(self):
        return self.length

    def to_json(self):
        return self.char_list