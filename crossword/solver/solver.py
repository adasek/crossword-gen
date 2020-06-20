import random
from operator import attrgetter
import time


class Solver(object):

    def __init__(self):
        self.MAX_FAILED_WORDS = 500
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
                affected = failed_ws.unbind()
                for affected_word_space in affected:
                    affected_word_space.rebuild_possibility_matrix(word_list)
                failed_ws.rebuild_possibility_matrix(word_list)
                word_spaces.append(failed_pair[0])
                # print(f"Giving {failed_ws} back")
                ws = failed_pair[0]
                failed_ws.failed_words.add(failed_word)
                self.counters['failed'] += 1
                if self.counters['failed'] > self.MAX_FAILED_WORDS:
                    # Too many retries
                    self.t1 = time.time()
                    self.solved = True
                    self.solution_found = False
                    return False
                # print(f"Solving {ws} again")
                backtrack = False
            else:
                affected = ws.bind(best_option)
                for affected_word_space in affected:
                    affected_word_space.rebuild_possibility_matrix(word_list)

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

                # find relevant wordspaces (2 or 1)
                associated_word_spaces = []
                for word_space in word_spaces:
                    if (x, y) in word_space.spaces():
                        associated_word_spaces.append(word_space)

                if len(associated_word_spaces) > 2:
                    raise Exception("Char with >2 Wordspaces", x, y)
                elif len(associated_word_spaces) == 0:
                    char = ':'
                else:
                    # Check both crossed wordspaces have equal char
                    char = None
                    not_bound_count = 0
                    ws_retries = 0
                    for ws in associated_word_spaces:
                        if ws.occupied_by is not None and char is not None and char != ws.char_at(x, y):
                            print(f"{ws.char_at(x,y)}")
                            raise Exception("Incoherent WordSpaces", x, y)
                        if ws.occupied_by is not None:
                            char = ws.char_at(x, y)
                        else:
                            not_bound_count += 1
                        ws_retries += len(ws.failed_words)

                    if not char:
                        # both unbounded
                       char = ' '
                    if ws_retries > 0 and char:
                        char = char.upper()
                    if ws_retries > 0 and not char:
                        char = '?'

                print(char, end="")
            print("")

    def time_elapsed(self):
        if not self.solved:
            raise Exception("Not solved")
        return self.t1 - self.t0
