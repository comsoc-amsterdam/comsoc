# Running the Demo Locally

## Installation

First, make sure to install all the Python dependencies, `graphviz`, and to compile MARCO. To do so, see the installation instructions in `../README.md`.

## Running the demo

Then, run the following commands (in the folder where `wsgi.py` is located) on **two different** shells:

    python wsgi.py

and

    celery -A wsgi.celery worker --pool=solo --loglevel=INFO

Then, the demo will be available locally at [http://127.0.0.1:5000/].

## Troubleshooting

If you get an error message saying "Error 111 connecting to localhost:6379. Connection refused.", you might have to install `redis-server`. How to do so might depend on your system.

On Ubuntu:

    sudo apt-get install redis-server

On Arch linux:

    sudo pacman -S valkey
    sudo systemctl enable --now redis.service
