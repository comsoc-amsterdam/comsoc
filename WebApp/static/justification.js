function submit_form() {
    var understandable = document.getElementById("understandable");
    radios = understandable.getElementsByTagName("input");
    var understandability = "";
    for (var i = 0 ; i < radios.length; i++) {
        if (radios[i].checked) understandability = radios[i].className;
    }

    var convincing = document.getElementById("convincing");
    radios = convincing.getElementsByTagName("input");
    var convincingness = "";
    for (var i = 0 ; i < radios.length; i++) {
        if (radios[i].checked) convincingness = radios[i].className;

    }

    feedback = document.getElementById("further-feedback").value;

    var submit = document.getElementById("submit-area");
    submit.innerHTML = "<strong>Thank you!</strong>"

    post("/feedback", {"understandability": understandability, "convincingness": convincingness, "feedback": feedback, "justification" : justification, "html_justification": html_justification})
}

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

var areas = document.getElementsByTagName('area');
for (var i = 0; i < areas.length; i++) {
    areas[i].setAttribute('onclick', 'click_node(event, \"' + areas[i].id + '\");')
}

function change_image(node) {
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

    document.getElementById("image").getElementsByTagName("img")[0].src = "data:image/png;base64," + pngs[node];
    document.getElementById("description").innerHTML = labels[node];

    document.getElementById("outcomes-table").innerHTML = tables[node];
}

function click_node(event, id) {
    event.preventDefault();

    var node = "N" + id.slice(-1);
    current = parseInt(id.slice(-1));
    change_image(node);
}

function next() {
    if (current < max) {
        current = current + 1;
        var node = "N" + current;
        change_image(node);
    }
}

function prev() {

    if (current > min) {
        current = current - 1;
        var node = "N" + current;
        change_image(node);
    }
}

