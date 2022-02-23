// RANK COLORS
  if (alternatives.length > 1) {
    var colorInterpolator = d3.interpolateRgb("green", "red");

    steps = alternatives.length;

    var colorArray = d3.range(0, (1 + 1 / steps), 1 / (steps - 1)).map(function(d) {
      return colorInterpolator(d)
    });

  } else {
    colorArray = ["green"];
  }


function rank(alternative_button) {
  var ballot = alternative_button.parentElement.parentElement;
  var ranked = ballot.getElementsByClassName("ranked")[0];
  var button = htmlToElement("<button class=\"derank-button\" type=\"button\" onclick=\"derank(this);\">" + alternative_button.innerHTML + "</button>");
  var rank = ranked.getElementsByClassName("derank-button").length;

  button.style.backgroundColor = colorArray[rank];
  ranked.appendChild(button);
  alternative_button.remove();
}

function derank(alternative_button) {
  var ballot = alternative_button.parentElement.parentElement;
  deranked = ballot.getElementsByClassName("deranked")[0];
  deranked_alternatives = deranked.getElementsByTagName("button");
  new_alternative = htmlToElement("<button class=\"rank-button\" type=\"button\" onclick=\"rank(this);\">" + alternative_button.innerHTML + "</button>");

  var inserted = 0;

  for (var i = 0; i < deranked_alternatives.length; i++) {
    if (deranked_alternatives[i].innerHTML > alternative_button.innerHTML) {
      deranked.insertBefore(new_alternative, deranked_alternatives[i]);
      inserted = 1;
      break;
    }
  }

  if (inserted == 0)
    deranked.appendChild(new_alternative);

  alternative_button.remove();

  ranked_alternatives = ballot.getElementsByClassName("derank-button");

  for (var i = 0; i < ranked_alternatives.length; i++) {
    ranked_alternatives[i].style.backgroundColor = colorArray[i];
  }
}


function decrease_count(object) {
  var button = object.parentNode;
  number = button.getElementsByClassName("number")[0];
  value = parseInt(number.innerHTML);
  if (value == 1) {
    button.parentNode.remove();
  }
  else {
    number.innerHTML = value - 1;
  }
}

function increase_count(object) {
  var button = object.parentNode;
  number = button.getElementsByClassName("number")[0];
  value = parseInt(number.innerHTML);
  number.innerHTML = value + 1;
}

function get_number_button() {
  button = "<div class=\"number-input\">";
  button += "<button onclick=\"this.parentNode.querySelector('input[type=number]').stepDown()\" class=\"minus\"></button>";
  button += "<input class=\"quantity\" min=\"1\" name=\"quantity\" value=\"1\" type=\"number\">";
  button += "<button onclick=\"this.parentNode.querySelector('input[type=number]').stepUp()\" class=\"plus\"></button>";
  button += "</div><img src=\"https://cdn.icon-icons.com/icons2/1674/PNG/512/person_110935.png\" class=\"person-icon\"/>";
  return button;
}

function remove_ballot(ballot) {
  ballot.remove();
  var ballots = document.getElementsByClassName("ballot");
  if (ballots.length == 0) {
    document.getElementById("submit").style.visibility = "hidden";
  }
}

function add_ballot() {
  ballots = document.getElementById("ballots");

  html = "<div class=\"ballot\">";

  html += "<div class=\"handle-ballot\">";
  html += get_number_button();
  html += "<button class=\"ballot-remove\" onclick=\"remove_ballot(this.parentNode.parentNode);\">&times;</button>";
  html += "</div>";

  html += "<div class=\"alternatives\"><div class=\"deranked\">";
  for (var i = 0; i < alternatives.length; i++) {
    html += "<button class=\"rank-button\" type=\"button\" onclick=\"rank(this);\">" + alternatives[i] + "</button>";
  }
  html += "</div><div class=\"ranked\"></div></div>";
  html += "</div>";
  ballot = (htmlToElement(html));
  button_size = ballot.getElementsByClassName("alternatives")[0].getElementsByClassName("deranked")[0].style.height;
  ballot.getElementsByClassName("alternatives")[0].style.height = (alternatives.length * (40 + 5*2)) + "px";

  ballots.insertBefore(ballot, ballots.firstChild);

  document.getElementById("submit").style.visibility = "visible";
}

function submit() {
  ballots = document.getElementsByClassName("ballot");
  profile_str = "";
  if (ballots.length > 0) {
    for (var i = 0; i < ballots.length; i++) {
      ballot = ballots[i];
      number = ballot.getElementsByClassName("quantity")[0].value;
      if (number <= 0) {
        swal("Ballot counts must be positive!");
        return;
      }
      ranked_alternatives = ballot.getElementsByClassName("ranked")[0].getElementsByTagName("button");
      if (ranked_alternatives.length < alternatives.length) {
        swal("You have some unranked alternatives!");
        return;
      }
      profile_str += number + ":";
      for (var j = 0; j < ranked_alternatives.length; j++) {
        if (bad_input(ranked_alternatives[j].innerHTML)) {
          return;
        }
        profile_str += ranked_alternatives[j].innerHTML;
        if (j < ranked_alternatives.length - 1) {
          profile_str += '>';
        }
      }
      if (i < ballots.length - 1) {
        profile_str += ','
      }
    }
  }

  if (profile_str == "") {
    return;
  }

  post('/outcomes', {"profile" : profile_str});
}