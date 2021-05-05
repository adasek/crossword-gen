import random
from operator import attrgetter
import time
import pandas as pd
import random
from random import gauss
import math


class Solver(object):

    def __init__(self):
        self.max_failed_words = 2000
        self.t0 = None
        self.t1 = None
        self.reset()
        self.randomize = True
        self.assign_first_word = True

    def solve(self, crossword, word_list, max_failed_words=2000, randomize=0.5, assign_first_word=True,
              priority_crossing_aggregate: str = 'sum', priority_letter_aggregate: str = 'max', priority_unbound: int = math.inf,
              priority_reverse: bool = True):
        self.reset()
        self.assign_first_word = assign_first_word
        self.randomize = randomize
        self.max_failed_words = max_failed_words

        self.t0 = time.time()
        for key in self.counters.keys():
            self.counters[key] = 0
        word_spaces = [w for w in crossword.word_spaces]

        # assign first word_space randomly
        ws = random.choice(word_spaces)
        word = ws.find_best_option(word_list)
        ws.bind(word)

        assigned = []
        ws = None
        backtrack = False
        option_number = 0
        best_remaining = len(crossword.word_spaces)
        while True:
            # compute word_space potential
            if len(word_spaces) == 0:
                break

            if ws is None:
                word_spaces_to_fill_next = sorted(word_spaces, key=lambda ws: ws.solving_priority(word_list=word_list,
                                                                                                  crossing_aggregate=priority_crossing_aggregate,
                                                                                                  letter_aggregate=priority_letter_aggregate,
                                                                                                  unbound=priority_unbound),
                                                  reverse=priority_reverse)

                if self.randomize > 0 and random.random() < self.randomize and len(word_spaces_to_fill_next) > 1:
                    tmp = word_spaces_to_fill_next[0]
                    word_spaces_to_fill_next[0] = word_spaces_to_fill_next[1]
                    word_spaces_to_fill_next[1] = tmp
                # random.shuffle(word_spaces_to_fill_next)
                if len(word_spaces_to_fill_next) == 0:
                    # No possible spaces => backtrack!
                    raise Exception("backtrack or not?")
                    backtrack = True
                else:
                    option_number = 0
                    ws = word_spaces_to_fill_next[0]
                    # print(f"Picking next ws: {ws}")
                    ws.failed_words_index_set = set()

            best_option = None
            while not backtrack and best_option is None:
                best_option = ws.find_best_option(word_list, 'cs')
                # print(best_option)
                option_number += 1
                if best_option is None:
                    # no possible option
                    backtrack = True
                    break

            # print(f"expectation_value={ws.expectation_value(word_list)}")
            # print(f"best_option={best_option}")

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

                #for affected_word_space in affected:
                #    affected_word_space.rebuild_possibility_matrix(word_list)
                failed_ws.rebuild_possibility_matrix(word_list)
                word_spaces.append(failed_pair[0])
                # print(f"Giving {failed_ws} back")
                ws = failed_pair[0]
                failed_ws.failed_words_index_set.add(failed_word.index)
                self.counters['failed'] += 1
                if self.counters['failed'] > self.max_failed_words:
                    # Too many retries
                    self.t1 = time.time()
                    self.solved = True
                    self.solution_found = False
                    return False
                # print(f"Solving {ws} again")
                backtrack = False
            else:
                affected = ws.bind(best_option)

                # print(crossword)
                #self.print(word_spaces, crossword)
                for affected_word_space in affected:
                    affected_word_space.rebuild_possibility_matrix(word_list)

                # print(f"Assigned {best_option} to {ws}")
                self.counters['assign'] += 1
                best_remaining = min(best_remaining, len(word_spaces))
                if self.counters['assign'] % 100 == 0:
                    # print(f"Assigned {self.counters['assign']}, remaining: {len(word_spaces)}/{best_remaining}")
                    #for word_space in word_spaces:
                    #    print(word_space)
                    # self.print(crossword.word_spaces, crossword)
                    pass
                assigned.append((ws, best_option))
                word_spaces.remove(ws)
                #print(f"word_spaces length: {len(word_spaces)}")
                #self.print(crossword.word_spaces, crossword)
                ws = None
                backtrack = False

        self.score = crossword.evaluate_score()
        self.t1 = time.time()
        self.solved = True
        self.solution_found = True
        self.solution = crossword.word_spaces
        return crossword.word_spaces

    def time_elapsed(self):
        if not self.solved:
            raise Exception("Not solved")
        return self.t1 - self.t0

    def reset(self):
        self.score = 0
        self.solved = False
        self.solution_found = False
        self.solution = None
        self.counters = {'assign': 0, 'backtrack': 0, 'failed': 0}
