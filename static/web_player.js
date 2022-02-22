
if (window.location.protocol == "https:") {
  var ws_scheme = "wss://";
} else {
  var ws_scheme = "ws://";
}

// This function establishes a websocket and waits for it to get a message (the auth token)
function connect() {
  return new Promise(function(resolve, reject) {
      var server = new WebSocket(ws_scheme + location.host + '/webPlayer');
      server.onmessage = function(event) {

          resolve(event.data);
      };
      server.onerror = function(err) {
          reject(err);
      };

  });
}





window.onSpotifyWebPlaybackSDKReady = () => {

  // This is where the function is called
  connect().then(function(socketMsg) {

    authTok = socketMsg
    console.log("Obtained authtok "  + authTok)

    const token = authTok; //Auth token!
    console.log("Creating new player with token " + authTok)
    const player = new Spotify.Player({
      name: 'Spotifinders Web Player',
      getOAuthToken: cb => { cb(token); },
      volume: 0.5
    });
    // Ready
    player.addListener('ready', ({ device_id }) => {
      console.log('Ready with Device ID', device_id);
      const deviceServer = new WebSocket(ws_scheme + location.host + '/deviceID');
      deviceServer.addEventListener('open', (event) => {
        deviceServer.send(device_id);
        console.log('sent device id to client ' + device_id)
      });

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
    document.getElementById('start_device').onclick = function() {
      player.activateElement();
      player.togglePlay();
    };
    player.connect().then(success => {
      if (success) {
        console.log('The Web Playback SDK successfully connected to Spotify!');
      }
    });

  }).catch(function(err) {
    // error here
    console.log("failed to get authtok. No player created")
  });
  


}

// var that = this;

// function closeSocket(){
//   that.webPlayerSocket.close();
// }


  