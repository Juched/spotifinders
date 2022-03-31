

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

  //When speech recognition is ready, we decide that textbox functionality be initialized

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

    sendSpeechSocketUpdate(transcript)


    console.log(transcript)
    console.log(confidence)

};
recognition.start();

//}

// This runs when the speech recognition service starts

if (window.location.protocol == "https:") {
  var ws_scheme = "wss://";
} else {
  var ws_scheme = "ws://"
};



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

function toggleDebugMenu(toggleOn){
  menu = document.getElementById("debug_selection_box");

  if(toggleOn){
    menu.style.display = "block";
  } else {
    menu.style.display = "none";
  }
}

function toggleTypeMode(){
  button = document.getElementById("type_toggle");

  if(button.classList.contains("toggle_off")){
    //button is currently off. user is trying to turn it on.
    //this code runs "turn on" code for button
    button.classList.remove("toggle_off");
    button.classList.add("toggle_on");

    document.getElementById("typebox").style.display = "block";
    button.innerHTML = "Type In Mode: On";
  } else {
    //button is currently on. user is trying to turn it off.
    //this code runs "turn off" code for button
    if (button.classList.contains("toggle_on")){
      button.classList.remove("toggle_on")
    }
    button.classList.add("toggle_off")
    document.getElementById("typebox").style.display = "none";
    button.innerHTML = "Type In Mode: Off";

    
  }
}



