function handle_keypress() {
  if(document.getElementById("addAlternative").value === "") submit();
  else add_alternative();
}

function add_alternative() {

  alternatives = document.getElementById("alternatives").getElementsByTagName('div');

  var new_alternative = document.getElementById("addAlternative").value;

  if (new_alternative.length == 0) {
    return;
  }

  if (bad_input(new_alternative)) {
    swal("Bad alternative name!");
    return;
  }

  // Alternative accepted

  if (alternatives.length == 1) {
    document.getElementById("submit").style.opacity = "1";
    document.getElementById("submit").style.cursor = "pointer";
  }

  if (alternatives.length == 3) {
    document.getElementById("addButton").style.opacity = "0.5";
    document.getElementById("addButton").style.cursor = "default";
  }

  document.getElementById("addAlternative").value = "";

  new_node = htmlToElement("<div class=\"alternative-div\" id=" + new_alternative + "><label><span class=\"alternative-span\">"+ new_alternative + "</span></label><button class=\"alternative-button\" onclick=\"remove(" + new_alternative + ");\">x</button></div>");
  new_node.style.opacity = 0;

  var added = 0;

  for (var i = 0; i < alternatives.length; i++) {
    if (alternatives[i].id.toLowerCase() == new_alternative.toLowerCase()) {
      return;
    }
    if (alternatives[i].id.toLowerCase() > new_alternative.toLowerCase()) {
      document.getElementById("alternatives").insertBefore(new_node, alternatives[i]);
      added = 1;
      break;
    }
  }
  
  if (added == 0) {
    document.getElementById("alternatives").appendChild(new_node);
  }

  var steps = 0;
    var timer = setInterval(function() {
        steps++;
        new_node.style.opacity = 0.05 * steps;
        if(steps >= 20) {
            clearInterval(timer);
            timer = undefined;
        }
  }, 20);
}

function remove(to_delete) {
  document.getElementById("addButton").style.opacity = "1";
  document.getElementById("addButton").style.cursor = "pointer";
  to_delete.remove();

  alternatives = document.getElementById("alternatives").getElementsByTagName('div');

  if (alternatives.length < 2) {
    document.getElementById("submit").style.opacity = "0";
    document.getElementById("submit").style.cursor = "default";
  }
}

function submit() {

  alternatives = document.getElementById("alternatives").getElementsByTagName('div');

  if (alternatives.length < 2) {
    return;
  }

  result = {};

  for (var i = 0; i < alternatives.length; i++) {
    if (bad_input(alternatives[i].id)) {
      return;
    }
    
    result["alternative_" + alternatives[i].id] = alternatives[i].id
  }

  post('/buildprofile', result);
}

function example() {
  post('/outcomes', {"profile": "2:Chianti>Brunello>Amarone,1:Brunello>Amarone>Chianti,1:Brunello>Chianti>Amarone,1:Amarone>Chianti>Brunello"});
}

/* modal */

 // Get the modal
var modal = document.getElementById("myModal");

// Get the button that opens the modal
var btn = document.getElementById("myBtn");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

// When the user clicks on the button, open the modal
btn.onclick = function() {
  modal.style.display = "block";
}

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
  modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
} 