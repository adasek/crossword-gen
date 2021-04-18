from config import ENV
from faktory import Worker
import time
import logging
from pathlib import Path
import pandas as pd
import json
from crossword.objects import WordList
from crossword.objects import Crossword
from crossword.solver import Solver


# Load the general words matrix
lang = 'cs'
# general_words_matrix: word_id, word, description, meta...
general_words_matrix_path = Path('words', lang, 'general_words_matrix.pickle.gzip')
general_words_matrix = pd.read_pickle(general_words_matrix_path, compression='gzip')


# general_categorization_matrix: word_id, categorization
general_categorization_matrix_path = Path('words', lang, 'general_categorization_matrix_1.pickle.gzip')
general_categorization_matrix = pd.read_pickle(general_categorization_matrix_path, compression='gzip')

# todo: let all words
# general_words_matrix = general_words_matrix.sample(10000, random_state=1)
# general_categorization_matrix = general_categorization_matrix.sample(10000, random_state=1)

start = time.perf_counter()
word_list = WordList(words_df=general_words_matrix, language='cs')
print(f"  General wordlist loaded in {round(-start + (time.perf_counter()), 2)}s")

##############################
print("Server ready")

def generate_crossword(crossword_task):
    solver = Solver()
    # load a crossword from request:
    crossword = Crossword.from_grid_object(crossword_task['Grid'])

    # load a user vector from the request
    user_vector = pd.Series(crossword_task['CategorizationPreference']['value']).astype('float64')

    start = time.perf_counter()
    # individual score (vector of wordScore)
    individual_score = general_categorization_matrix.loc[:, user_vector.index].dot(user_vector).rename('score')
    # individual score with word id (vector of wordId,wordScore)
    individual_score_df = pd.concat([general_categorization_matrix.loc[:, 'word_concept_id'], individual_score],
                                    axis=1).set_index('word_concept_id')
    print(f"  individual_score_df in {round(-start + (time.perf_counter()), 2)}s")

    start = time.perf_counter()
    word_list.use_score_vector(individual_score_df)
    print(f"word_list.use_score_vector in {round(-start + (time.perf_counter()), 2)}s")

    start = time.perf_counter()
    for ws in crossword.word_spaces:
        ws.build_possibility_matrix(word_list)
    print(f"build_possibility_matrix in {round(-start + (time.perf_counter()), 2)}s")

    max_score = -99999
    for i in range(30):
        start = time.perf_counter()
        word_spaces = solver.solve(crossword, word_list, randomize=0.05, assign_first_word=True)
        print(f"Score: {solver.score} in {round(-start + (time.perf_counter()), 2)}s")
        # if not solver.solution_found:
        #    print(crossword)
        if word_spaces is not None and solver.score > max_score:
            max_score = solver.score
            max_crossword = crossword.get_copy()
        crossword.reset()
    # todo: send the crossword back
    print(max_crossword)

input_json = json.loads('{"CategorizationPreference":{"categorization_type":1,"createdAt":"2021-04-18T11:49:33.605Z","id":5,"updatedAt":"2021-04-18T11:49:33.605Z","user_id":1,"value":{"ART":"1"}},"Grid":{"bitmap":"XXXXXXXXX     X     XX      X   X  X  X   X X    ","createdAt":"2021-04-18T07:01:40.937Z","height":7,"id":3,"image":"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAcAAAAHCAIAAABLMMCEAAAACXBIWXMAAAPoAAAD6AG1e1JrAAAAHklEQVQImWNgwAP+owIcQpii6GrhbIQomjSIg2YOAGxxXKTq2R7/AAAAAElFTkSuQmCC","updatedAt":"2021-04-18T07:01:40.937Z","user_id":1,"width":7},"categorization_preference_id":5,"createdAt":"2021-04-18T11:49:33.625Z","crossword":null,"grid_id":3,"id":5,"score":null,"status":"created","updatedAt":"2021-04-18T11:49:33.625Z","user_id":1}')
generate_crossword(input_json)


w = Worker(queues=['default'], concurrency=1, faktory=ENV['FAKTORY_URL'])
w.register('CrosswordTask', generate_crossword)
w.run()
