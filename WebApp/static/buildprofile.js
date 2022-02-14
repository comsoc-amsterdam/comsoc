function htmlToElement(html) {
    var template = document.createElement('template');
    html = html.trim(); // Never return a text node of whitespace as the result
    template.innerHTML = html;
    return template.content.firstChild;
}

function post(path, params, method='post') {

  // The rest of this code assumes you are not using a library.
  // It can be made less verbose if you use one.
  const form = document.createElement('form');
  form.method = method;
  form.action = path;

  for (const key in params) {
    if (params.hasOwnProperty(key)) {
      const hiddenField = document.createElement('input');
      hiddenField.type = 'hidden';
      hiddenField.name = key;
      hiddenField.value = params[key];

      form.appendChild(hiddenField);
    }
  }

  document.body.appendChild(form);
  form.submit();
}

// RANK COLORS
  if (candidates.length > 1) {
    var colorInterpolator = d3.interpolateRgb("green", "red");

    steps = candidates.length;

    var colorArray = d3.range(0, (1 + 1 / steps), 1 / (steps - 1)).map(function(d) {
      return colorInterpolator(d)
    });

  } else {
    colorArray = ["green"];
  }


function rank(candidate_button) {
  var ballot = candidate_button.parentElement.parentElement;
  var ranked = ballot.getElementsByClassName("ranked")[0];
  var button = htmlToElement("<button class=\"derank-button\" type=\"button\" onclick=\"derank(this);\">" + candidate_button.innerHTML + "</button>");
  var rank = ranked.getElementsByClassName("derank-button").length;

  button.style.backgroundColor = colorArray[rank];
  ranked.appendChild(button);
  candidate_button.remove();
}

function derank(candidate_button) {
  var ballot = candidate_button.parentElement.parentElement;
  deranked = ballot.getElementsByClassName("deranked")[0];
  deranked_candidates = deranked.getElementsByTagName("button");
  new_candidate = htmlToElement("<button class=\"rank-button\" type=\"button\" onclick=\"rank(this);\">" + candidate_button.innerHTML + "</button>");

  var inserted = 0;

  for (var i = 0; i < deranked_candidates.length; i++) {
    if (deranked_candidates[i].innerHTML > candidate_button.innerHTML) {
      deranked.insertBefore(new_candidate, deranked_candidates[i]);
      inserted = 1;
      break;
    }
  }

  if (inserted == 0)
    deranked.appendChild(new_candidate);

  candidate_button.remove();

  ranked_candidates = ballot.getElementsByClassName("derank-button");

  for (var i = 0; i < ranked_candidates.length; i++) {
    ranked_candidates[i].style.backgroundColor = colorArray[i];
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

  html += "<div class=\"candidates\"><div class=\"deranked\">";
  for (var i = 0; i < candidates.length; i++) {
    html += "<button class=\"rank-button\" type=\"button\" onclick=\"rank(this);\">" + candidates[i] + "</button>";
  }
  html += "</div><div class=\"ranked\"></div></div>";
  html += "</div>";
  ballot = (htmlToElement(html));
  button_size = ballot.getElementsByClassName("candidates")[0].getElementsByClassName("deranked")[0].style.height;
  ballot.getElementsByClassName("candidates")[0].style.height = (candidates.length * (40 + 5*2)) + "px";

  ballots.insertBefore(ballot, ballots.firstChild);

  document.getElementById("submit").style.visibility = "visible";
}

function bad_candidate(candidate) {
    return (! /^[a-zA-Z]+$/.test(candidate));
}

function submit() {
  ballots = document.getElementsByClassName("ballot");
  profile_str = "";
  if (ballots.length > 0) {
    for (var i = 0; i < ballots.length; i++) {
      ballot = ballots[i];
      number = ballot.getElementsByClassName("quantity")[0].value;
      if (number <= 0) {
        return;
      }
      ranked_candidates = ballot.getElementsByClassName("ranked")[0].getElementsByTagName("button");
      if (ranked_candidates.length < candidates.length) {
        swal("You have some unranked alternatives!");
        return;
      }
      profile_str += number + ":";
      for (var j = 0; j < ranked_candidates.length; j++) {
        if (bad_candidate(ranked_candidates[j].innerHTML)) {
          return;
        }
        profile_str += ranked_candidates[j].innerHTML;
        if (j < ranked_candidates.length - 1) {
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