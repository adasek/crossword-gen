:- initialization mark_start_time, load_words, load_words_usable, load_word_space_names, load_word_masks, load_crosses, load_word_space_fills, generate_cross.

mark_start_time :-
 get_time(TimeStarted),
 assertz(get_time_started(TimeStarted)).

load_words_usable :-
 consult(words_usable).

load_words :-
 consult(words).

load_word_space_names :-
 consult(word_space_names).

load_word_masks :-
 read_file_to_string("../dataset/word_masks.csv", DataFileString, []),
 split_string(DataFileString, "\n", "", Lines),
 maplist(parse_word_mask_line, Lines).

parse_word_mask_line("").
parse_word_mask_line(Line) :-
 split_string(Line, ",", "", List),
 assert_wordmask(List).


assert_wordmask(List) :-
  nth1(1, List, Mask),
  nth1(2, List, WordIdStr),
  nth1(3, List, CharString),
  atom_number(WordIdStr, WordIdInt),
  split_string(CharString, ";", "", CharList),
  %  print(Mask),write(","),
  % print(WordIdInt),write(","),
  %  print(CharList),nl,
  assertz(word_mask(Mask, WordIdInt, CharList)).

load_crosses :-
 consult(crosses).

load_word_space_fills :-
 consult(word_space_fills).

%! find_and_output_word_space(+WordSpaceName:string, -WordId:integer) is nondet
%% For a WordSpace find a suitable Word and return its id.
find_word_space(WordSpaceName, WordId) :-
    word_space_fill(Mask, Chars, WordSpaceName),
    word_mask(Mask, WordId, Chars),
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
    get_time_started(TimeStarted),
    get_time(TimeLoaded),
    bagof(WordSpaceName, word_space_name(WordSpaceName), WordSpaceNames),
    solve_word_spaces(WordSpaceNames, [], UsedWords),
    %profile(call_with_time_limit(10,     ....   ))
    get_time(TimeEnded),
    LoadTime is TimeLoaded - TimeStarted,
    ComputeTime is TimeEnded - TimeLoaded,
    write("status:found"),nl,
    write("load_time:"),print(LoadTime),nl,
    write("compute_time:"),print(ComputeTime),nl,
    print_word_spaces(WordSpaceNames, UsedWords),
    halt(0).

generate_cross :-
    get_time_started(TimeStarted),
    get_time(TimeLoaded),
    get_time(TimeEnded),
    LoadTime is TimeLoaded - TimeStarted,
    ComputeTime is TimeEnded - TimeLoaded,
    write("status:not_found"),nl,
    write("load_time:"),print(LoadTime),nl,
    write("compute_time:"),print(ComputeTime),nl,
    !, halt(1).