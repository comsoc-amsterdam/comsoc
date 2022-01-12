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

function rank(candidate_button) {
  var ballot = candidate_button.parentElement.parentElement;
  var ranked = ballot.getElementsByClassName("ranked")[0];
  ranked.appendChild(htmlToElement("<button type=\"button\" onclick=\"derank(this);\">" + candidate_button.innerHTML + "</button>"));
  candidate_button.remove();
}

function derank(candidate_button) {
  var ballot = candidate_button.parentElement.parentElement;
  deranked = ballot.getElementsByClassName("deranked")[0];
  deranked_candidates = deranked.getElementsByTagName("button");
  new_candidate = htmlToElement("<button type=\"button\" onclick=\"rank(this);\">" + candidate_button.innerHTML + "</button>");
  for (var i = 0; i < deranked_candidates.length; i++) {
    if (deranked_candidates[i].innerHTML >  candidate_button.innerHTML) {
      deranked.insertBefore(new_candidate, deranked_candidates[i]);
      candidate_button.remove();
      return;
    }
  }

  deranked.appendChild(new_candidate);
  candidate_button.remove();
}

function add_ballot() {
  ballots = document.getElementById("ballots");
  html = "<div><input type=\"number\" value=\"1\" min=\"1\"> rank these: <span class=\"deranked\"> ";
  for (var i = 0; i < candidates.length; i++) {
    html += "<button type=\"button\" onclick=\"rank(this);\">" + candidates[i] + "</button>";
  }
  html += "</span> ranked: <span class=\"ranked\"> </span> <button type=\"button\" onclick=\"this.parentNode.remove();\">remove</button></div>";
  ballots.appendChild((htmlToElement(html)));
}

function submit() {
  ballots = document.getElementById("ballots").getElementsByTagName("div");
  profile_str = "";
  if (ballots.length > 0) {
    for (var i = 0; i < ballots.length; i++) {
      ballot = ballots[i];
      number = ballot.getElementsByTagName("input")[0].value;
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