// Initialise the colors for each rank position in a dictionary that maps
// a rank position (1,2,3...) to a color

// if we have at least 2 alternatives... (should always be true)
if (alternatives.length > 1) {
  // d3 is imported from the HTML file
  // it creates an interpolator from green to red
  var colorInterpolator = d3.interpolateRgb("green", "red");
  // number of interpolation steps: alternatives
  steps = alternatives.length;
  // the color array is created with this function
  var colorArray = d3.range(0, (1 + 1 / steps), 1 / (steps - 1)).map(function(d) {
    return colorInterpolator(d)
  });
// If only one alternative: just green
} else {
  colorArray = ["green"];
}

// Happens when sombedoy clicks on a alternative to be ranked
function rank(alternative_button) {
  // the relative ballot
  var ballot = alternative_button.parentElement.parentElement;
  // the alternative slaready ranked in this ballot
  var ranked = ballot.getElementsByClassName("ranked")[0];
  // create a new button (the ranked alternative on the right side) in HTML
  // it is of class derank-button, and when clicked laucnehs the "derank" function
  var button = htmlToElement("<button class=\"derank-button\" type=\"button\" onclick=\"derank(this);\">" + alternative_button.innerHTML + "</button>");
  // The rank of the current alternative is the length of the already-ranked alterantives
  var rank = ranked.getElementsByClassName("derank-button").length;
  // Set the color accordingly
  button.style.backgroundColor = colorArray[rank];
  ranked.appendChild(button);
  // Remove from the rankable alternatives
  alternative_button.remove();
}

// Similar as above, but when an already ranked alternative is "deranked"
function derank(alternative_button) {
  var ballot = alternative_button.parentElement.parentElement;
  deranked = ballot.getElementsByClassName("deranked")[0];
  deranked_alternatives = deranked.getElementsByTagName("button");
  new_alternative = htmlToElement("<button class=\"rank-button\" type=\"button\" onclick=\"rank(this);\">" + alternative_button.innerHTML + "</button>");

  // Add the alternative back to the "rankable" ones of this ballot, in alphabetical orderr
  // Flag: was this inserted?
  var inserted = 0;

  // scan all rankable alternatives and insert it in the right position
  for (var i = 0; i < deranked_alternatives.length; i++) {
    if (deranked_alternatives[i].innerHTML > alternative_button.innerHTML) {
      deranked.insertBefore(new_alternative, deranked_alternatives[i]);
      inserted = 1;
      break;
    }
  }

  // No "right positon" found? Add it at the end
  if (inserted == 0)
    deranked.appendChild(new_alternative);

  // remove the "derank" button from the right side
  alternative_button.remove();

  // Adjust the color of the ranked alterntives accordingly
  ranked_alternatives = ballot.getElementsByClassName("derank-button");
  for (var i = 0; i < ranked_alternatives.length; i++) {
    ranked_alternatives[i].style.backgroundColor = colorArray[i];
  }
}

// Get the html code for the selector button for assigning a number of voters to a ballot
function get_number_button() {
  button = "<div class=\"number-input\">";
  button += "<button onclick=\"this.parentNode.querySelector('input[type=number]').stepDown()\" class=\"minus\"></button>";
  button += "<input class=\"quantity\" min=\"1\" name=\"quantity\" value=\"1\" type=\"number\">";
  button += "<button onclick=\"this.parentNode.querySelector('input[type=number]').stepUp()\" class=\"plus\"></button>";
  button += "</div><img src=\"https://cdn.icon-icons.com/icons2/1674/PNG/512/person_110935.png\" class=\"person-icon\"/>";
  return button;
}

// Remove a ballot. If none are there, then hide the possibility to submit
function remove_ballot(ballot) {
  ballot.remove();
  var ballots = document.getElementsByClassName("ballot");
  if (ballots.length == 0) {
    document.getElementById("submit").style.visibility = "hidden";
  }
}

// Add a new ballot
function add_ballot() {
  ballots = document.getElementById("ballots");

  // Dynamically build the html code
  html = "<div class=\"ballot\">";

  html += "<div class=\"handle-ballot\">";
  html += get_number_button(); // add the "number selector" button
  html += "<button class=\"ballot-remove\" onclick=\"remove_ballot(this.parentNode.parentNode);\">&times;</button>";
  html += "</div>";

  // Add the rankable alterantives
  html += "<div class=\"alternatives\"><div class=\"deranked\">";
  for (var i = 0; i < alternatives.length; i++) {
    html += "<button class=\"rank-button\" type=\"button\" onclick=\"rank(this);\">" + alternatives[i] + "</button>";
  }
  html += "</div><div class=\"ranked\"></div></div>";
  html += "</div>";
  // construct the html object
  ballot = (htmlToElement(html));
  // Dynamically set the height
  button_size = ballot.getElementsByClassName("alternatives")[0].getElementsByClassName("deranked")[0].style.height;
  ballot.getElementsByClassName("alternatives")[0].style.height = (alternatives.length * (40 + 5*2)) + "px";

  // Add the new ballot first
  ballots.insertBefore(ballot, ballots.firstChild);

  // The submit button is visible whenever a ballot is added (originally hidden)
  document.getElementById("submit").style.visibility = "visible";
}

// Submit the profile
function submit() {
  // Get all ballots
  ballots = document.getElementsByClassName("ballot");
  // Construct the profile string. Format: 3:a>b>c,2:b>a>c means that three voters express a>b>c and two b>a>c
  profile_str = "";
  // For each ballot (if at least one)
  if (ballots.length > 0) {
    for (var i = 0; i < ballots.length; i++) {
      ballot = ballots[i];
      // Number of voters (must be positive)
      number = ballot.getElementsByClassName("quantity")[0].value;
      if (number <= 0) {
        swal("Ballot counts must be positive!");
        return;
      }
      // Ranked alterantives: must be all!
      ranked_alternatives = ballot.getElementsByClassName("ranked")[0].getElementsByTagName("button");
      if (ranked_alternatives.length < alternatives.length) {
        swal("You have some unranked alternatives!");
        return;
      }
      // Add the number of voters the profile string, and then we add the alternatives
      // just to be sure, check again that no special character was used in the alternatives names
      profile_str += number + ":";
      for (var j = 0; j < ranked_alternatives.length; j++) {
        if (bad_input(ranked_alternatives[j].innerHTML)) {
          return;
        }
        // add the alternative, an if it is not the last one, also a >
        profile_str += ranked_alternatives[j].innerHTML;
        if (j < ranked_alternatives.length - 1) {
          profile_str += '>';
        }
      }
      // if this is not the last ballot, add a comma to separate it
      if (i < ballots.length - 1) {
        profile_str += ','
      }
    }
  }

  // sanity check
  if (profile_str == "") {
    return;
  }

  // send a post request with to the outcome selection page with this profile
  post(base_url + '/outcomes', {"profile" : profile_str});
}