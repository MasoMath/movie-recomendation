#!/usr/bin/env bash

cd backend && flask --app server.py --debug run &
BACK_PID=$!


cd frontend && npm run dev &
FRONT_PID=$!

wait $BACK_PID $FRONT_PID
echo "finished launching frontend and backend"
