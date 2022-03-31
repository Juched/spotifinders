"""App module."""
# compose_flask/app.py
# from threading import local
# from tkinter import E

# import scipy as sp
# import time


import os
import uuid
import random
import string
import json

import requests
import numpy as np


from flask import Flask, render_template, session, request, redirect

# from spotipy.oauth2 import SpotifyClientCredentials

import spotipy
from flask_session import Session
from flask_sock import Sock


app = Flask(__name__)
sock = Sock(app)
# model = BERTModel()

app.config["SECRET_KEY"] = os.urandom(64)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./.flask_session/"
Session(app)

SPOTIPY_CLIENT_ID = os.environ["SPOTIPY_CLIENT_ID"]
SPOTIPY_CLIENT_SECRET = os.environ["SPOTIPY_CLIENT_SECRET"]
SPOTIPY_REDIRECT_URI = os.environ["SPOTIPY_REDIRECT_URI"]

SPOTIPY_OATH_SCOPE = (
    "user-library-read playlist-read-private user-top-read "
    "user-read-currently-playing user-read-playback-state streaming "
    "user-modify-playback-state"
)

SEED_GENRES = ["rock", "pop", "alternative", "indie", "rap"]

CACHES_FOLDER = "./.spotify_caches/"
if not os.path.exists(CACHES_FOLDER):
    os.makedirs(CACHES_FOLDER)


def session_cache_path():
    """sets up the session cache"""
    return CACHES_FOLDER + session.get("uuid")


# update the song playing every 15 seconds
UPDATE_SONG_TIME_MS = 15 * 1000

# @app.route('/')
# def index():
#     return render_template('index.html')


@app.before_request
def before_request():
    """code to execute prior"""
    if "localhost" not in SPOTIPY_REDIRECT_URI:
        scheme = request.headers.get("X-Forwarded-Proto")
        if scheme and scheme == "http" and request.url.startswith("http://"):
            url = request.url.replace("http://", "https://", 1)
            code = 301
            return redirect(url, code=code)
    else:
        return


@app.route("/")
def log():
    """log in function"""
    if not session.get("uuid"):
        # Step 1. Visitor is unknown, give random ID
        session["uuid"] = str(uuid.uuid4())

    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path()
    )
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        scope=SPOTIPY_OATH_SCOPE, cache_handler=cache_handler, show_dialog=True
    )

    if request.args.get("code"):
        # Step 3. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect("/")

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 2. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return render_template("index.html", auth_url=auth_url)
        # return f'<h2><a href="{auth_url}">Sign in</a></h2>'

    # Step 4. Signed in, display data
    local_spotify = spotipy.Spotify(auth_manager=auth_manager)

    # USERDICT[session.get('uuid')] = spotify
    # # curernt time set to 0 until the player starts to play
    # CURRENT_TIME[session.get('uuid')] = 0

    u_data = local_spotify.me()

    prof_pic_url = u_data["images"][0]["url"]

    u_playlists = playlists(local_spotify)

    return render_template(
        "loggedin.html",
        purl=prof_pic_url,
        pname=u_data["display_name"],
        user_playlists=u_playlists,
    )  # map(json.dumps, uPlaylists))


def get_model_data(text: string):
    """Gets feature dictionary from NLP model"""
    req = requests.post(
        "http://bert:5000/api/v1/bert",
        json={"text": text},
    )
    return req.json()["vector"]


# called once for each thread
@sock.route("/echo")
def echo(socket):
    """websocket route to get the speech to throw in the model and then update a song"""

    while True:
        data = json.loads(socket.receive())

        feature_dict = get_model_data(data["text"])

        next_song(feature_dict, data)

        socket.send(feature_dict)


# gets the Spotipy obj
def get_spotipy():
    """Retreives the current users spotipy object, which contains the spotify info as well"""
    try:

        # standard
        cache_handler = spotipy.cache_handler.CacheFileHandler(
            cache_path=session_cache_path()
        )
        auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
        if not auth_manager.validate_token(cache_handler.get_cached_token()):
            # return redirect('/')
            raise Exception("Was unable to connct to your spotify account")

        return spotipy.Spotify(auth_manager=auth_manager)

    except Exception as ex:
        print(f"Error: {ex}")
    return None


# using spotipy to get a close match
def discover_song(audio_features, spotipy_manager=None):
    """discovers a song from spotify"""
    # get black box list of audio features :)
    # danceability, valence, energy dictionary
    songs = []

    local_spotify = get_spotipy() if spotipy_manager is None else spotipy_manager

    tracks = local_spotify.recommendations(
        seed_genres=["rock", "pop", "alternative", "indie", "rap"],
        target_danceability=audio_features["danceability"],
        target_energy=audio_features["energy"],
        target_valence=audio_features["valence"],
        limit=100,
    )

    for track in tracks["tracks"]:
        songs.append(track["uri"])

    return songs


def find_closest_match(ideal_features, playlist_features):
    """from a list of songs features, and the ideal features,
    function will return the clostest song to the ideal"""
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
                ideal_id = single_track["id"]

    except Exception as ex:
        print(f"Error: {ex}")

    return ideal_id  # some track id


def gather_song_set(playlist_id, ideal_audio_features, spotipy_manager=None):
    """Obtains a list of songs depending what playlist is selected"""
    local_spotipy = get_spotipy() if spotipy_manager is None else spotipy_manager

    try:

        if playlist_id in ["discover_mode", 1]:  # OR WAHATEVER WE WANTED
            songs = discover_song(ideal_audio_features, local_spotipy)

        elif playlist_id in ["liked_songs", "1"]:
            tracks = dict(local_spotipy.current_user_saved_tracks(limit=50))
            songs = []

            for song in tracks["items"]:
                if song is not None:
                    songs.append(dict(song)["track"]["uri"])

        else:
            # get the songs from the playlist
            tracks = local_spotipy.playlist(playlist_id)
            intermediate_songs = tracks["tracks"]["items"]
            songs = []

            for song in intermediate_songs[:100]:
                if song is not None:
                    songs.append(dict(song)["track"]["uri"])

        print(local_spotipy.current_playback().keys())
        curr_song = local_spotipy.current_playback()["item"]["uri"]
        if curr_song in songs:
            print(curr_song)
            songs.remove(curr_song)

    except Exception as ex:
        print(f"Error: {ex}")
        songs = ["spotify:track:4uLU6hMCjMI75M1A2tKUQC"]
        # default list of songs if something goes wrong,
        # nothing should so this should not really be used

    return songs


def filter_songs(track_ids, ideal_audio_features, spotipy_manager=None):
    """filters down the possible set of songs to the ideal one, return best match"""
    local_spotipy = get_spotipy() if spotipy_manager is None else spotipy_manager

    audio_features = None

    # get the audio features
    audio_features = local_spotipy.audio_features(tracks=track_ids)

    # find the closest match
    return find_closest_match(ideal_audio_features, audio_features)


def queue_song(cool_song, spotipy_manager=None):
    """takes the song given and queues and plays the song"""
    local_spotipy = get_spotipy() if spotipy_manager is None else spotipy_manager

    # add to queue
    if cool_song is not None:
        local_spotipy.add_to_queue(cool_song)

        if local_spotipy.current_playback() is not None:
            local_spotipy.next_track()
        else:
            local_spotipy.start_playback()


# Method that obtains and plays the next song given the circumstances
# Parameter idea_audio_features is the model's vector interpretation of the conversation
# Parameter data is the JSON packet sent back from the websocket. Includes playlistID
def next_song(ideal_audio_features, data):
    """queues a song based on the ideal audio features"""
    playlist_id = data["playlistID"]
    local_spotipy = get_spotipy()

    # TO DO to remove the song update timing when we get
    #  the proper conversation tracking in place
    if local_spotipy is not None and (
        local_spotipy.current_playback() is None
        or local_spotipy.current_playback()["progress_ms"] >= UPDATE_SONG_TIME_MS
        # TODO: Maybe implement here to change if conversation is changed enough?
    ):

        songs = gather_song_set(playlist_id, ideal_audio_features, local_spotipy)
        cool_song = filter_songs(songs, ideal_audio_features, local_spotipy)
        queue_song(cool_song, local_spotipy)

    return ideal_audio_features


# gets the playlists name and IDs and returns them (easily replaceable for URIs too)
def playlists(spotipy_manager=None):
    """gets the playlists name and IDs and returns them (easily replaceable for URIs too)"""
    local_spotify = spotipy_manager if spotipy_manager is not None else get_spotipy()
    local_playlists = None
    playlists_summary = {}

    if local_spotify is not None:
        local_playlists = local_spotify.current_user_playlists()

        if "items" in local_playlists:
            for single_playlist in local_playlists["items"]:
                playlists_summary[single_playlist["id"]] = single_playlist["name"]

    return playlists_summary


# def pickTrackFromPlaylist() # take in track ID, if empty/None, use liked songs playlist.
# This websocket is responsible for sending the auth token to the fronend in order to initialize
# a webplayer. See static/web_player.js
@sock.route("/webPlayer")
def spotify_web_player(socket):
    """
    This websocket is responsible for sending the auth token to the fronend in order to
    initialize a webplayer. See static/web_player.js
    """
    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path()
    )
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect("/")
    token = auth_manager.get_access_token()
    socket.send(token["access_token"])
    # sock.close()


# This websocket is used to first switch over Spotify to the Spotifinders Web API Device.
# This is what "Turns on" Our webplayer.
# This websocket is called FIRST when the server first loads
# and THEN every time the user selects a playlist.
@sock.route("/deviceID")
def device_listener(socket):
    """
    This websocket is used to first switch over Spotify to the Spotifinders Web API Device.
    This is what "Turns on" Our webplayer.
    This websocket is called FIRST when the server first loads
    and THEN every time the user selects a playlist.
    """
    try:
        # refactored to use less than 15 loacl vars...
        spotify = get_spotipy()
        if spotify:
            data = json.loads(socket.receive())
            print(f"Transferring playback to device {data['device_id']}")

            try:
                spotify.transfer_playback(device_id=data["device_id"])
            except Exception as ex:
                # TODO: Make this exception choose from "Liked" or "Discovery" mode
                # TODO: Broaden this error of transferring playback.
                # Possible glitch whenever user manually selects illegal song.
                # Try: frontend errors when illegal song
                spotify.start_playback(
                    device_id=data["device_id"],
                    uris=["spotify:track:6AjOUvtWc4h6MY9qEcPMR7"],
                )
                print(f"Error: {ex}")

            while True:
                data = json.loads(socket.receive())
                playlist_id = data["playlist_id"]
                is_custom = data["isCustomUserPlaylist"]

                if playlist_id == "discover_mode":
                    rec_songs_arr = spotify.recommendations(seed_genres=SEED_GENRES)[
                        "tracks"
                    ]
                    rec_uris = [song["uri"] for song in rec_songs_arr]
                    spotify.start_playback(device_id=data["device_id"], uris=rec_uris)

                elif playlist_id == "liked_songs":
                    # this array is a bunch of liked songs.
                    # arrray of {added at: , track: } objecats
                    # track is {artists... album... uri...}

                    # TO DO: Research liked song limitation. CAn only retrieve 50!
                    liked_songs_arr = spotify.current_user_saved_tracks(limit=50)[
                        "items"
                    ]

                    # TODO: See if we should sample more than 20 liked songs.
                    # Research what this does.
                    sampled_liked_songs = random.sample(liked_songs_arr, 20)

                    random_liked_song_uris = [
                        dict(song)["track"]["uri"] for song in sampled_liked_songs
                    ]
                    spotify.start_playback(
                        device_id=data["device_id"], uris=random_liked_song_uris
                    )
                elif is_custom:
                    print(f"Custom playlist recieved: {playlist_id} ")
                    selected_playlist = spotify.playlist(playlist_id)
                    spotify.start_playback(
                        device_id=data["device_id"],
                        context_uri=selected_playlist["uri"],
                    )
                else:
                    print(
                        f"Unknown variant of PlaylistID: {playlist_id}, \
                    \nThis should never happen!"
                    )

            # play from liked playlists

            # immediate pause

            # this should work but I am getting 403 errors when I have commeted out...
            saved_tracks = spotify.current_user_saved_tracks()["items"]
            first_song = saved_tracks[random.randint(0, len(saved_tracks) - 1)]["track"]
            spotify.add_to_queue(first_song["id"])  # queueFromPlaylist)

            # spotify.start_playback(device_id=device_id, \
            # uris=['spotify:track:6AjOUvtWc4h6MY9qEcPMR7'])
            # Ideally, we start playing a song depending on what they want
        else:
            print("Error: spotify not loaded for user")

    except Exception as ex:
        print(f"Error: {ex}")


@app.route("/testplayer")
def test():
    """just a useful test route for testing purposes"""
    audio_features = {}
    audio_features["danceability"] = 0.88
    audio_features["energy"] = 0.9
    audio_features["valence"] = 0.9

    playlist_id = "37i9dQZF1EUMDoJuT8yJsl"

    # return str(player(audioFeatures))
    return str(next_song(audio_features, playlist_id))


@app.route("/sign_out")
def sign_out():
    """sign out logic"""
    try:
        # Remove the CACHE file (.cache-test) so that a new user can authorize.
        os.remove(session_cache_path())
        session.clear()
    except OSError as ex:
        print(f"Error: {ex.filename} - {ex.strerror}.")
    return redirect("/")


@app.route("/currently_playing")
def currently_playing():
    """returns what is currently playing for the user"""
    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path()
    )
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect("/")
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    track = spotify.current_user_playing_track()
    if not track is None:
        return track
    return "No track currently playing."


@app.route("/start_playing", methods=["POST"])
def start_playing():
    """post method to start the playing of a song"""
    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path()
    )
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect("/")
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    # track = spotify.current_user_playing_track()
    spotify.start_playback(uris=["spotify:track:6AjOUvtWc4h6MY9qEcPMR7"])

    return "Playing"


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
