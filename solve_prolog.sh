#!/bin/bash
cd dataset
if prolog ../solve.pl
then
 echo "Solution found" >&2
else
 echo "No solution" >&2 
fi
