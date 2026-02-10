#!/bin/bash

# Kill processes using ports 8000 and 8081
echo "Killing processes using ports 8000 and 8081..."
for port in 8000 8081; do
    PIDS=$(lsof -ti :$port)
    if [ -n "$PIDS" ]; then
        echo "Killing process(es) using port $port: $PIDS"
        kill -9 $PIDS
    else
        echo "No processes using port $port"
    fi
done

