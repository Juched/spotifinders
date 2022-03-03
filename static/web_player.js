
if (window.location.protocol == "https:") {
  var ws_scheme = "wss://";
} else {
  var ws_scheme = "ws://";
}
console.log('web_player js loaded')
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

function makePlayer(socketMsg){
  // The following code block will run when the auth code is provided. Establishes the web player
  authTok = socketMsg

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

    player.togglePlay();

    // const deviceServer = new WebSocket(ws_scheme + location.host + '/deviceID');
    // deviceServer.addEventListener('open', (event) => {
    //   deviceServer.send(device_id);
    //   console.log('sent device id to client ' + device_id)
    // });

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
  var playpause = document.getElementById('pp_toggle')
  playpause.onclick = function() {
    player.togglePlay();
    if(playpause.classList.contains("glyphicon-play")){
      playpause.classList.remove("glyphicon-play")
      playpause.classList.add("glyphicon-pause")
    } else {
      playpause.classList.remove("glyphicon-pause")
      playpause.classList.add("glyphicon-play")
    }
  };
  document.getElementById('resume_song').onclick = function() {
    player.resume().then(() => {
      console.log('Resumed song!');
    });
  };
  document.getElementById('activate_element').onclick = function() {
    player.activateElement().then(() => {
      console.log('Activated element!');
    });
  };
  document.getElementById('skip_track').onclick = function() {
    player.nextTrack().then(() => {
      console.log('Skipped to next track!');
    });
  };
  document.getElementById('curr_state').onclick = function() {
    player.getCurrentState().then(state => {
      if (!state) {
        console.error('User is not playing music through the Web Playback SDK');
        return;
      }
    
      var current_track = state.track_window.current_track;
      var next_track = state.track_window.next_tracks[0];
    
      console.log('Currently Playing', current_track);
      console.log('Playing Next', next_track);
    });

  };
  console.log('all listeners added')
  player.connect().then(success => {
    if (success) {
      console.log('The Web Playback SDK successfully connected to Spotify!');
    }
  }).catch(function(err) {
    console.log("Failed to connect player. Player-connect issue, not authtok")
  });
  console.log('Should have obtained confirmation about playback sdk')

}

// var playpause = document.getElementById("toggle_play")
// playpause.onclick = function() {
//   playpause.classList.toggle('paused');
//   return false;
// };

// var playpause = document.getElementById("pp_toggle")
// playpause.onclick = function() {
//   if(playpause.classList.contains("glyphicon-play")){
//     playpause.classList.remove("glyphicon-play")
//     playpause.classList.add("glyphicon-pause")
//   } else {
//     playpause.classList.remove("glyphicon-pause")
//     playpause.classList.add("glyphicon-play")
//   }
//   return false;
// };




window.onSpotifyWebPlaybackSDKReady = () => {
  // Waits for the socket to provide an auth code. 
  connect().then(function(socketMsg) {
    makePlayer(socketMsg)
  }).catch(function(err) {
    // error here (Socket never recieved the auth token)
    console.log("failed to get authtok. No player created")
  });
}



