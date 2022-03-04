
if (window.location.protocol == "https:") {
  var ws_scheme = "wss://";
} else {
  var ws_scheme = "ws://";
}
console.log('web_player js loaded')

var isPlayerReady = false;
onSpotifyWebPlaybackSDKReady = () => {
  //update button
  isPlayerReady = true;
};


//This function synchronizes all web player buttons depending on status of player.
//Update Album Art
//update Song Title
//Synch play/pause button
//
function synchronizePlayer(state){
  if (!state) {
    console.error('User is not playing music through the Web Playback SDK');
    return;
  }

  var playpause = document.getElementById('pp_toggle');
  if(state.paused) {
    //it's paused, make it reflect so
    playpause.classList.remove("glyphicon-pause");
    playpause.classList.add("glyphicon-play");
  } else {
    //it's playing, make it reflect so
    playpause.classList.remove("glyphicon-play");
    playpause.classList.add("glyphicon-pause");
  }

  let artists_concat = ""
  for (let artist of state.track_window.current_track.artists) {
    artists_concat = artists_concat + artist.name + ", "
  }

  var songNameBox = document.getElementById('song_title');
  songNameBox.innerText = state.track_window.current_track.name + "\n Artist: " + artists_concat.substring(0, artists_concat.length - 2)

  var albumArtBox = document.getElementById('album_art');
  albumArtBox.setAttribute('src',state.track_window.current_track.album.images[0].url)
}
function pauseButtonToggle(){
  var playpause = document.getElementById('pp_toggle');
  if(playpause.classList.contains('glyphicon-play')){
    playpause.classList.remove("glyphicon-play");
    playpause.classList.add("glyphicon-pause");
  } else {
    playpause.classList.remove("glyphicon-pause");
    playpause.classList.add("glyphicon-play");
  }
}


// This function establishes a websocket and waits for it to get a message (the auth token)
function connect_webplayer_socket() {
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

    const deviceServer = new WebSocket(ws_scheme + location.host + '/deviceID');
    deviceServer.addEventListener('open', (event) => {
      deviceServer.send(device_id);
      console.log('sent device id to client ' + device_id)
    });

  });

  // Not Ready
  player.addListener('not_ready', ({ device_id }) => {
    console.log('Device ID has gone offline', device_id);
    player.disconnect(); //disconnect player bc we'll just make you re-make a player

    //TODO: grey out stuff again to force new player

  });

  player.addListener('player_state_changed', (state) => {
    synchronizePlayer(state);
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
  document.getElementById('pp_toggle').onclick = function() {
    player.togglePlay().then(function(value) {
      console.log('Toggled playback!');
    });
  };
  document.getElementById('skip_forward').onclick = function() {
    player.nextTrack().then(() => {
      console.log('Skipped to next track!');
    });
  };
  document.getElementById('skip_backward').onclick = function() {
    player.previousTrack().then(() => {
      console.log('Skipped back to the last track!');
    });
  };

  player.connect().then(success => {
    if (success) {
      console.log('The Web Playback SDK successfully connected to Spotify!');
    }
  });
}




function startPlayer() {
  // Waits for the socket to provide an auth code.
  if(isPlayerReady) {
    connect_webplayer_socket().then(function(socketMsg) {
      makePlayer(socketMsg);
    }).catch(function(err) {
      // error here (Socket never recieved the auth token)
      console.log("failed to get authtok. No player created")
    });

    delMask()
  } 
}
function delMask(){
  document.getElementById('mask_player').style.display = 'none';
}



