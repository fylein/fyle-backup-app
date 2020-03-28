# fyle-backup-app
Multi-tenant self serve application to take backup of Fyle data

### Development setup

1. Fyle App registration (get your client_id and client_secret here)
    1. Login to [Fyle](https://app.fyle.in)
    2. Goto settings and click on Developers
    3. Click on create new app, enter the details and select type as OAuth 2.0
    4. For Redirect URI enter 
        1. 'http://localhost:8000/main/callback/' for development
        2. 'https://your_domain/main/callback/' for production
        3. 'http://localhost:8000/accounts/fyle/login/callback/' for development
        4. 'https://your_domain/accounts/fyle/login/callback/' for production
    5. Note down the client_secret and client_id

2. Install the project dependencies by running `pip install -r requirements.txt`in a python environment of your choice
    1. If you face an error related to mysql_config follow the steps in [this](https://stackoverflow.com/questions/7475223/mysql-config-not-found-when-installing-mysqldb-python-interface) article
3. Rename the file ```.env.template``` to ```.env``` and customize it accordingly
4. Run ```python manage.py migrate``` to populate your database
5. Run ```python manage.py createsuperuser``` and follow the instructions to create a superuser 
6. Open django-admin and create a new record under Social Applications. Select Fyle as provider and enter your client_secret and client_id. Add our site to the Chosen sites on the bottom.
7. Run ```python manage.py runserver``` to start the server on localhost
8. You might want to comment out the FyleJobs section (```apps/backups/views.py```) during development 


Visit [http://localhost:8000](http://localhost:8000) to access the application

