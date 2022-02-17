// completely untested since I could not get my spotify to load with the app :)


window.onSpotifyWebPlaybackSDKReady = () => {
  // You can now initialize Spotify.Player and use the SDK

  const play = ({
    spotify_uri,
    playerInstance: {
      _options: {
        getOAuthToken
      }
    }
  }) => {
    getOAuthToken(access_token => {
      fetch(`https://api.spotify.com/v1/me/player/play?device_id=${id}`, {
        method: 'PUT',
        body: JSON.stringify({ uris: [spotify_uri] }),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${access_token}`
        },
      });
    });
  };
  
  play({
    playerInstance: new Spotify.Player({ name: "..." }),
    spotify_uri: 'spotify:track:7xGfFoTpQ2E7fRF5lN10tr',
  });
};


  