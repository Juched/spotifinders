let playlist = null
/* New functions */
function toggleTextBox() {
  var x = document.getElementById("inputTextContainer");
  x.classList.toggle("off")
}
function closeMenu() {
  var x = document.getElementById("inputTextContainer");
  x.classList.add("off")
}

function togglePlaylistMenu(){
  var x = document.getElementById("generated-playlist-container");
  x.classList.toggle("off")
}

function submitTextInBox()
{
  text_box = document.getElementById('text_box')
  text_box_data = text_box.value
  text_box.value = ""
  let data = {text: text_box_data};

  closeMenu();

  fetch("http://localhost:5000/book", {
    method: "POST",
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  }).then(res => {
    return res.json();
  }).then(jsonRes => {
    console.log(jsonRes);
    playlist = jsonRes;
      
    console.log(jsonRes['0'])
    let songContainer = document.getElementById('generated-playlists');
      songContainer.innerHTML = "";
    for (var song in jsonRes){
      console.log("PRINGINT STUFF " + jsonRes[song]['name']);
      let songDiv = document.createElement("div");
      songDiv.classList.add("songBox");

      let album_art = document.createElement("img");
      album_art.setAttribute("src",jsonRes[song]['album_art']);
      album_art.classList.add("album-art");


      let nameDiv = document.createElement("div");
      nameDiv.innerText = jsonRes[song]['name'];
      nameDiv.classList.add("song-name");

      let artistDiv = document.createElement("div");
      artistDiv.innerText = jsonRes[song]['artist'];
      artistDiv.classList.add("artist-name");

      songDiv.appendChild(album_art);
      songDiv.appendChild(nameDiv);
      songDiv.appendChild(artistDiv);

      songContainer.appendChild(songDiv);
    }
    togglePlaylistMenu();






    

  }).catch(error => {
     console.log(error);
  });
}

function createPlaylist()
{
  if (playlist != null)
  {
    fetch("http://localhost:5000/create_playlist", {
      method: "POST",
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(playlist)
    }).then(res => {
      return res.json();
   }).then(jsonRes => {
      console.log(jsonRes[0]);
   }).catch(error => {
      console.log(error);
   });

    playlist = null;
  }
}

