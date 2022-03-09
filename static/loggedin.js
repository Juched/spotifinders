

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

    console.log(transcript)
    console.log(confidence)
    socket.send(transcript)
    
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