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

    def prefix_derivations(self):
        return_list = []
        for index, applied in enumerate(self.mask):
            if applied:
                return_list.append(Mask(self.mask[0:index+1] + [False]*(self.length-index - 1)))
        return return_list

    def bind_count(self):
        return self.mask.count(True)

    # Returns relevant chars
    def apply_word(self, word):
        applied = []

        for crossed, char in zip(self.mask, word):
            if crossed:
                applied.append(char)
        return CharList(applied)

    # Returns array of tuples (mask, char)
    # according to this mask one_masks
    def divide(self, chars):
        mask_char_tuples = []
        applied_cnt = 0
        for index, applied in enumerate(self.mask):
            if applied:
                mask_list = [False] * self.length
                mask_list[index] = True
                mask_char_tuples.append((Mask(mask_list), CharList(chars[applied_cnt])))
                applied_cnt += 1

        return mask_char_tuples

    def from_indices(self, indices):
        return Mask([(index in indices) for index in range(0, self.length)])
