// Note: the global variables here references (current, tables, labels, pngs,...) are initialised in the HTML head

// submit feedback form
function submit_form() {

    // understandability data: depends on which radio button is clicked
    var understandable = document.getElementById("understandable");
    radios = understandable.getElementsByTagName("input");
    var understandability = "";
    for (var i = 0 ; i < radios.length; i++) {
        // each star has as a class name the corresponding number, so we can get
        // the score from there, and parse it as an integer.
        if (radios[i].checked) understandability = parseInt(radios[i].className);
    }

    // Same for this
    var convincing = document.getElementById("convincing");
    radios = convincing.getElementsByTagName("input");
    var convincingness = "";
    for (var i = 0 ; i < radios.length; i++) {
        if (radios[i].checked) convincingness = parseInt(radios[i].className);

    }

    // Feedback text...
    feedback = document.getElementById("further-feedback").value;

    // First, remove the "submit" button and substitute it with a thank you. This
    // is to avoid repeated clicks...
    var submit = document.getElementById("submit-area");
    submit.innerHTML = "<strong>Thank you!</strong>"

    // Prepare resulting request object
    result = {"understandability": understandability, "convincingness": convincingness, "feedback": feedback};

    // These variables contain the information about the justification (they are initialised in the HTML file head)
    result["justification_html"] = justification_html;
    result["justification_pickle"] = justification_pickle;
    result["signature"] = signature;

    // send a post request with this data to the feedback page (in a new tab)
    post(base_url + "/feedback", result, inNewPage = true)
}

// The area tags are inside the MAP for the clickable images. They represent the different nodes we can click on. That is,
// one area is a clicakble node. Every area has an id the corresponds to a node number.
// For every area, we set the onclick event to launch the click_node(event, NodeIdCorrespondingToThisArea)
var areas = document.getElementsByTagName('area');
for (var i = 0; i < areas.length; i++) {
    areas[i].setAttribute('onclick', 'click_node(event, \"' + areas[i].id + '\");')
}

// Redraw the page to show a node
function change_image(node) {

    //recall that the current global variable contains the current node index/number. So we update it
    current = node;

    // Depending on the value of current, we might hide/show the navigation buttons
    if (current == max) {
        document.getElementById("next").style.visibility = "hidden";
    } else {
        document.getElementById("next").style.visibility = "visible";
    }

    if (current == min) {
        document.getElementById("prev").style.visibility = "hidden";
    } else {
        document.getElementById("prev").style.visibility = "visible";
    }

    // The following data structures are indexes with a string of form "N{current_node}"
    var node = "N" + current;

    // Change the navigation image with the png imge corresponding to this node
    // recall that these images are base64-encoded
    document.getElementById("image").getElementsByTagName("img")[0].src = "data:image/png;base64," + pngs[node];

    // Update the label and table as well
    document.getElementById("description").innerHTML = labels[node];
    document.getElementById("outcomes-table").innerHTML = tables[node];
}

// Click on a node
function click_node(event, id) {
    // Prevent the default behaviour of clicking on a map object (it behaves as if a link was clicked)
    event.preventDefault(); 
    // Get the clicked node index from the id of the clicked node (e.g. N3)
    change_image(parseInt(id.slice(-1)));
}

// If there is one, go to the next node (current stores the current node)
function next() {
    if (current < max) {
        change_image(current + 1);
    }
}

// If there is one, go to the previous node (current stores the current node)
function prev() {

    if (current > min) {
        change_image(current - 1);
    }
}

// MODAL STUFF

// Get the modal
var modal = document.getElementById("myModal");

// Get the button that opens the modal
var btn = document.getElementById("rate-button");

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