#!/usr/bin/env bash


#this probably will not work on Windows. If the only thing 
#stopping it from working on Windows is 'python3', change
#it for yourself to 'python' or 'py', since that is what
# (I think) is the executable for python on Windows
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi


source venv/bin/activate
pip install -r requirements.txt

if [ ! -d "kaggledata" ]; then
  python grab_data.py
fi


cd backend && flask --app server.py --debug run &
BACK_PID=$!


cd frontend && npm install &&  npm run dev &
FRONT_PID=$!

wait $BACK_PID $FRONT_PID
echo "finished launching frontend and backend"
