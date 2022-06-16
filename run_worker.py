#!/usr/bin/env python3

from config import ENV
import faktory
from faktory import Worker
import time
import logging
from pathlib import Path
import pandas as pd
import json
import requests
import re
from crossword.objects import WordList
from crossword.objects import Crossword
from crossword.solver import Solver

# Quick and dirty description filter
# todo: move this to the Wordgen!
def shorten_description(description_text, label_text):
    text = description_text
    text = re.compile(label_text, re.IGNORECASE).sub('***', text)
    text = re.compile("^[*][*][*] (je|jsou|byl|byla)", re.IGNORECASE).sub('', text)
    text = re.compile('[*][*][*],[^,]*, (je|jsou|byl|byla)', re.IGNORECASE).sub('', text)
    # text = re.compile('\([^)]*\)', re.IGNORECASE).sub('', text)
    return text.strip()

def shorten_description_row(row):
    previous_description = row['word_description_text']
    new_description = shorten_description(previous_description, row['word_label_text'])
    row['word_description_text'] = new_description
    return row


logger = logging.getLogger('run_worker')

stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stdout_handler.setFormatter(formatter)

logger.addHandler(stdout_handler)

logging.info("Server starting: loading general_words_matrix")
# Load the general words matrix
lang = 'cs'
# general_words_matrix: word_id, word, description, meta...
general_words_matrix_path = Path('words', lang, 'general_words_matrix.pickle.gzip')
general_words_matrix = pd.read_pickle(general_words_matrix_path, compression='gzip')

general_words_matrix = general_words_matrix.apply(shorten_description_row, axis=1)
general_words_matrix = general_words_matrix[general_words_matrix['word_description_text'] != ""]
logging.info("Server starting: general_words_matrix loaded")

logging.info("Server starting: loading general_categorization_matrix")
# general_categorization_matrix: word_id, categorization
general_categorization_matrix_path = Path('words', lang, 'general_categorization_matrix_1.pickle.gzip')
general_categorization_matrix = pd.read_pickle(general_categorization_matrix_path, compression='gzip')

logging.info("Server starting: general_categorization_matrix loaded")
# todo: let all words
# general_words_matrix = general_words_matrix.sample(10000, random_state=1)
# general_categorization_matrix = general_categorization_matrix.sample(10000, random_state=1)

logging.info("Server starting: parsing General wordlist")
start = time.perf_counter()
word_list = WordList(words_df=general_words_matrix, language='cs')
logging.debug(f"  General wordlist loaded in {round(-start + (time.perf_counter()), 2)}s")
logging.info("Server starting: General wordlist ready")

##############################
logging.info("Server ready")

def generate_crossword(crossword_task):
    logging.info(f"starting generate_crossword for task #{crossword_task['id']}")
    logging.debug(crossword_task)
    solver = Solver()
    # load a crossword from request:
    crossword = Crossword.from_grid_object(crossword_task['Grid'])

    # load a user vector from the request
    if 'value' not in crossword_task['CategorizationPreference']:
        raise Exception("Empty CategorizationPreference")
    user_vector = pd.Series(data=crossword_task['CategorizationPreference']['value'], dtype='float64')

    start = time.perf_counter()
    # individual score (vector of wordScore)
    individual_score = general_categorization_matrix.loc[:, user_vector.index].dot(user_vector).rename('score')
    # individual score with word id (vector of wordId,wordScore)
    individual_score_df = pd.concat([general_categorization_matrix.loc[:, 'word_concept_id'], individual_score],
                                    axis=1).set_index('word_concept_id')
    logging.debug(f"  individual_score_df in {round(-start + (time.perf_counter()), 2)}s")

    start = time.perf_counter()
    word_list.use_score_vector(individual_score_df)
    logging.debug(f"word_list.use_score_vector in {round(-start + (time.perf_counter()), 2)}s")

    start = time.perf_counter()
    for ws in crossword.word_spaces:
        ws.build_possibility_matrix(word_list)
    logging.debug(f"build_possibility_matrix in {round(-start + (time.perf_counter()), 2)}s")

    max_score = -99999
    max_crossword = None
    for i in range(int(ENV['CROSSWORD_REGENERATE_COUNT']) or 10):
        start = time.perf_counter()
        word_spaces = solver.solve(crossword,
                                   word_list,
                                   randomize=0.05,
                                   assign_first_word=True,
                                   max_failed_words=int(ENV['CROSSWORD_MAX_FAILED_WORDS']) or 50
                                   )
        logging.debug(f"Score: {solver.score} in {round(-start + (time.perf_counter()), 2)}s")
        # if not solver.solution_found:
        #    logging.debug(crossword)
        if crossword.is_success() and crossword.evaluate_score() > max_score:
            max_score = crossword.evaluate_score()
            max_crossword = crossword.get_copy()
        crossword.reset()
    # Send the crossword back
    if 'webhook' in crossword_task:
        url = crossword_task['webhook']
    else:
        url = ENV['SOLVE_WEBHOOK_URL_DEFAULT']
        solved_task = crossword_task.copy()
        if max_crossword is not None:
            solved_task['crossword'] = max_crossword.as_json(export_occupied_by=True)
            solved_task['score'] = max_score
            solved_task['status'] = 'success'
        else:
            solved_task['status'] = 'unfeasible'
        response = requests.post(url, json=solved_task)
        logging.debug(response.status_code)
        if response.status_code < 300:
            logging.debug(response.json())

# input_json = json.loads('{"CategorizationPreference":{"categorization_type":1,"createdAt":"2021-04-18T11:49:33.605Z","id":5,"updatedAt":"2021-04-18T11:49:33.605Z","user_id":1,"value":{"ART":"1"}},"Grid":{"bitmap":"XXXXXXXXX     X     XX      X   X  X  X   X X    ","createdAt":"2021-04-18T07:01:40.937Z","height":7,"id":3,"image":"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAcAAAAHCAIAAABLMMCEAAAACXBIWXMAAAPoAAAD6AG1e1JrAAAAHklEQVQImWNgwAP+owIcQpii6GrhbIQomjSIg2YOAGxxXKTq2R7/AAAAAElFTkSuQmCC","updatedAt":"2021-04-18T07:01:40.937Z","user_id":1,"width":7},"categorization_preference_id":5,"createdAt":"2021-04-18T11:49:33.625Z","crossword":null,"grid_id":3,"id":5,"score":null,"status":"created","updatedAt":"2021-04-18T11:49:33.625Z","user_id":1}')
# input_json = json.loads('{"id":9,"user_id":1,"grid_id":8,"categorization_preference_id":9,"status":"created","createdAt":"2021-04-19T16:01:41.845Z","updatedAt":"2021-04-19T16:31:55.864Z","Grid":{"image":"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAMCAIAAADUCbv3AAAACXBIWXMAAAPoAAAD6AG1e1JrAAAANElEQVQYlWNgIAj+YwMMYHHs0gwwQSzSDEgiOA2HyqFZj4WLZiB2u3Gpw66PLGksjscjDQA4WgEOOngFMQAAAABJRU5ErkJggg==","id":8,"user_id":1,"width":10,"height":12,"bitmap":"XXXXXXXXXXX       X X      X  X     X   X        XXX   XX   X X    X  X  X X    X    X    X    X    X         X         ","createdAt":"2021-04-18T11:15:56.871Z","updatedAt":"2021-04-18T11:15:56.871Z"},"CategorizationPreference":{"id":9,"user_id":1,"categorization_type":1,"value":{"BIO":"-1","CHE":"1","ECO":"1","EDU":"-1","GEO":"0.3","HIS":"-1","ICT":"1","INF":"0","LAN":"-1","LAW":"-1","LIF":"-1","MAT":"1","MED":"-1","MIX":"-1","PHI":"-1","PHY":"1","POL":"-1","PSY":"-1","REC":"-1","SCT":"-1","SOC":"-1","SPO":"-1","TEC":"1","THE":"-1"},"createdAt":"2021-04-19T16:01:41.829Z","updatedAt":"2021-04-19T16:01:41.829Z"}}')
# generate_crossword(input_json)

worker = None
while True:
    try:
        if worker is None:
            worker = Worker(queues=['default'], concurrency=1, faktory=ENV['FAKTORY_URL'])
            worker.register('CrosswordTask', generate_crossword)
        try:
            worker.run()
        except ConnectionRefusedError:
            time.sleep(60)
            continue
    except json.decoder.JSONDecodeError:
        # todo: log this
        print(f"probably server heartbeat missed")
        time.sleep(30)
    except faktory.exceptions.FaktoryConnectionResetError:
        worker = None
        time.sleep(60)
        # try to revive the worker
