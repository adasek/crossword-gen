:- initialization load_words, load_words_usable, load_word_space_names, load_word_masks, load_word_space_fills, generate_cross.

load_words_usable :-
 consult(words_usable).

load_words :-
 consult(words).

load_word_space_names :-
 consult(word_space_names).

load_word_masks :-
 consult(word_masks).

load_word_space_fills :-
 style_check(-singleton),
 consult(word_space_fills),
 style_check(+singleton).

%! find_and_output_word_space(+WordSpaceName:string, -WordId:integer) is nondet
%% For a WordSpace find a suitable Word and return its id.
find_word_space(WordSpaceName, WordId) :-
    word_space_fill(Mask, Chars, WordSpaceName),
    word_mask(Mask, Chars, WordId),
    usable_word(WordId, 1).

% https://stackoverflow.com/a/15865303
not_in_used_words(_, []).

not_in_used_words(X, [WordId|Tail]) :-
     X \= WordId,
    not_in_used_words(X, Tail).

%! solve_word_spaces(+WordSpaceNames:list, +UsedWordsBefore:list, -UsedWords:list) is nondet
%% Recursively call search for suitable word for every WordSpace given in first parameter
%% After match is made, remove the word from usable words
solve_word_spaces([],X,X).
solve_word_spaces([WordSpaceName | Rest], UsedWordsBefore, UsedWords) :-
    find_word_space(WordSpaceName, WordId),
    not_in_used_words(WordId, UsedWordsBefore),
    solve_word_spaces(Rest, [WordId|UsedWordsBefore], UsedWords).

%! print_word_spaces(+WordSpaceNames:list, +UsedWords:list) is nondet
%% Print words that were found for respective WordSpaces.
%% Second parameter is list of word ids
print_word_spaces([],[]).
print_word_spaces([WordSpaceName|Rest1],[UsedWordId|Rest2]) :-
    word(UsedWordId, WordString),
    print(WordSpaceName),write(":"), print(WordString),nl,
    print_word_spaces(Rest1, Rest2).


%! generate_cross() is nondet
%% Main function for Crossword generation
generate_cross :-
    write("..."),nl,
    bagof(WordSpaceName, word_space_name(WordSpaceName), WordSpaceNames),
    solve_word_spaces(WordSpaceNames, [], UsedWords),
    %profile(call_with_time_limit(10,     ....   ))
    write("Crossword filling:"),nl,
    print_word_spaces(WordSpaceNames, UsedWords),
    halt(0).

generate_cross :-
    !, halt(1).