# compose_flask/app.py
from flask import Flask, render_template
from redis import Redis

from rtcbot import RTCConnection, getRTCBotJS

conn = RTCConnection()  # For this example, we use just one global connection

@conn.subscribe
def onMessage(msg):  # Called when messages received from browser
    print("Got message:", msg["data"])
    conn.put_nowait({"data": "pong"})


app = Flask(__name__)
redis = Redis(host='redis', port=6379)

# This sets up the connection
@app.route("/connect", methods = ['POST'])
async def connect(request):
    clientOffer = await request.json()
    serverResponse = await conn.getLocalDescription(clientOffer)
    return web.json_response(serverResponse)


@app.route('/rtcbot.js')
def rtcbotjs(request):
    return getRTCBotJS()

@app.route('/')
def hello():
    return render_template("mockup.html")

async def cleanup(app=None):
    await conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)