"""Spotify Web Requester module."""
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

def requestSong():
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials()) #.Spotify()
    # start_playback()
    # add_to_queue()
    # get the URL for an artist image given the artist’s name
    # results = sp.search(q='artist:' + name, type='artist')
    # items = results['artists']['items']
    # sp.recommendations(seed_genres=recommendation_genre_seeds())

    # q=name:abacab&type=album,track where q is the query and type is the thing with that name,
    # returns list of album or tracks in this case with name q
