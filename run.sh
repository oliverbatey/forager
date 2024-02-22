#!/bin/bash

# Runs the extract and summarise commands in sequence and automatically
# creates directories to store input and output files.

cwd=$(pwd)
timestamp=$(date +"%Y_%m_%d__%H_%M_%S")
extract_output="${cwd}/extract_output/${timestamp}"
summarise_output="${cwd}/summarise_output/${timestamp}"

if [ ! -d "${extract_output}" ]; then
    mkdir -p "${extract_output}"
fi

if [ ! -d "${summarise_output}" ]; then
    mkdir -p "${summarise_output}"
fi

python reddit_summariser/runner.py extract -o="${extract_output}"
python reddit_summariser/runner.py summarise -i="${extract_output}" -o="${summarise_output}"
