:- initialization mark_start_time, load_words, load_words_usable, load_word_spaces  , load_word_masks, load_crosses, generate_cross.

:- set_prolog_flag(double_quotes, atom).

mark_start_time :-
 get_time(TimeStarted),
 assertz(get_time_started(TimeStarted)).

load_words_usable :-
 consult(words_usable).

load_words :-
 consult(words).

load_word_spaces :-
 consult(word_spaces).


load_word_masks :-
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
 consult(crosses).

%%%%%
solve_cross(DataIn, CrossId, Char, FoundWord1, FoundWord2, DataOutter) :-
 cross(WS1, MaskWS1, WS2, MaskWS2, CrossId),
 %write("solve_cross/WS1:"),print(WS1),nl,
 %write("solve_cross/DataIn:"),print(DataIn),nl,
 word_space_fill_one(DataIn, MaskWS1, Char, WS1, FoundWord1, DataOut),
 %write("solve_cross/WS2:"),print(WS2),nl,
 %write("solve_cross/MaskWS2:"),print(MaskWS2),nl,
 %write("solve_cross/Char:"),print(Char),nl,
 %write("solve_cross/DataOut:"),print(DataOut),nl,
 word_space_fill_one(DataOut, MaskWS2, Char, WS2, FoundWord2, DataOutter).


word_space_fill_one(DataIn, Mask, Char, WordSpaceId, WordId, DataOut) :-
 find_mask(DataIn, WordSpaceId, OldMask, OldChars),
 combine_masks(Mask, [Char], OldMask, OldChars, NewMask, NewChars),
 word_mask(NewMask, WordId, NewChars),
 bind_crosses(WordSpaceId, WordId),
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

combine_mask_lists(["."|Mask1List], Chars1, ["."|Mask2List], Chars2, ["."|NewMaskList], NewChars) :-
    combine_mask_lists(Mask1List, Chars1, Mask2List, Chars2, NewMaskList, NewChars).


update_mask(DataIn, WordSpaceId, NewMask, NewChars, DataOut) :-
    %write("update_mask WordSpaceId="),print(WordSpaceId),nl,
    %write("update_mask NewMask="),print(NewMask),nl,
    put_dict(WordSpaceId, DataIn, _{mask: NewMask, chars: NewChars} , DataOut).


bind_crosses(WordSpaceId, WordId) :-
    word_space(WordSpaceId,_,CrossesList),
    word(WordId,WordString),
    split_string(WordString, "", "", CharList),
    bind_crosses_list(WordSpaceId,CrossesList,CharList).

bind_crosses_list(_, [],[]).
bind_crosses_list(_, [CrossId|CrossListRest],[Char|CharListRest]):-
 string_length(CrossId,Len),
 =(Len, 0)
 bind_crosses_list(_, CrossListRest, CharListRest).

bind_crosses_list(WordSpaceId, [CrossId|CrossListRest],[Char|CharListRest]) :-
 cross(WS1,Mask1,WS2,Mask2,CrossId),
 =(WS1, WordSpaceId),
 %WS 2 is the unbounded one

 cross("WS_3","..X.","WS_7","..X.","C_4_4").



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
    write("solve_crosses0:"),print(CrossId),nl,
    write(DataIn),nl,
    solve_cross(DataIn, CrossId, _, FoundWord1, FoundWord2, DataOut),
    not_in_used_words(FoundWord1, UsedWordsBefore),
    not_in_used_words(FoundWord2, [FoundWord1|UsedWordsBefore]),
    sleep(0.1),
    word(FoundWord1, FoundWord1String),
    word(FoundWord2, FoundWord2String),
    write(" FoundWord1:"),print(FoundWord1String),nl,
    write(" FoundWord2:"),print(FoundWord2String),nl,
    append(UsedWordsBefore, [FoundWord1], UsedWordsA),
    append(UsedWordsA, [FoundWord2], UsedWordsB),
    write("solve_crosses1:"),print(CrossId),nl,
    solve_crosses(DataOut, Rest, UsedWordsB, UsedWords, DataBack).


initialize_word_masks(OutDict, [], OutDict).
initialize_word_masks(InDict, [WordSpaceId|WordSpaceList], OutDict) :-
 word_space(WordSpaceId, WordLength, _),
 empty_mask(WordLength, Mask),
 put_dict(WordSpaceId, InDict, _{mask: Mask, chars: []}, Dict),
 initialize_word_masks(Dict, WordSpaceList, OutDict).

empty_mask(Length, "") :- =(Length, 0).
empty_mask(Length, OutStr) :-
LenDec is Length - 1,
>(Length, 0),
empty_mask(LenDec, InStr),
string_concat(".", InStr, OutStr).

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
    findall(WordSpaceId, word_space(WordSpaceId, _, _), WordSpaceIds),
    initialize_word_masks(_{}, WordSpaceIds ,WordMasks),
    findall(CrossId, cross(_, _, _, _, CrossId), CrossIds),
    print(CrossIds),nl,
    solve_crosses(WordMasks, CrossIds, [], UsedWords, _),
    print(UsedWords),nl,
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