let playlist = null

function toggleTextBox() {
  var x = document.getElementById("inputTextContainer");
  x.classList.toggle("off")
}
function closeMenu() {
  var x = document.getElementById("inputTextContainer");
  x.classList.add("off")
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

