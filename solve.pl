#!/usr/bin/env prolog
:- initialization load_word_space_names, load_word_masks, load_word_space_fills, generate_cross, halt.

load_word_space_names :-
 consult(word_space_names).

load_word_masks :-
 consult(word_masks).

load_word_space_fills :-
 consult(word_space_fills).

% https://stackoverflow.com/a/15865303
not_used_word(_, []) :- !.

not_used_word(X, [Head|Tail]) :-
     X \= Head,
    not_used_word(X, Tail).

find_and_output_word_space(WordSpaceName, UsedWords, WordString) :-
    word_space_fill(Mask, Chars, WordSpaceName),
    word_mask(Mask, Chars, WordString),
    not_used_word(WordString, UsedWords).
    %print(WordSpaceName),write("="),print(WordString),nl.

solve_word_spaces([],X,X).
solve_word_spaces([WordSpaceName | Rest], UsedWordsBefore, UsedWords) :-
    find_and_output_word_space(WordSpaceName, UsedWordsBefore, WordString),
    solve_word_spaces(Rest, [WordString|UsedWordsBefore], UsedWords).

print_word_spaces([],[]).
print_word_spaces([WordSpaceName|Rest1],[UsedWord|Rest2]) :-
    print(WordSpaceName),write(":"),print(UsedWord),nl,
    print_word_spaces(Rest1,Rest2).


generate_cross :-
    write("..."),nl,
    bagof(WordSpaceName, word_space_name(WordSpaceName), WordSpaceNames),
    solve_word_spaces(WordSpaceNames, [], UsedWords),
    write("Crossword filling:"),nl,
    print_word_spaces(WordSpaceNames, UsedWords).