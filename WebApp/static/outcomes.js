function count_checkboxes() {
  var all_axioms = document.getElementById("checkboxes").getElementsByClassName('axiom-checkbox');
  var checked_axioms = 0;

  for (var i = 0; i < all_axioms.length; i++) {
    if (all_axioms[i].checked) checked_axioms++;
  }

  var all_outcomes = document.getElementById("outcome").getElementsByTagName('input');
  var checked_outcomes = 0;

  for (var i = 0; i < all_outcomes.length; i++) {
    if (all_outcomes[i].checked) checked_outcomes++;
  }

  if (checked_axioms == 0 || checked_outcomes == 0) {
     document.getElementById("submit").style.visibility = "hidden";
  } else {
     document.getElementById("submit").style.visibility = "visible";
  }
}

function submit() {

  var all_axioms = document.getElementById("checkboxes").getElementsByClassName('axiom-checkbox');
  var checked_axioms = [];

  for (var i = 0; i < all_axioms.length; i++) {
    if (all_axioms[i].checked) {
      checked_axioms.push(all_axioms[i]);
    }
  }

  if (checked_axioms.length <= 0) {
    return;
  }

  result = {"profile": profile_name};

  for (var i = 0; i < checked_axioms.length; i++) {
    if (bad_input(checked_axioms[i].id))
      return; 
    result["axiom_" + checked_axioms[i].id] = checked_axioms[i].id
  }

  var all_outcomes = document.getElementById("outcome").getElementsByTagName('input');
  var checked_outcomes = [];

  for (var i = 0; i < all_outcomes.length; i++) {
    if (all_outcomes[i].checked) {
      checked_outcomes.push(all_outcomes[i]);
    }
  }

  if (checked_outcomes.length <= 0) {
    return;
  }

  for (var i = 0; i < checked_outcomes.length; i++) {
    if (bad_input(checked_outcomes[i].id))
      return; 

    result["outcome_" + checked_outcomes[i].id] = checked_outcomes[i].id
  }

  document.getElementById("true-content").style.visibility = "hidden";
  document.getElementById("loading").style.visibility = "visible";

  post('/result', result);
}