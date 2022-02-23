// In the input field, if we press enter when the text is empty, we submit.
// If the text is not empty, we add the alternative
function handle_keypress() {
  if(document.getElementById("addAlternative").value === "")
    submit();
  else add_alternative();
}

function add_alternative() {
  // Add new alternative

  // Get the current alternatives
  alternatives = document.getElementById("alternatives").getElementsByTagName('div');

  // The new alternative (from the input field)
  var new_alternative = document.getElementById("addAlternative").value;

  // Can't me empty... We don't react
  if (new_alternative.length == 0) {
    return;
  }

  // If alternative is not alphabetical, can't go on...
  // (sweet alert is included in the main HTML file)
  if (bad_input(new_alternative)) {
    swal("Bad alternative name!");
    return;
  }

  // Alternative accepted!

  // If we had already one alternative, now we have two: so we set the submit button as visible
  // (originally it was hidden)
  if (alternatives.length == 1) {
    document.getElementById("submit").style.opacity = "1";
    document.getElementById("submit").style.cursor = "pointer";
  }

  // If we had already three alternatives, now we have four: so we set hide the addAlternative button
  // (in this way we cap the number of alternatives to four)
  if (alternatives.length == 3) {
    document.getElementById("addButton").style.opacity = "0.5";
    document.getElementById("addButton").style.cursor = "default";
  }

  // Empty the input field
  document.getElementById("addAlternative").value = "";

  // Construct the new altenrative as html
  new_node = htmlToElement("<div class=\"alternative-div\" id=" + new_alternative + "><label><span class=\"alternative-span\">"+ new_alternative + "</span></label><button class=\"alternative-button\" onclick=\"remove(" + new_alternative + ");\">x</button></div>");

  // Hide it at first (we will do a fade-in later)
  new_node.style.opacity = 0;

  // Add it in alphabetical order.
  // Flag to check whether it is added or not
  var added = 0;

  // Scan the list of alternatives we already have...
  // (comparisons are case insensitive)
  for (var i = 0; i < alternatives.length; i++) {
    // Already have this... Exit this function
    if (alternatives[i].id.toLowerCase() == new_alternative.toLowerCase()) {
      return;
    }
    // Ok, we need to add it here!
    if (alternatives[i].id.toLowerCase() > new_alternative.toLowerCase()) {
      document.getElementById("alternatives").insertBefore(new_node, alternatives[i]);
      added = 1;
      break;
    }
  }
  
  // If not added yet, add it at the end
  if (added == 0) {
    document.getElementById("alternatives").appendChild(new_node);
  }

  // Fade-in
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

// Remove an alternative
function remove(to_delete) {
  // Once an alternative is removed, irrespectively of the number of alternatives (it will be always less than 4)
  // we make the "add an alternative" fully visibile and clicakble
  document.getElementById("addButton").style.opacity = "1";
  document.getElementById("addButton").style.cursor = "pointer";

  // remove the alternative
  to_delete.remove();

  // If we have less than two alternatives, hide the submit button
  alternatives = document.getElementById("alternatives").getElementsByTagName('div');
  if (alternatives.length < 2) {
    document.getElementById("submit").style.opacity = "0";
    document.getElementById("submit").style.cursor = "default";
  }
}

// Submit the data!
function submit() {

  alternatives = document.getElementById("alternatives").getElementsByTagName('div');

  // Must have at least two
  if (alternatives.length < 2) {
    return;
  }

  // Request dictionary object
  result = {};

  // Add all alternatives to the request object (unless they have bad characters in them)
  for (var i = 0; i < alternatives.length; i++) {
    if (bad_input(alternatives[i].id)) {
      return;
    }
    
    result["alternative_" + alternatives[i].id] = alternatives[i].id
  }

  // Send this request-data to the buildprofile page (as a post request)
  post('/buildprofile', result);
}

// When we click the example link, we directly send a post request to the outcomes page
// with an example profile encoded as a string
function example() {
  post('/outcomes', {"profile": "2:Chianti>Brunello>Amarone,1:Brunello>Amarone>Chianti,1:Brunello>Chianti>Amarone,1:Amarone>Chianti>Brunello"});
}

/* modal code */

 // Get the modal
var modal = document.getElementById("myModal");

// Get the button that opens the modal
var btn = document.getElementById("open_modal");

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