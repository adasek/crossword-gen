#!/bin/bash
tail -n +1 input/Czech.dic  | \
 awk '{print tolower($0)}' |\
 cut -d '/' -f 1 |\
 sort -R |\
# head -n 10000 |\
 sed -e 's/;//g' |\
 awk '{printf("%s\n",$1,length($1))}' \
  > wordlist.dat

#-e 's/^\(.*\)$/word('\''\1'\'')./'
