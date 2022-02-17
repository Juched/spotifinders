# compose_flask/app.py
from flask import Flask, render_template, session, request, redirect
from spotipy.oauth2 import SpotifyClientCredentials


import time
import os
import uuid

import spotipy
from flask_session import Session
from flask_sock import Sock

from nlp_model import SpotifinderModel

app = Flask(__name__)
sock = Sock(app)

app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

SPOTIPY_CLIENT_ID = os.environ['SPOTIPY_CLIENT_ID']
SPOTIPY_CLIENT_SECRET = os.environ['SPOTIPY_CLIENT_SECRET']
SPOTIPY_REDIRECT_URI = os.environ['SPOTIPY_REDIRECT_URI']

caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)

def session_cache_path():
    return caches_folder + session.get('uuid')


USERDICT = {}
# curernt time set to 0 for a session until the player starts to play
CURRENT_TIME = {}
# update the song playing every 15 seconds
UPDATE_SONG_TIME_MS = 15 * 1000

# @app.route('/')
# def index():
#     return render_template('index.html')

@app.route('/')
def log():
    if not session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())

    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope='user-library-read playlist-read-private user-top-read user-read-currently-playing user-read-playback-state streaming',
                                                cache_handler=cache_handler, 
                                                show_dialog=True)

    if request.args.get("code"):
        # Step 3. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 2. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return render_template("index.html", auth_url=auth_url)
        #return f'<h2><a href="{auth_url}">Sign in</a></h2>'

    # Step 4. Signed in, display data
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    USERDICT[session.get('uuid')] = spotify
    # curernt time set to 0 until the player starts to play
    CURRENT_TIME[session.get('uuid')] = 0

    u_data = spotify.me()

    prof_pic_url = u_data['images'][0]['url']

    return render_template("loggedin.html",purl=prof_pic_url, pname=u_data['display_name'])



@sock.route('/echo')
def echo(sock):
    model = SpotifinderModel()
    while True:
        data = sock.receive()
        feature_dict = model.get_vector(data)
        player(feature_dict)
        sock.send(data)


def player(audioFeatures):
    # get black box list of audio features :)
    # danceability, valence, energy dictionary
    
    # standard
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    localSP = spotipy.Spotify(auth_manager=auth_manager)
    # return spotify.current_user_playlists()

    # prev_time = CURRENT_TIME[session]
    # CURRENT_TIME[session] = time.perf_counter()

    thing = localSP.current_playback()

    # play a new song if the timer allows it
    # if CURRENT_TIME[session.get('uuid')] - prev_time >=  UPDATE_SONG_TIME_SECONDS:
    if localSP.current_playback() == None or localSP.current_playback()['progress_ms'] >= UPDATE_SONG_TIME_MS:
        # localSP  = USERDICT[session.get('uuid')] 
        songs = localSP.recommendations(seed_genres= ['rock', 'pop', 'alternative', 'indie', 'rap'], #localSP.recommendation_genre_seeds(),  #'alternative', #, pop, alternative, indie', # just general stuff for now
            target_danceability=audioFeatures['danceability'], 
            target_energy=audioFeatures['energy'], 
            target_valence=audioFeatures['valence']
            )


        # headers = {
        #     'Authorization': 'Bearer {token}'.format(token=access_token)
        # }
        # adds new suggest song to queue
        thing = songs['tracks'][0]['id']
        localSP.add_to_queue(thing)
        if localSP.current_playback() != None: #currently_playing() != None: # DOESN'T RETURN BOOL, BUT NOONE WILL TELL ME WHAT IT DOES RETURN AND I CANT TEST YET
            localSP.next_track()
        else:
            localSP.start_playback()

    return thing


@app.route('/testplayer')
def test():
    audioFeatures = {}
    audioFeatures['danceability'] = .88
    audioFeatures['energy'] = .9
    audioFeatures['valence'] = .9


    return str(player(audioFeatures))


@app.route('/sign_out')
def sign_out():
    try:
        # Remove the CACHE file (.cache-test) so that a new user can authorize.
        os.remove(session_cache_path())
        session.clear()
    except OSError as e:
        print ("Error: %s - %s." % (e.filename, e.strerror))
    return redirect('/')

@app.route('/currently_playing')
def currently_playing():
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    track = spotify.current_user_playing_track()
    if not track is None:
        return track
    return "No track currently playing."

@app.route('/start_playing',methods=["POST"])
def start_playing():
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    # track = spotify.current_user_playing_track()
    spotify.start_playback(uris=['spotify:track:6AjOUvtWc4h6MY9qEcPMR7'])

    # return redirect('/')


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
