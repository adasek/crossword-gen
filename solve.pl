#!/usr/bin/env prolog
:- initialization load_word_space_names, load_word_masks, load_word_space_fills, generate_cross, halt.

load_word_space_names :-
 consult(word_space_names).

load_word_masks :-
 consult(word_masks).

load_word_space_fills :-
 consult(word_space_fills).

find_and_output_word_space(WordSpaceName) :-
    word_space_fill(Mask, Chars, WordSpaceName),
    word_mask(Mask, Chars, WordString),
    print(WordSpaceName),write("="),print(WordString),nl.


generate_cross :-
    write("Crossword filling:"),nl,
    forall(word_space_name(WordSpaceName), find_and_output_word_space(WordSpaceName)).