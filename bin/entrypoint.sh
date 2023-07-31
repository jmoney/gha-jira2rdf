#!/bin/sh

python3 /app/main.py --jira-server $1 --username $2 --max-results $3 --jql $4 > $5