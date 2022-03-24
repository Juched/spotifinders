"""App module."""
# compose_flask/app.py
from threading import local
from tkinter import E
from flask import Flask, render_template, session, request, redirect
from spotipy.oauth2 import SpotifyClientCredentials


import time
import os
import uuid
import random
import numpy as np
import json

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

SPOTIPY_OATH_SCOPE = ('user-library-read playlist-read-private user-top-read '
                    'user-read-currently-playing user-read-playback-state streaming '
                    'user-modify-playback-state'
                    )

SEED_GENRES = ['rock', 'pop', 'alternative', 'indie', 'rap']

CACHES_FOLDER = './.spotify_caches/'
if not os.path.exists(CACHES_FOLDER):
    os.makedirs(CACHES_FOLDER)

def session_cache_path():
    """ sets up the session cache """
    return CACHES_FOLDER + session.get('uuid')


# update the song playing every 15 seconds
UPDATE_SONG_TIME_MS = 15 * 1000

# @app.route('/')
# def index():
#     return render_template('index.html')

@app.before_request
def before_request():
    """ code to execute prior """
    if 'localhost' not in SPOTIPY_REDIRECT_URI:
        scheme = request.headers.get('X-Forwarded-Proto')
        if scheme and scheme is 'http' and request.url.startswith('http://'):
            url = request.url.replace('http://', 'https://', 1)
            code = 301
            return redirect(url, code=code)
    else:
        return


@app.route('/')
def log():
    if not session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())

    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope=SPOTIPY_OATH_SCOPE,
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

    # USERDICT[session.get('uuid')] = spotify
    # # curernt time set to 0 until the player starts to play
    # CURRENT_TIME[session.get('uuid')] = 0

    u_data = spotify.me()

    prof_pic_url = u_data['images'][0]['url']

    u_playlists = playlists(spotify)

    return render_template("loggedin.html", \
                            purl=prof_pic_url, \
                            pname=u_data['display_name'], \
                            user_playlists=u_playlists) \
                            #map(json.dumps, uPlaylists))


# called once for each thread
@sock.route('/echo')
def echo(sock):
    """ websocket route to get the speech to throw in the model and then update a song """
    model = SpotifinderModel()
    while True:
        data = json.loads(sock.receive())
        print(data)
        feature_dict = model.get_vector(data["text"])

        queue_from_playlist(feature_dict, data)
        print(feature_dict)
        # print(data)
        sock.send(feature_dict)

# gets the Spotipy obj
def get_spotipy():
    """ Retreives the current users spotipy object, which contains the spotify info as well """
    try:

        # standard
        cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
        auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
        if not auth_manager.validate_token(cache_handler.get_cached_token()):
            # return redirect('/')
            raise Exception('Was unable to connct to your spotify account')

        return spotipy.Spotify(auth_manager=auth_manager)

    except Exception as e:
        print (f"Error: {e}")
    return None

# using spotipy to get a close match
def discover_song(audio_features):
    """ discovers a song from spotify """
    # get black box list of audio features :)
    # danceability, valence, energy dictionary
    thing = ''
    print('discovery mode!')
    try:

        # standard    
        spotipy = get_spotipy()
        # return spotify.current_user_playlists()


        # play a new song if the timer allows it
        if spotipy is not  None and (spotipy.current_playback() is None or \
            spotipy.current_playback()['progress_ms'] >= UPDATE_SONG_TIME_MS):

            #localSP.recommendation_genre_seeds(),  #'alternative', #, pop, alternative, indie'
            songs = spotipy.recommendations(
                seed_genres = ['rock', 'pop', 'alternative', 'indie', 'rap'],
                target_danceability=audio_features['danceability'],
                target_energy=audio_features['energy'],
                target_valence=audio_features['valence']
                )

            # adds new suggest song to queue
            thing = songs['tracks'][0]['id']
            spotipy.add_to_queue(thing)

            # DOESN'T RETURN BOOL, BUT NOONE WILL TELL ME WHAT IT DOES RETURN AND I CANT TEST YET
            #currently_playing() != None:
            if spotipy.current_playback() != None:
                spotipy.next_track()
            else:
                spotipy.start_playback()

    except Exception as ex:
        print (f"Error: {ex}")

    return thing


def find_closest_match(ideal_features, playlist_features):
    """ from a list of songs features, and the ideal features, function will return the clostest song to the ideal """
    implemented_features = ideal_features.keys()
    ideal_vector = []
    min_norm = None
    ideal_id = None

    try:

        for feature in implemented_features:
            ideal_vector.append(ideal_features[feature])
        ideal_vector = np.array(ideal_vector)

        for single_track in playlist_features:
            current_vector = []
            for feature in implemented_features:
                current_vector.append(single_track[feature])
            # we have the curernt audio feature vector at this point

            current_min = np.linalg.norm(np.array(current_vector) - ideal_vector)
            if ideal_id is None or min_norm is None or current_min < min_norm:
                min_norm = current_min
                ideal_id = single_track['id']
                print(ideal_id)

    except Exception as ex:
        print (f"Error: {ex}")

    return ideal_id # some track id

#Method that starts play
def queue_from_playlist(ideal_audio_features, data):
    """ queues a song based on the ideal audio features """
    playlist_id = data["playlistID"]

    if (playlist_id is "discover_mode" or
        playlist_id is 1 or
        playlist_id is "liked_songs" or
        playlist_id is "1"):
        # In the case this is a new playlist, we don't need to recommend anything
        # (as of right now). Just transfer playback
        discover_song(ideal_audio_features)
        return

    local_spotipy = get_spotipy()
    audio_features = None

    if (local_spotipy is not None and (local_spotipy.current_playback() is None or
        local_spotipy.current_playback()['progress_ms'] >= UPDATE_SONG_TIME_MS)):
        # get the songs from the playlist
        # tracks = localSP.playlist(playlistID, fields="tracks,next")
        tracks = local_spotipy.playlist(playlist_id)
        # print('Custom playlist!')

        # print(tracks)
        trackIDs = []

        for (song, i) in zip(tracks["tracks"]["items"], range(100)):
            if song != None:
                trackIDs.append(song['track']['uri'])

        print(trackIDs)
        # get the audio features
        audio_features = local_spotipy.audio_features(tracks=trackIDs)

        # print('got audio features! print here:')
        # print(audioFeatures)
        # find the closest match
        coolSong = find_closest_match(ideal_audio_features, audio_features)
        # add to queue
        if coolSong != None:
            local_spotipy.add_to_queue(coolSong)

            #currently_playing() != None:
            # DOESN'T RETURN BOOL, BUT NOONE WILL TELL ME WHAT IT DOES RETURN AND I CANT TEST YET
            if local_spotipy.current_playback() != None:
                local_spotipy.next_track()
            else:
                local_spotipy.start_playback()

    return audio_features

# gets the playlists name and IDs and returns them (easily replaceable for URIs too)
def playlists(spotipy_manager=None):
    """ gets the playlists name and IDs and returns them (easily replaceable for URIs too) """
    spotipy = spotipy_manager if spotipy_manager is not None else get_spotipy()
    local_playlists = None
    playlists = {}

    if spotipy is not None:
        local_playlists = spotipy.current_user_playlists()

        if "items" in local_playlists:
            for p in local_playlists["items"]:
                playlists[p["id"]] = p["name"]

    return playlists

# def pickTrackFromPlaylist() # take in track ID, if empty/None, use liked songs playlist.
# This websocket is responsible for sending the auth token to the fronend in order to initialize
# a webplayer. See static/web_player.js
@sock.route('/webPlayer')
def spotifyWebPlayer(sock):
    """ 
        This websocket is responsible for sending the auth token to the fronend in order to initialize 
        a webplayer. See static/web_player.js 
    """
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    token = auth_manager.get_access_token()
    sock.send(token['access_token'])
    # sock.close()

# This websocket is used to first switch over Spotify to the Spotifinders Web API Device.
# This is what "Turns on" Our webplayer.
# This websocket is called FIRST when the server first loads
# and THEN every time the user selects a playlist.
@sock.route('/deviceID')
def deviceListener(sock):
    """
        This websocket is used to first switch over Spotify to the Spotifinders Web API Device.
        This is what "Turns on" Our webplayer.
        This websocket is called FIRST when the server first loads
        and THEN every time the user selects a playlist.
    """
    try:

        cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
        auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
        if not auth_manager.validate_token(cache_handler.get_cached_token()):
            return redirect('/')
        spotify = spotipy.Spotify(auth_manager=auth_manager)

        data = json.loads(sock.receive())
        print(f"Transferring playback to device {data['device_id']}")

        spotify.transfer_playback(device_id=data['device_id'])

        while True:
            data = json.loads(sock.receive())
            playlist_id = data['playlist_id']
            is_custom = data['isCustomUserPlaylist']


            if playlist_id is "discover_mode":
                rec_songs_arr = spotify.recommendations(seed_genres = SEED_GENRES)['tracks']
                rec_uris = [song['uri'] for song in rec_songs_arr]
                spotify.start_playback(device_id=data['device_id'], uris=rec_uris)

            elif playlist_id is "liked_songs":
                #this array is a bunch of liked songs.
                #arrray of {added at: , track: } objecats
                #track is {artists... album... uri...}

                # TO DO: Research liked song limitation. CAn only retrieve 50!
                liked_songs_arr = spotify.current_user_saved_tracks(limit=50)["items"]

                # TO DO: See if we should sample more than 20 liked songs. Research what this does.
                sampled_liked_songs = random.sample(liked_songs_arr, 20)

                random_liked_song_uris = [song['track']['uri'] for song in sampled_liked_songs]
                spotify.start_playback(device_id=data['device_id'], uris=random_liked_song_uris)
            elif is_custom:
                print(f"Custom playlist recieved: {playlist_id} ")
                selected_playlist = spotify.playlist(playlist_id)
                spotify.start_playback(device_id=data['device_id'],
                                        context_uri=selected_playlist['uri'])
            else:
                print(f"Unknown variant of PlaylistID: {playlist_id}, \nThis should never happen!")

        #play from liked playlists

        #immediate pause

        # this should work but I am getting 403 errors when I have commeted out...
        savedTracks = spotify.current_user_saved_tracks()["items"]
        firstSong = savedTracks[random.randint(0,len(savedTracks)-1)]["track"]
        spotify.add_to_queue(firstSong["id"]) # queueFromPlaylist)

        # spotify.start_playback(device_id=device_id,uris=['spotify:track:6AjOUvtWc4h6MY9qEcPMR7'])
        # Ideally, we start playing a song depending on what they want

    except Exception as ex:
        print (f"Error: {ex}")

    return

def start_play(tracks_array, spotify):
    """ starts the playback of a random song """
    song = tracks_array[random.randint(0,len(tracks_array)-1)]


@app.route('/testplayer')
def test():
    """ just a useful test route for testing purposes """
    audio_features = {}
    audio_features['danceability'] = .88
    audio_features['energy'] = .9
    audio_features['valence'] = .9

    playlist_id = '37i9dQZF1EUMDoJuT8yJsl'

    # return str(player(audioFeatures))
    return str(queue_from_playlist(audio_features, playlist_id))


@app.route('/sign_out')
def sign_out():
    """ sign out logic """
    try:
        # Remove the CACHE file (.cache-test) so that a new user can authorize.
        os.remove(session_cache_path())
        session.clear()
    except OSError as e:
        print ("Error: %s - %s." % (e.filename, e.strerror))
    return redirect('/')

@app.route('/currently_playing')
def currently_playing():
    """ returns what is currently playing for the user """
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
    """ post method to start the playing of a song """
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    # track = spotify.current_user_playing_track()
    spotify.start_playback(uris=['spotify:track:6AjOUvtWc4h6MY9qEcPMR7'])

    return "Playing"


if __name__ is "__main__":
    """ main """
    app.run(host="0.0.0.0", debug=True)
