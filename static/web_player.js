
if (window.location.protocol == "https:") {
  var ws_scheme = "wss://";
} else {
  var ws_scheme = "ws://";
}

const webPlayerSocket = new WebSocket(ws_scheme + location.host + '/webPlayer');


var authTok = null;

// Spotify Web Player won't get its "onReady" methods set until the authToken is sent from the backend.

webPlayerSocket.addEventListener('message', ev => {
// Once we get a message (auth token), establish SDK
  console.log(ev.data)
  authTok = ev.data
});



window.onSpotifyWebPlaybackSDKReady = () => {
  while (authTok == null) {
    console.log('awaiting authtok')

  } //await
  console.log("obtained token: " + authTok)

  const token = authTok; //Auth token!
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

// var that = this;

// function closeSocket(){
//   that.webPlayerSocket.close();
// }


  