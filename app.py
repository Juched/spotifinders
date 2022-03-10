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

caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)

def session_cache_path():
    return caches_folder + session.get('uuid')


# update the song playing every 15 seconds
UPDATE_SONG_TIME_MS = 15 * 1000

# @app.route('/')
# def index():
#     return render_template('index.html')

@app.before_request
def before_request():
    if 'localhost' not in SPOTIPY_REDIRECT_URI:
        scheme = request.headers.get('X-Forwarded-Proto')
        if scheme and scheme == 'http' and request.url.startswith('http://'):
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
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope='user-library-read playlist-read-private user-top-read user-read-currently-playing user-read-playback-state streaming user-modify-playback-state',
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

    uPlaylists = playlists(spotify)

    return render_template("loggedin.html",purl=prof_pic_url, pname=u_data['display_name'], userPlaylists=uPlaylists) #map(json.dumps, uPlaylists))


# called once for each thread
@sock.route('/echo')
def echo(sock):
    model = SpotifinderModel()
    while True:
        data = json.loads(sock.receive())
        print(data)
        feature_dict = model.get_vector(data["text"])

        queueFromPlaylist(feature_dict, data)
        print(feature_dict)
        sock.send(feature_dict)

# gets the Spotipy obj
def getSpotipy():
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
def discoverSong(audioFeatures):
    # get black box list of audio features :)
    # danceability, valence, energy dictionary
    thing = ''
    try:
        
        # standard
        cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
        auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
        if not auth_manager.validate_token(cache_handler.get_cached_token()):
            return redirect('/')

        localSP = spotipy.Spotify(auth_manager=auth_manager)
        # return spotify.current_user_playlists()

        # 
        thing = localSP.current_playback()

        # play a new song if the timer allows it
        if localSP.current_playback() == None or localSP.current_playback()['progress_ms'] >= UPDATE_SONG_TIME_MS:
            songs = localSP.recommendations(seed_genres= ['rock', 'pop', 'alternative', 'indie', 'rap'], #localSP.recommendation_genre_seeds(),  #'alternative', #, pop, alternative, indie', # just general stuff for now
                target_danceability=audioFeatures['danceability'], 
                target_energy=audioFeatures['energy'], 
                target_valence=audioFeatures['valence']
                )


            
            # adds new suggest song to queue
            thing = songs['tracks'][0]['id']
            localSP.add_to_queue(thing)
            if localSP.current_playback() != None: #currently_playing() != None: # DOESN'T RETURN BOOL, BUT NOONE WILL TELL ME WHAT IT DOES RETURN AND I CANT TEST YET
                localSP.next_track()
            else:
                localSP.start_playback()

    except Exception as e:
        print (f"Error: {e}")

    return thing


def findClosestMatch(idealAF, playlistAFs):
    implementedFeatures = idealAF.keys()
    idealVector = []
    minNorm = None
    idealID = None

    try:

        for feature in implementedFeatures:
            idealVector.append(idealAF[feature])
        idealVector = np.array(idealVector)

        for singleTrack in playlistAFs:
            currentVector = []
            for feature in implementedFeatures:
                currentVector.append(singleTrack[feature])
            # we have the curernt audio feature vector at this point

            currentMin = np.linalg.norm(np.array(currentVector) - idealVector)
            if idealID == None or minNorm == None or currentMin < minNorm:
                minNorm = currentMin
                idealID = singleTrack['id']
                print(idealID)
    
    except Exception as e:
        print (f"Error: {e}")

    return idealID # some track id

#Method that starts play
def queueFromPlaylist(idealAudioFeatures, data):
    playlistID = data["playlistID"]

    #In the case this is a new playlist, we don't need to recommend anything (as of right now). Just transfer playback

    if playlistID == "discover_mode":
        discoverSong(idealAudioFeatures)
        return
    

    localSP = getSpotipy()
    audioFeatures = None

    if localSP != None and (localSP.current_playback() == None or localSP.current_playback()['progress_ms'] >= UPDATE_SONG_TIME_MS):
        # get the songs from the playlist
        # tracks = localSP.playlist(playlistID, fields="tracks,next")
        tracks = localSP.playlist(playlistID)

        # print(tracks)
        trackIDs = []

        for (song, i) in zip(tracks["tracks"]["items"], range(100)):
            if song != None:
                trackIDs.append(song['track']['id'])


        # get the audio features
        audioFeatures = localSP.audio_features(trackIDs)

        # find the closest match
        coolSong = findClosestMatch(idealAudioFeatures, audioFeatures)
        # add to queue
        if coolSong != None:
            localSP.add_to_queue(coolSong) 
            if localSP.current_playback() != None: #currently_playing() != None: # DOESN'T RETURN BOOL, BUT NOONE WILL TELL ME WHAT IT DOES RETURN AND I CANT TEST YET
                localSP.next_track()
            else:
                localSP.start_playback()
        
    return audioFeatures

# gets the playlists name and IDs and returns them (easily replaceable for URIs too)
def playlists(spotopyManager=None):
    
    localSP = spotopyManager if spotopyManager != None else getSpotipy()
    localPlaylists = None
    playlists = {}

    if localSP != None:
        localPlaylists = localSP.current_user_playlists()

        if "items" in localPlaylists:
            for p in localPlaylists["items"]:
                playlists[p["id"]] = p["name"]

    return playlists

# def pickTrackFromPlaylist() # take in track ID, if empty/None, use liked songs playlist
#This websocket is responsible for sending the auth token to the fronend in order to initialize a webplayer. See static/web_player.js
@sock.route('/webPlayer')
def spotifyWebPlayer(sock):
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')    
    token = auth_manager.get_access_token()
    sock.send(token['access_token'])
    # sock.close()

#This websocket is used to first switch over Spotify to the Spotifinders Web API Device. This is what "Turns on" Our webplayer
#This websocket is called FIRST when the server first loads and THEN every time the user selects a playlist.
@sock.route('/deviceID')
def deviceListener(sock):
    try:
        
        cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
        auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
        if not auth_manager.validate_token(cache_handler.get_cached_token()):
            return redirect('/')
        spotify = spotipy.Spotify(auth_manager=auth_manager)



        data = json.loads(sock.receive())
        print(f"Transferring playback to device {data['device_id']}")
        spotify.transfer_playback(device_id=data['device_id'])



        while(True):
            data = json.loads(sock.receive())
            playlist_id = data['playlist_id']
            is_custom = data['isCustomUserPlaylist']

            
            if playlist_id == "discover_mode":
                rec_songs_arr = spotify.recommendations(seed_genres= ['rock', 'pop', 'alternative', 'indie', 'rap'])['tracks']
                rec_uris = [song['uri'] for song in rec_songs_arr]
                spotify.start_playback(device_id=data['device_id'], uris=rec_uris)

            elif playlist_id == "liked_songs":
                #this array is a bunch of liked songs.
                #arrray of {added at: , track: } objecats
                #track is {artists... album... uri...} 
                liked_songs_arr = spotify.current_user_saved_tracks(limit=50)["items"]      #TODO: Research liked song limitation. CAn only retrieve 50!
                sampled_liked_songs = random.sample(liked_songs_arr, 20)                    #TODO: see if we should sample more than 20 liked songs. Research what this does too.
                random_liked_song_uris = [song['track']['uri'] for song in sampled_liked_songs]
                spotify.start_playback(device_id=data['device_id'], uris=random_liked_song_uris)
            elif is_custom:
                print(f"Custom playlist recieved: {playlist_id} ")
                selected_playlist = spotify.playlist(playlist_id)
                spotify.start_playback(device_id=data['device_id'], context_uri=selected_playlist['uri'])
            else:
                print(f"Unknown variant of PlaylistID: {playlist_id}, \nThis should never happen!")



        #play from liked playlists

        #immediate pause


        # this should work but I am getting 403 errors when I have commeted out...
        savedTracks = spotify.current_user_saved_tracks()["items"]
        firstSong = savedTracks[random.randint(0,len(savedTracks)-1)]["track"]
        spotify.add_to_queue(firstSong["id"]) # queueFromPlaylist)

        # spotify.start_playback(device_id=device_id, uris=['spotify:track:6AjOUvtWc4h6MY9qEcPMR7']) #Ideally, we start playing a song depending on what they want
    
    except Exception as e:
        print (f"Error: {e}")
    
    return 
def startPlay(tracks_array, spotify):
    song = tracks_array[random.randint(0,len(tracks_array)-1)]

    


    



@app.route('/testplayer')
def test():
    audioFeatures = {}
    audioFeatures['danceability'] = .88
    audioFeatures['energy'] = .9
    audioFeatures['valence'] = .9

    playlistID = '37i9dQZF1EUMDoJuT8yJsl'

    # return str(player(audioFeatures))
    return str(queueFromPlaylist(audioFeatures, playlistID))


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

    return "Playing"


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
