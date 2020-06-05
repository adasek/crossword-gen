
class Cross:
    def __init__(self, word_space1, word_space2):
        self.word_space_horizontal = None
        self.word_space_vertical = None
        self.coordinates = None
        self.good = True

        if word_space1.type == 'horizontal' and word_space2.type == 'vertical':
            self.word_space_horizontal = word_space1
            self.word_space_vertical = word_space2
        elif word_space1.type == 'vertical' and word_space2.type == 'horizontal':
            self.word_space_vertical = word_space1
            self.word_space_horizontal = word_space2
        else:
            raise Exception("Bad types")

        # Compute coordinates
        cross_coordinates = set(self.word_space_vertical.spaces()).intersection(
            set(self.word_space_horizontal.spaces()))
        if len(cross_coordinates) > 1:
            raise Exception("Non Euclidian crossword")
        elif len(cross_coordinates) == 0:
            raise Exception("Incoherent cross")
        else:
            self.coordinates = cross_coordinates.pop()

    def id(self):
        return f"C_{self.coordinates[0]}_{self.coordinates[1]}"

    def other(self, word_space):
        if word_space == self.word_space_vertical:
            return self.word_space_horizontal
        elif word_space == self.word_space_horizontal:
            return self.word_space_vertical
        else:
            raise Exception("Bad call of other", self, word_space, self.word_space_horizontal, self.word_space_vertical)

    def mask_one(self, type):
        if type == 'horizontal':
            ws = self.word_space_horizontal
        elif type == 'vertical':
            ws = self.word_space_vertical
        else:
            raise Exception("Bad types")

        mask_list = ["."] * ws.length
        mask_list[ws.index_of_cross(self)] = 'X'
        return "".join(mask_list)

    def bound_value(self):
        char = self.word_space_horizontal.my_char_on_cross(self) or  self.word_space_vertical.my_char_on_cross(self)
        return char

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.coordinates == other.coordinates

    def __hash__(self):
        return hash(self.coordinates)

    def __str__(self):
        return f"Cross at {self.coordinates} between {self.word_space_horizontal} and {self.word_space_vertical}"
