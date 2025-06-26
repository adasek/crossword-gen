#!/usr/bin/env python3

import cProfile
import json
import pickle
import time
from pathlib import Path

import numpy as np

from crossword.objects import Crossword, WordList
from crossword.parser import Parser
from crossword.solver import Solver

DIRECTORY = "."
parser = Parser(DIRECTORY)

#dict_file = "input/Czech.dic"
#words = parser.parse_original_wordlist(dict_file)

#words = parser.parse_csv_wordlist("../word-gen/meanings_filtered.txt", delimiter=':')
#words_df = parser.load_dataframe('individual_words.pickle.gzip')
# words_df = parser.load_dataframe('../wordlist.pickle.gzip')  # 'cs'


Path("cache").mkdir(parents=True, exist_ok=True)

start = time.perf_counter()
wordlist_filename = Path('individual_words.pickle.gzip')
word_list_cache = Path("cache",f"wordlist_{wordlist_filename.stem}.pkl")
word_list = None
if word_list_cache.exists() and word_list_cache.is_file():
    print(f"Loading WordList from cache {word_list_cache}")
    with word_list_cache.open('rb') as f:
        word_list = pickle.load(f)
else:
    words_df = parser.load_dataframe(wordlist_filename)
    # words_df = parser.load_dataframe('./words/cs/general_words_matrix.pickle.gzip')  # 'cs'
    # words_df = parser.load_dataframe('./words/jafjdev.pickle.gzip')  # 'en'
    # words_df = words_df.sample(100000, random_state=1)

    #print(words_df.query('word_label_text.str.len() == 4'))
    #words_df = words_df.query('word_label_text.str.len() == 4').sample(20000, random_state=1)
    #words_df = words_df.sample(20000, random_state=1)
    # words = parser.parse_csv_wordlist("../word-gen/words_2020_11_02_useful.txt", delimiter=',')
    print(f"words_df loaded {words_df.shape}")
    print(f"  words_df loaded in {round(-start + (time.perf_counter()), 2)}s")


    start = time.perf_counter()
    # Build WordList from Dataframe
    word_list = WordList(words_df=words_df, language='cs')

    with word_list_cache.open('wb') as f:
        pickle.dump(word_list, f, protocol=pickle.HIGHEST_PROTOCOL)

print(f"  WordList in {round(-start + (time.perf_counter()), 2)}s")

start = time.perf_counter()
# crossword = Crossword.from_grid(Path(DIRECTORY, "grids/crossword4.dat"))
# crossword = Crossword.from_grid(Path(DIRECTORY, "grids/crossword_vkk174.dat"))
# crossword = Crossword.from_grid(Path(DIRECTORY, "grids/crossword.jose.dat"))
crossword = Crossword.from_grid(Path(DIRECTORY, "grids/crossword.20b.dat"))
#for ws in crossword.word_spaces:
#   print(ws)

print(f"  crossword loaded in {round(-start + (time.perf_counter()), 2)}s")
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
    start = time.perf_counter()
    # cProfile.run('word_spaces = solver.solve(crossword, word_list, randomize=0, max_failed_words=200)', 'profiles/restats_e9446e_20h')
    word_spaces = solver.solve(crossword, word_list, randomize=0, max_failed_words=200)
    time_to_solve = -start + (time.perf_counter())
    times_to_solve.append(time_to_solve)
    if crossword.is_success():
        success_counter += 1
        print(f"Success, Score: {solver.score}")
        if crossword.evaluate_score() > max_score:
            max_score = crossword.evaluate_score()
            max_crossword = crossword.get_copy()
    else:
        failure_counter += 1
        print(f"Failed: {solver.score}")

    crossword.reset()
    parser.build_possibility_matrix(crossword.word_spaces, word_list)


average_time_to_solve = np.average(np.array(times_to_solve))
print(f"{success_counter} from {success_counter + failure_counter} ok")
print(f"Average time to solve {average_time_to_solve}")

if max_crossword is None:
    print(crossword)
    print(f"No solutions found")
else:
    print(f"Score: {max_crossword.evaluate_score()}")
    print(max_crossword)
    print(f"As json", max_crossword.to_json(True))
    with open('out_crossword.json', 'w') as json_out:
        json_out.write(json.dumps(json.loads(crossword.to_json()), sort_keys=True, indent=4))
