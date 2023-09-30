#!/usr/bin/env python3
from crossword.exporter import PrologExporter
from crossword.runner import Runner
from crossword.objects import WordList
from crossword.parser import Parser
from crossword.solver import Solver
from crossword.objects import Crossword
from pathlib import Path
import json
import cProfile
import numpy as np
import time

DIRECTORY = "."
parser = Parser(DIRECTORY)

#dict_file = "input/Czech.dic"
#words = parser.parse_original_wordlist(dict_file)

start = time.perf_counter()
#words = parser.parse_csv_wordlist("../word-gen/meanings_filtered.txt", delimiter=':')
words_df = parser.load_dataframe('individual_words.pickle.gzip')

#print(words_df.query('word_label_text.str.len() == 4'))
#words_df = words_df.query('word_label_text.str.len() == 4').sample(20000, random_state=1)
#words_df = words_df.sample(20000, random_state=1)
# words = parser.parse_csv_wordlist("../word-gen/words_2020_11_02_useful.txt", delimiter=',')
print(f"  words_df loaded in {round(-start + (time.perf_counter()), 2)}s")

start = time.perf_counter()
# crossword = Crossword.from_grid(Path(DIRECTORY, "crossword4.dat"))
# crossword = Crossword.from_grid(Path(DIRECTORY, "crossword_vkk174.dat"))
crossword = Crossword.from_grid(Path(DIRECTORY, "crossword.dat"))

print(f"  crossword loaded in {round(-start + (time.perf_counter()), 2)}s")
start = time.perf_counter()
# Todo: Build WordList from Dataframe
word_list = WordList(words_df=words_df, language='cs')

print(f"  WordList in {round(-start + (time.perf_counter()), 2)}s")
start = time.perf_counter()

parser.build_possibility_matrix(crossword.word_spaces, word_list)

print(f"  build_possibility_matrix in {round(-start + (time.perf_counter()), 2)}s")
start = time.perf_counter()

# (start with 1-masks)
# X..X.,'ab' = X....,'a' union ...X.,'b'
#  WordList[mask][chars]

# WordSpaces x Words precomputation:
# for every WordSpace produces matrix
# wordlen x number_of_words
# this matrix is in WordSpace and is immutable

# Algorithm:
# word_spaces_to_fill_next = sorted(word_spaces, key=lambda ws: ws.expectation_value(words_by_masks), reverse=True)
# Exceptation value is maximum from  WSMatrix*(inverted_bind_vector)
#
# [20 50 10]
# [5 0 10]
# inverted_bind_vector = [true, false]^-1
#

#exporter = PrologExporter("dataset")
#exporter.export_all(words, word_spaces, possible_masks, words_by_masks)


#runner = Runner('../solve.pl', "dataset")
#runner.run()
#runner.fetch_results(word_spaces)
#print(runner.output(), flush=True)

# Solve
print("Solving:")
solver = Solver()
original_word_spaces = crossword.word_spaces
# profile memory: run
# /usr/bin/time -f "KB:%K user: %U" -- python run.py


max_score = -99999
max_crossword = None
times_to_solve = []
success_counter = 0
failure_counter = 0
for i in range(30):
    # cProfile.run('word_spaces = solver.solve(crossword, word_list)', 'restats')
    start = time.perf_counter()
    word_spaces = solver.solve(crossword, word_list, randomize=0, assign_first_word=True, max_failed_words=200)
    time_to_solve = -start + (time.perf_counter())
    times_to_solve.append(time_to_solve)
    if crossword.is_success():
        success_counter += 1
        print(f"Success, Score: {solver.score}")
    else:
        failure_counter += 1
        print(f"Failed: {solver.score}")

    if crossword.is_success() and crossword.evaluate_score() > max_score:
        max_score = crossword.evaluate_score()
        max_crossword = crossword.get_copy()
    crossword.reset()

average_time_to_solve = np.average(np.array(times_to_solve))
print(f"{success_counter} from {success_counter + failure_counter} ok")
print(f"Average time to solve {average_time_to_solve}")

if max_crossword is None:
    print(crossword)
    print(f"No solutions found")
else:
    print(f"Score: {max_crossword.evaluate_score()}")
    print(max_crossword)
    with open('out_crossword.json', 'w') as json_out:
        json_out.write(json.dumps(json.loads(crossword.to_json()), sort_keys=True, indent=4))
