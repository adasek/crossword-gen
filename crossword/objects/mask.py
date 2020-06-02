import more_itertools
from .charlist import CharList


class Mask(object):
    # Immutable, https://stackoverflow.com/a/4828108
    __slots__ = ["length", "mask"]

    def __init__(self, spaces, crosses=None):
        if crosses:
            super(Mask, self).__setattr__("length", len(spaces))
            # print(f"Creating mask of {len(spaces)} with {spaces} and:")
            # for cross in crosses:
            #    print(f"  {cross}")

            mask_list = []
            for space in spaces:
                space_cross = [cross for cross in crosses if cross.coordinates == space]
                if len(space_cross) == 0:
                    mask_list.append(False)
                elif len(space_cross) == 1:
                    mask_list.append(True)
                elif len(space_cross) > 1:
                    raise Exception("Multiple crosses")
            super(Mask, self).__setattr__("mask", mask_list)
        else:
            # First parameter = mask array
            super(Mask, self).__setattr__("mask", spaces)
            super(Mask, self).__setattr__("length", len(spaces))

    def __hash__(self):
        return hash(self.mask_string())

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.mask == other.mask

    def __str__(self):
        return self.mask_string()

    def mask_string(self):
        mask_string = ""
        for applied in self.mask:
            if applied:
                mask_string += "X"
            else:
                mask_string += "."
        return mask_string

    def all_derivations(self):
        my_indices = []
        for index, applied in enumerate(self.mask):
            my_indices.append(index)

        return [self.from_indices(indices) for indices in more_itertools.powerset(my_indices)]

    def bind_count(self):
        return self.mask.count(True)

    # Returns relevant chars
    def apply_word(self, word):
        applied = []

        for crossed, char in zip(self.mask, word):
            if crossed:
                applied.append(char)
        return CharList(applied)

    def from_indices(self, indices):
        return Mask([(index in indices) for index in range(0, self.length)])