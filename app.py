# compose_flask/app.py
from flask import Flask, render_template

from flask_sock import Sock
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

app = Flask(__name__)
sock = Sock(app)

@app.route('/')
def index():
    return render_template('index.html')


@sock.route('/echo')
def echo(sock):
    while True:
        data = sock.receive()
        sock.send(data)


@app.route('/player')
def player():
    return f""


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)