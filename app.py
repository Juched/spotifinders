# compose_flask/app.py
from flask import Flask
from redis import Redis

app = Flask(__name__)
redis = Redis(host='redis', port=6379)

@app.route('/')
def hello():
    redis.incr('hits')
    return f"This Compose/Flask demo has been viewed {int(redis.get('hits'))} time(s)."

@app.route('/test')
def testing():
    e = redis.client_getname()
    return "hillo" + str(e)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)