:- initialization mark_start_time, load_words, load_words_usable, load_word_space_names, load_word_masks, load_crosses, generate_cross.

:- set_prolog_flag(double_quotes, atom).

mark_start_time :-
 get_time(TimeStarted),
 assertz(get_time_started(TimeStarted)).

load_words_usable :-
 print("load_words_usable"),nl,
 consult(words_usable).

load_words :-
 print("load_words"),nl,
 consult(words).

load_word_space_names :-
 print("load_word_space_names"),nl,
 consult(word_space_names).

load_word_masks :-
 print("load_word_masks"),nl,
 read_file_to_string("../dataset/word_masks.csv", DataFileString, []),
 split_string(DataFileString, "\n", "", Lines),
 maplist(parse_word_mask_line, Lines).

parse_word_mask_line(Str) :-
 string_length(Str,Len),
 =(Len, 0).

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
 print("load_crosses"),nl,
 consult(crosses).

%%%%%
solve_cross(DataIn, CrossId, Char, FoundWord1, FoundWord2, DataOut) :-
 cross(WS1, MaskWS1, WS2, MaskWS2, CrossId),
 word_space_fill_one(DataIn, MaskWS1, Char, WS1, FoundWord1, DataOut),
 word_space_fill_one(DataIn, MaskWS2, Char, WS2, FoundWord2, DataOut).


word_space_fill_one(DataIn, Mask, Char, WordSpaceId, WordId, DataOut) :-
 find_mask(DataIn, WordSpaceId, OldMask, OldChars),
 combine_masks(Mask, [Char], OldMask, OldChars, NewMask, NewChars),
 word_mask(NewMask, WordId, NewChars),
 update_mask(DataIn, WordSpaceId, NewMask, NewChars, DataOut).

find_mask(Data, WordSpaceId, Mask, Chars) :-
    get_dict(WordSpaceId, Data, Record),
    get_dict(mask, Record, Mask),
    get_dict(chars, Record, Chars).

combine_masks(Mask1, Chars1, Mask2, Chars2, NewMask, NewChars) :-
    string_chars(Mask1, Mask1List),
    string_chars(Mask2, Mask2List),
    combine_mask_lists(Mask1List, Chars1, Mask2List, Chars2, NewMaskList, NewChars),
    atomics_to_string(NewMaskList, NewMask).

combine_mask_lists([], [], [], [], [], []).

combine_mask_lists(["X"|Mask1List], [C|Chars1], ["."|Mask2List], Chars2, ["X"|NewMaskList], [C|NewChars]) :-
    combine_mask_lists(Mask1List, Chars1, Mask2List, Chars2, NewMaskList, NewChars).

combine_mask_lists(["."|Mask1List], Chars1, ["X"|Mask2List], [C|Chars2], ["X"|NewMaskList], [C|NewChars]) :-
    combine_mask_lists(Mask1List, Chars1, Mask2List, Chars2, NewMaskList, NewChars).

combine_mask_lists(["."|Mask1List], Chars1, ["."|Mask2List], Chars2, ["X"|NewMaskList], NewChars) :-
    combine_mask_lists(Mask1List, Chars1, Mask2List, Chars2, NewMaskList, NewChars).



update_mask(DataIn, WordSpaceId, NewMask, NewChars, DataOut) :-
    print(WordSpaceId),
    put_dict(WordSpaceId, DataIn, _{test: _{mask: NewMask, chars: NewChars} }, DataOut).
%%%%%%%%%%%

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

%! solve_crosses(+CrossNames:list, +UsedWordsBefore:list, -UsedWords:list) is nondet
%% Recursively call search for suitable word for every WordSpace given in first parameter
%% After match is made, remove the word from usable words
solve_crosses(Data,[],X,X,Data).
solve_crosses(DataIn, [CrossId | Rest], UsedWordsBefore, UsedWords, DataBack) :-
    print("solve_crosses"),nl,
    solve_cross(DataIn, CrossId, _, FoundWord1, FoundWord2, DataOut),
    not_in_used_words(FoundWord1, UsedWordsBefore),
    not_in_used_words(FoundWord2, UsedWordsBefore),
    solve_crosses(DataOut, Rest, [FoundWord2|[FoundWord1|UsedWordsBefore]], UsedWords, DataBack).

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
    write("ABC"),nl,
    get_time_started(TimeStarted),
    get_time(TimeLoaded),
    print("CrossIds:"),nl,
    bagof(CrossId, cross(_, _, _, _, CrossId), CrossNames),
    solve_crosses(_{}, CrossNames, [], UsedWords, _),
    print(UsedWords),
    %profile(call_with_time_limit(10,     ....   ))
    get_time(TimeEnded),
    LoadTime is TimeLoaded - TimeStarted,
    ComputeTime is TimeEnded - TimeLoaded,
    write("status:found"),nl,
    write("load_time:"),print(LoadTime),nl,
    write("compute_time:"),print(ComputeTime),nl,
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