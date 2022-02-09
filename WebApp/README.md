To test this, you need to install [Flask](https://flask.palletsprojects.com/en/2.0.x/) and [Celery with redis](https://docs.celeryproject.org/en/stable/getting-started/introduction.html#installation):

    pip install "celery[redis]"

Then, run the following commands (in the folder where `wsgi.py` is located) on **two different** bash shells:

    python wsgi.py

and

    celery -A wsgi.celery worker

Then, you should connect to http://127.0.0.1:5000/