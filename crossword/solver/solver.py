import random
from operator import attrgetter
import time


class Solver(object):

    def __init__(self):
        self.MAX_FAILED_WORDS = 100
        self.t0 = None
        self.t1 = None
        self.solved = False
        self.solution_found = False
        self.solution = None
        self.counters = {'assign': 0, 'backtrack': 0, 'failed': 0}

    def solve(self, all_word_spaces, word_list, crossword):
        self.t0 = time.time()
        for key in self.counters.keys():
            self.counters[key] = 0
        word_spaces = [w for w in all_word_spaces]

        # One half random fill (vertical for now)
        assigned = []
        ws = None
        backtrack = False
        option_number = 0
        best_remaining = len(all_word_spaces)
        while True:
            # compute word_space potential
            if len(word_spaces) == 0:
                break

            if ws is None:
                word_spaces_to_fill_next = sorted(word_spaces, key=lambda ws: ws.expectation_value(word_list), reverse=True)
                if len(word_spaces_to_fill_next) == 0:
                    # No possible spaces => backtrack!
                    raise Exception("backtrack or not?")
                    backtrack = True
                else:
                    option_number = 0
                    ws = word_spaces_to_fill_next[0]
                    #print(f"Picking next ws: {ws}")
                    ws.failed_words = set()

            best_option = None
            while not backtrack and best_option is None:
                best_option = ws.find_best_option(word_list)
                option_number += 1
                if best_option is None:
                    # no possible option
                    backtrack = True
                    break

            #print(f"expectation_value={ws.expectation_value(word_list)}")
            #print(f"best_option={best_option}")

            if backtrack:
                self.counters['backtrack'] += 1
                # print(f"~~~ backtrack ~~~")
                # backtrack
                if len(assigned) == 0:
                    # All possibilites were tried
                    self.t1 = time.time()
                    self.solved = True
                    self.solution_found = False
                    return False
                failed_pair = assigned.pop()
                failed_ws = failed_pair[0]
                failed_word = failed_pair[1]
                failed_ws.unbind()
                word_spaces.append(failed_pair[0])
                # print(f"Giving {failed_ws} back")
                ws = failed_pair[0]
                failed_ws.failed_words.add(failed_word)
                self.counters['failed'] += 1
                if self.counters['failed'] > self.MAX_FAILED_WORDS:
                    # Too many retries on this slot
                    self.t1 = time.time()
                    self.solved = True
                    self.solution_found = False
                    return False
                # print(f"Solving {ws} again")
                backtrack = False
            else:
                ws.bind(best_option) #, True, word_list
                # print(f"Assigned {best_option} to {ws}")
                self.counters['assign'] += 1
                best_remaining = min(best_remaining, len(word_spaces))
                if self.counters['assign'] % 100 == 0:
                    # print(f"Assigned {self.counters['assign']}, remaining: {len(word_spaces)}/{best_remaining}")
                    #for word_space in word_spaces:
                    #    print(word_space)
                    # self.print(all_word_spaces, crossword)
                    pass
                assigned.append((ws, best_option))
                word_spaces.remove(ws)
                #print(f"word_spaces length: {len(word_spaces)}")
                #self.print(all_word_spaces, crossword)
                ws = None
                backtrack = False

        self.t1 = time.time()
        self.solved = True
        self.solution_found = True
        self.solution = all_word_spaces
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

    def time_elapsed(self):
        if not self.solved:
            raise Exception("Not solved")
        return self.t1 - self.t0
