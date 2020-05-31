#!/bin/bash
cp solve.pl prolog_output/
cd prolog_output
if prolog solve.pl
then
 echo "Solution found" >&2
else
 echo "No solution" >&2 
fi
