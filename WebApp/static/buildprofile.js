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

var rank_color = {0: "#008000", 1: "#595300", 2: "#a62d00", 3: "#ff0000"}

function rank(candidate_button) {
  var ballot = candidate_button.parentElement.parentElement;
  var ranked = ballot.getElementsByClassName("ranked")[0];
  var button = htmlToElement("<button class=\"derank-button\" type=\"button\" onclick=\"derank(this);\">" + candidate_button.innerHTML + "</button>");
  var rank = ranked.getElementsByClassName("derank-button").length;
  button.style.backgroundColor = rank_color[rank];
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
    ranked_candidates[i].style.backgroundColor = rank_color[i];
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
  button += "</div>";
  return button;
}

function add_ballot() {
  ballots = document.getElementById("ballots");

  html = "<div class=\"ballot\">";

  html += "<div class=\"handle-ballot\">";
  html += get_number_button();
  html += "<button class=\"ballot-remove\" onclick=\"this.parentNode.parentNode.remove();\">x</button>";
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
        return;
      }
      profile_str += number + ":";
      for (var j = 0; j < ranked_candidates.length; j++) {
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

  result = {"profile" : profile_str}

  all_axioms = document.getElementById("axioms").getElementsByTagName('input');
  checked_axioms = [];

  for (var i = 0; i < all_axioms.length; i++) {
    if (all_axioms[i].checked) {
      checked_axioms.push(all_axioms[i]);
    }
  }

  if (checked_axioms.length <= 0) {
    return;
  }

  for (var i = 0; i < checked_axioms.length; i++) {
    result["axiom_" + checked_axioms[i].id] = checked_axioms[i].id
  }

  all_outcomes = document.getElementById("outcome").getElementsByTagName('input');
  checked_outcomes = [];

  for (var i = 0; i < all_outcomes.length; i++) {
    if (all_outcomes[i].checked) {
      checked_outcomes.push(all_outcomes[i]);
    }
  }

  if (checked_outcomes.length <= 0) {
    return;
  }

  for (var i = 0; i < checked_outcomes.length; i++) {
    result["outcome_" + checked_outcomes[i].id] = checked_outcomes[i].id
  }

  post('/result', result);
}