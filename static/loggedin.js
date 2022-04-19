
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

  fetch("http://localhost:5000/book", {
     method: "POST",
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify(data)
  }).then(res => {
     return res.json();
  }).then(jsonRes => {
     console.log(jsonRes);
  }).catch(error => {
     console.log(error);
  });
}
