// completely untested since I could not get my spotify to load with the app :)






window.onSpotifyWebPlaybackSDKReady = () => {
  const token = '';
  const player = new Spotify.Player({
    name: 'Spotifinders Web Player',
    getOAuthToken: cb => { cb(token); },
    volume: 0.5
  });



  // Ready
  player.addListener('ready', ({ device_id }) => {
    console.log('Ready with Device ID', device_id);
  });

  // Not Ready
  player.addListener('not_ready', ({ device_id }) => {
    console.log('Device ID has gone offline', device_id);
  });
  player.addListener('initialization_error', ({ message }) => { 
    console.error(message);
  });

  player.addListener('authentication_error', ({ message }) => {
      console.error(message);
  });

  player.addListener('account_error', ({ message }) => {
      console.error(message);
  });

  player.connect();
}



// window.onSpotifyWebPlaybackSDKReady = () => {
//   // You can now initialize Spotify.Player and use the SDK

//   const play = ({
//     spotify_uri,
//     playerInstance: {
//       _options: {
//         getOAuthToken
//       }
//     }
//   }) => {
//     getOAuthToken(access_token => {
//       fetch(`https://api.spotify.com/v1/me/player/play?device_id=${id}`, {
//         method: 'PUT',
//         body: JSON.stringify({ uris: [spotify_uri] }),
//         headers: {
//           'Content-Type': 'application/json',
//           'Authorization': `Bearer ${access_token}`
//         },
//       });
//     });
//   };
  
//   play({
//     playerInstance: new Spotify.Player({ name: "..." }),
//     spotify_uri: 'spotify:track:7xGfFoTpQ2E7fRF5lN10tr',
//   });
// };


  