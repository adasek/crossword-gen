#!/usr/bin/env python3

# This is a simple heuristic test:
# without a Persona, score ...

from crossword.objects import WordList
from crossword.parser import Parser
from crossword.solver import Solver
from crossword.objects import Crossword
from pathlib import Path
import json
import time
import copy
import csv
from multiprocessing import Pool

DIRECTORY = "."
parser = Parser(DIRECTORY)

def Average(lst):
    return sum(lst) / len(lst)


def init_worker(function, words_all_df):
    function.words_all_df = words_all_df

def worker_do_one(sample_size):
    words_all_df = worker_do_one.words_all_df
    timing = {1: [], 2: [], 3: []}
    counter_ok = 0
    counter_fail = 0
    for i in range(100):
        words_df = words_all_df.sample(sample_size, random_state=i)
        unique = set(words_df.loc[:, 'word_label_text'].map(
            lambda word: word.lower().strip()))
        start = time.perf_counter()
        word_list = WordList(words_df=words_df, language='cs', word_spaces=crossword.word_spaces)
        timing[1].append(-start + (time.perf_counter()))
        start = time.perf_counter()
        parser.build_possibility_matrix(crossword.word_spaces, word_list)
        timing[2].append(-start + (time.perf_counter()))
        # Solve
        start = time.perf_counter()
        solver = Solver()
        timing[3].append(-start + (time.perf_counter()))

        word_spaces = solver.solve(crossword, word_list, max_failed_words=500)
        if word_spaces is not False:
            counter_ok += 1
        else:
            counter_fail += 1
        crossword.reset()

    return {
            'crossword_file': crossword_file,
            'sample_size': sample_size,
            'counter_ok': counter_ok,
            'counter_fail': counter_fail,
            'timing1': Average(timing[1]),
            'timing2': Average(timing[2]),
            'timing3': Average(timing[3])
            }

start = time.perf_counter()
#words = parser.parse_csv_wordlist("../word-gen/meanings_filtered.txt", delimiter=':')
words_all_df = parser.load_dataframe('individual_words.pickle.gzip')
words_all_df.loc[:, 'word_label_text_lower'] = words_all_df.loc[:, 'word_label_text'].map(lambda word: word.lower().strip())
words_all_df = words_all_df.drop_duplicates(subset=['word_label_text_lower'])

for crossword_file in ["crossword.dat"]:

    with open(crossword_file+'.csv', 'w', newline='') as out_file:
        writer = csv.writer(out_file)
        writer.writerow(["crossword_file", "sample_size", "success", "fail", "success_rate", "timing1", "timing2", "timing3"])
        crossword = Crossword.from_grid(Path(DIRECTORY, crossword_file))
        with Pool(processes=12, initializer=init_worker, initargs=(worker_do_one, words_all_df)) as pool:
            for i, result in enumerate(pool.imap(worker_do_one, range(10000, words_all_df.shape[0], 500), chunksize=1)):
                writer.writerow([result['crossword_file'], result['sample_size'],
                                 result['counter_ok'], result['counter_fail'],
                                 (result['counter_ok']/(result['counter_ok']+result['counter_fail'])),
                                 result['timing1'], result['timing2'], result['timing3']
                                 ])
                out_file.flush()
