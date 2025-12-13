# Steps to follow on Windows
## First we need to create the containers
docker compose up -d

## Then we have to install  the requirements
python -m pip install -r requirements.txt

## After that we execute this python file in order to save the raw data in MongoDB
python etl/main_etl.py

## Once executed the command before, now you'll be able to see the data stored in MongoDB just using the following port and going to dota_project
### Port used:
http://localhost:8081/db/dota_project/
### User:
admin
### Password:
password123

## After we execute this command in order to execute the FastAPI server
py -m uvicorn backend.main:app
### Or if you have stopped it and you want to execute it again
py -m uvicorn backend.main:app --reload

## You will be able to see the json in
 http://127.0.0.1:8000/ONE_OF_THE_FIVE_ENDPOINTS
 ### Example
 http://127.0.0.1:8000/analytics/insights/market-gaps