

// if(navigator.userAgent.toLowerCase().indexOf('firefox') > -1){
//   var julius = new Julius();
// }else{
var SpeechRecognition = window.webkitSpeechRecognition ||
                        window.mozSpeechRecognition ||
                        window.msSpeechRecognition ||
                        window.oSpeechRecognition ||
                        window.SpeechRecognition;

var recognition = new SpeechRecognition();

recognition.addEventListener('end', () => recognition.start())
recognition.onstart = function() {
  //console.log("We are listening. Try speaking into the microphone.");
};

recognition.onspeechend = function() {
  // when user is done speaking
  //recognition.stop();
  //recognition.start()
}

//this variable keeps track of the current playlist on the JS side.
//Whenever user changes playlist, we see a discrepancy between this variable and the HTML storage.
//When there is a discrepancy, this indicates recent playlist chnage. We have to tell the backend to start a different playlist.
var currentPlaylistID = document.getElementById("CURRENTLY_PLAYING").getAttribute("playlist_id"); //should be 1 at start.



var that = this;
recognition.onresult = function(event) {
    var transcript = event.results[0][0].transcript;
    var confidence = event.results[0][0].confidence;
    var x = document.getElementById("snackbar");
    x.innerHTML = transcript;

    // Add the "show" class to DIV
    x.className = "show";

    // After 3 seconds, remove the show class from DIV
    setTimeout(function(){ x.className = x.className.replace("show", ""); }, 2000);

    socketData = {};
    socketData["text"] = transcript;
    socketData["playlistID"] = document.getElementById("CURRENTLY_PLAYING").getAttribute("playlist_id");

    //Set the "isNew" flag. If the User has selected a new playlist, we send back "true". Otherwise, we send back "False"
    let isNew = false;
    if(socketData["playlistID"] != currentPlaylistID){
      console.log("User has switched playlists! exclaim new value on backend.")
      isNew = true;
      currentPlaylistID = socketData["playlistID"]
    }


    socketData["isNew"] = isNew
    socketData["deviceID"] = document.getElementById("CURRENTLY_PLAYING").getAttribute("device_id");


    console.log(transcript)
    console.log(confidence)
    socket.send(JSON.stringify(socketData))
    
};
recognition.start();
         
//}

// This runs when the speech recognition service starts

if (window.location.protocol == "https:") {
  var ws_scheme = "wss://";
} else {
  var ws_scheme = "ws://"
};

const socket = new WebSocket(ws_scheme + location.host + '/echo');


socket.addEventListener('message', ev => {
  console.log('<<< ' + ev.data);
});

// julius.onrecognition = function(sentence) {
//   console.log(sentence);
// };

// This runs when the speech recognition service returns result


//console.log("did this even start")
// start recognition

function toggleMic()
{
  document.getElementById("mic_icon").innerHTML = (document.getElementById('mic_icon').innerHTML === "mic_on" ? "mic_off" : "mic_on")
  if( document.getElementById("mic_icon").innerHTML == "mic_on"){
    document.getElementById("mic_icon").style.paddingLeft = "35%"
  } else {
    document.getElementById("mic_icon").style.paddingLeft = "0%"
  }
  
}

function playSong(url)
{
  var xhr = new XMLHttpRequest();
  xhr.open("POST", url, true);
  xhr.setRequestHeader('Content-Type', 'application/json');
  xhr.send();
}

