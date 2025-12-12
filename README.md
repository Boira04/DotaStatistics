# Steps to follow
## First we need to create the containers
docker compose up -d

## Then we have to install  the requirements
python -m pip install -r requirements.txt

## After that we execute this python file in order to save the raw data in MongoDB
python etl/main_etl.py