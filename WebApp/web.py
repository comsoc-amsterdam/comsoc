#!/usr/bin/python

from flask import Flask, request, render_template, url_for
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buildprofile', methods=["POST"])
def buildprofile():
    return render_template('buildprofile.html', candidates = list(request.form.values()))

@app.route('/result', methods=["POST"])
def result():
    return request.form["profile"]

if __name__ == '__main__':
    ip, port = '127.0.0.1', 5004
    print(f"Go to http://{ip}:{port}/")
    socketio.run(app, host=ip, port=port)