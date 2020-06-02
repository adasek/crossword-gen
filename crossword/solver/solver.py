import random
from operator import attrgetter


class Solver(object):

    def __init__(self, generate_children_threshold=0):
        self.generate_children_threshold = generate_children_threshold

    def find_some_replacements(self, words_by_masks, word_space):
        mask = word_space.good_mask()
        if self.generate_children_threshold > 0 and mask.bind_count() <= self.generate_children_threshold:
            submasks = mask.all_derivations()
        else:
            submasks = [mask]
        submasks.sort(key=attrgetter('length'), reverse=True)
        for submask in submasks:
            subchars = submask.apply_word(word_space.occupied_by)
            if submask in words_by_masks and subchars in words_by_masks[submask]:
                return list(words_by_masks[submask][subchars])
        raise KeyError

    def solve(self, word_spaces, words_by_length, words_by_masks):
        iteration_counter = 1

        # Make two disjoint sets
        word_spaces_horizontal = [w for w in word_spaces if w.type == 'horizontal']
        word_spaces_vertical = [w for w in word_spaces if w.type == 'vertical']

        # One half random fill (vertical for now)
        for word_space in word_spaces_vertical:
            word_space.bind(random.choice(words_by_length[word_space.length]))
        while True:
            not_fillable = []
            for word_space in word_spaces_horizontal:
                if word_space.occupied_by:
                    # Word already bound
                    continue

                mask = word_space.mask()
                required_chars = word_space.apply_other_words()
                try:
                    candidates = list(words_by_masks[mask][required_chars])
                    word_space.bind(random.choice(candidates))
                except KeyError:
                    not_fillable.append(word_space)
            if len(not_fillable) == 0:
                break
            # Replace all random choices crossing not_fillable
            to_replace = []
            for word_space in not_fillable:
                for cross in word_space.crosses:
                    cross.good = False
                    to_replace.append(cross.other(word_space))

            for word_space in to_replace:
                # based on good property of its crosses
                # it tries to find such masks to keep good and change other
                try:
                    candidates = self.find_some_replacements(words_by_masks, word_space)
                    word_space.bind(random.choice(candidates))
                except KeyError:
                    # no good-chars keeping candidate  => must reroll whole word
                    word_space.bind(random.choice(words_by_length[word_space.length]))
                # Remove the incompatible crossing words
                word_space.unbind_incompatible_crosswords()

            print(f"{iteration_counter} ... {len(not_fillable)}/{len(word_spaces_horizontal)} not fillable")
            iteration_counter += 1

        # Print crossword
        print(f"After {iteration_counter} steps")
        print("--------")
        for y, line in enumerate(crossword, start=1):
            for x, char in enumerate(line, start=1):
                char = None
                for word_space in word_spaces:
                    # Check if all crossed word_spaces have equal char
                    word_space_char = word_space.char_at(x, y)
                    if not word_space_char:
                        continue
                    elif not char:
                        char = word_space_char
                    elif char != word_space_char:
                        raise Exception("Incoherent WordSpaces", char, word_space_char)
                if not char:
                    char = ' '
                print(char, end="")
            print("")