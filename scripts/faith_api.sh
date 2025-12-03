#!/bin/bash
export HF_ENDPOINT=https://hf-mirror.com

# define log dir
OUT=${1:-"faith_api.log"}

# start server
nohup python -u faith_api.py  > $OUT 2>&1 &
   echo "faith_api started, output is being logged to $OUT"
   echo "To stop the server, use 'pkill -f faith_api.py'"
   echo "You can check the logs in $OUT"
   # disown the process so it continues running after the terminal is closed
   disown