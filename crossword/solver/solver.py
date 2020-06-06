import random
from operator import attrgetter


class Solver(object):

    def __init__(self, generate_children_threshold=0):
        self.generate_children_threshold = generate_children_threshold

    def solve(self, all_word_spaces, word_list):
        word_spaces = [w for w in all_word_spaces]

        # One half random fill (vertical for now)
        assigned = []
        failed_pairs = set()
        while True:
            # compute word_space potential
            word_spaces_to_fill_next = sorted(word_spaces, key=lambda ws: ws.expectation_value(word_list), reverse=True)
            if len(word_spaces_to_fill_next) == 0:
                break

            ws = word_spaces_to_fill_next[0]
            print(f"{ws.expectation_value(word_list)}")
            best_option = None
            option_number = 0
            while not best_option or (ws, best_option) in failed_pairs:
                best_option = ws.find_best_option(word_list, option_number)
                option_number += 1
                if not best_option:
                    break

            if not best_option:
                # backtrack
                failed_pair = assigned.pop()
                failed_pair[0].unbind()
                word_spaces.append(failed_pair[0])
                failed_pairs.add(failed_pair)
            else:
                ws.bind(best_option)
                print(f"Assigned {best_option} to {ws}")
                assigned.append((ws, best_option))
                word_spaces.remove(ws)

        return all_word_spaces

    def print(self, word_spaces, crossword):
        # Print crossword
        print("--------")
        for y, line in enumerate(crossword, start=1):
            for x, char in enumerate(line, start=1):
                char = None
                for word_space in word_spaces:
                    # Check if all crossed word_spaces have equal char
                    if not word_space.occupied_by:
                        continue
                    word_space_char = word_space.char_at(x, y)
                    if not word_space_char:
                        continue
                    elif not char:
                        char = word_space_char
                    elif char != word_space_char:
                        raise Exception("Incoherent WordSpaces", x, y, char, word_space_char)
                if not char:
                    char = ' '
                print(char, end="")
            print("")