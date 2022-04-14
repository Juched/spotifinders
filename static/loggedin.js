function buttonClick()
{
  text_box_data = document.getElementById('text_box').value

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
