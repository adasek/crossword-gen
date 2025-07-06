#!/usr/bin/env python3

import os
import pickle
import time
from pathlib import Path

import numpy as np

from crossword.objects import Crossword
from crossword.solver import Solver

DIRECTORY = "benchmark"

start = time.perf_counter()

word_list_cache = Path(DIRECTORY, f"./benchmark_word_list.pkl")
print(f"Loading WordList from cache {word_list_cache}")
with word_list_cache.open('rb') as f:
        word_list = pickle.load(f)

print(f"  WordList in {round(-start + (time.perf_counter()), 2)}s")

start = time.perf_counter()
crossword_solvable = Crossword.from_grid(Path(DIRECTORY, "crossword.20b.dat"))
crossword_unsolvable = Crossword.from_grid(Path(DIRECTORY, "crossword.20h.dat"))

print(f"  crossword loaded in {round(-start + (time.perf_counter()), 2)}s")
start = time.perf_counter()

crossword_solvable.build_possibility_matrix(word_list)
crossword_unsolvable.build_possibility_matrix(word_list)

solver = Solver()
times_to_solve: dict[Crossword, float] = {}
scores: dict[Crossword, float] = {}

solved_time = 0.0
avg_score = 0.0
unsolvable_time = 0.0
for crossword in [crossword_solvable, crossword_unsolvable]:
    times_to_solve[crossword] = []
    scores[crossword] = []
    for i in range(20):
        crossword.reset()
        crossword.build_possibility_matrix(word_list)

        start = time.perf_counter()
        word_spaces = solver.solve(crossword, word_list, randomize=1.0, max_failed_words=200)
        time_to_solve = -start + (time.perf_counter())
        times_to_solve[crossword].append(time_to_solve)
        scores[crossword].append(solver.score)
        if crossword == crossword_solvable:
            assert(crossword.is_success())

    valid_scores = [s for s in scores[crossword] if s is not None]
    if len(valid_scores) > 0:
        solved_time = round(np.mean(times_to_solve[crossword]), 3)
        avg_score = np.mean(valid_scores)
        print(f"Solved {crossword.grid_file.stem} in {solved_time}s "
            f"with average score {avg_score} ({len(valid_scores)})")
    else:
        unsolvable_time = round(np.mean(times_to_solve[crossword]), 3)
        print(f"Unsolvable {crossword.grid_file.stem} in {unsolvable_time}s")

github_output = os.environ.get("GITHUB_OUTPUT")
if github_output:
    with open(github_output, "a") as fh:
        fh.write(f"solved_time={solved_time}\n")
        fh.write(f"avg_score={avg_score}\n")
        fh.write(f"unsolvable_time={unsolvable_time}\n")
