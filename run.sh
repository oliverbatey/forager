#!/bin/bash

# Runs the extract, summarise and publish commands in sequence.
# Automatically creates directories to store input and output data.

cwd=$(pwd)
timestamp=$(date +"%Y_%m_%d__%H_%M_%S")
extract_output="${cwd}/extract_output/${timestamp}"
summarise_output="${cwd}/summarise_output/${timestamp}"
publish_output="${cwd}/publish_output/${timestamp}"

if [ ! -d "${extract_output}" ]; then
    mkdir -p "${extract_output}"
fi

python reddit_summariser/runner.py extract -o="${extract_output}"

if [ ! -d "${summarise_output}" ]; then
    mkdir -p "${summarise_output}"
fi

python reddit_summariser/runner.py summarise -i="${extract_output}" -o="${summarise_output}"

if [ ! -d "${publish_output}" ]; then
    mkdir -p "${publish_output}"
fi

python reddit_summariser/runner.py publish -i="${summarise_output}" -o="${publish_output}"
