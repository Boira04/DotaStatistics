# Run the project IN WINDOWS

## Requirements
- Docker
- Docker Compose

## Start everything
docker compose up -d --build

### Open a second terminal, enter in the frontend folder and execute the command below
python -m http.server 3000

### After that in the browser open a tab with the following port
http://localhost:3000

## Now you should be able to see our webpage!

## Extra things
### Services
- API: http://127.0.0.1:8000/docs#
- Mongo Express: http://localhost:8081
  - user: admin
  - password: password123

## One last thing
## How to create an admin user in order to see the admin panel
### You have to register as normal in  http://localhost:3000
### After you have to open the Mongo Express, put the user and password, and change manually the role (from user to admin)
### Once done that, refresh, enter again in the web and look if you're able to see the Admin Button

## NOTE if you're in ubuntu and the command below doesn't work
python -m http.server 3000
## Try doing the following:
python3 -m http.server 3000