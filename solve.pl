#!/usr/bin/env prolog
:- initialization load_words, load_words_usable, load_word_space_names, load_word_masks, load_word_space_fills, generate_cross, halt.

% hash of used words
:- dynamic usable_word/2.

load_words_usable :-
 consult(words_usable).

load_words :-
 consult(words).

load_word_space_names :-
 consult(word_space_names).

load_word_masks :-
 time(consult(word_masks)).

load_word_space_fills :-
 consult(word_space_fills).

%! find_and_output_word_space(+WordSpaceName:string, -WordId:integer) is nondet
%% For a WordSpace find a suitable Word and return its id.
find_and_output_word_space(WordSpaceName, WordId) :-
    word_space_fill(Mask, Chars, WordSpaceName),
    word_mask(Mask, Chars, WordId),
    usable_word(WordId, 1).

%! solve_word_spaces(+WordSpaceNames:list, +UsedWordsBefore:list, -UsedWords:list) is nondet
%% Recursively call search for suitable word for every WordSpace given in first parameter
%% After match is made, remove the word from usable words
solve_word_spaces([],X,X).
solve_word_spaces([WordSpaceName | Rest], UsedWordsBefore, UsedWords) :-
    find_and_output_word_space(WordSpaceName, WordId),
    retract(usable_word(WordId, WordUsability)),
    solve_word_spaces(Rest, [[WordId, WordUsability]|UsedWordsBefore], UsedWords).

%! print_word_spaces(+WordSpaceNames:list, +UsedWords:list) is nondet
%% Print words that were found for respective WordSpaces.
%% Second parameter is list of word ids
print_word_spaces([],[]).
print_word_spaces([WordSpaceName|Rest1],[[UsedWordId|_]|Rest2]) :-
    word(UsedWordId, WordString),
    print(WordSpaceName),write(":"), print(WordString),nl,
    print_word_spaces(Rest1, Rest2).

%! return_usable_words(+UsedWords:list) is nondet
%% Return words that were retracted during solve_word_spaces into database
return_usable_words([]).
return_usable_words([[UsedWordId|UsedWordUsability]|Rest]) :-
    asserta(usable_word(UsedWordId, UsedWordUsability)),
    return_usable_words(Rest).

%! generate_cross() is nondet
%% Main function for Crossword generation
generate_cross :-
    write("..."),nl,
    bagof(WordSpaceName, word_space_name(WordSpaceName), WordSpaceNames),
    time(solve_word_spaces(WordSpaceNames, [], UsedWords)),
    %profile(call_with_time_limit(10,     ....   ))
    write("Crossword filling:"),nl,
    print_word_spaces(WordSpaceNames, UsedWords),
    return_usable_words(UsedWords).