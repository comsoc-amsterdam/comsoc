function count_checkboxes() {

  // This function checks how many checkboxes are selected
  // If at least one outcome and one axiom are, then it shows the "submit" button, otherwise it hides it
  // This function is executed each time the page is rendered, or a checkbox is clicked on

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

  // Start the search for a justification...

  // Init request dictionary. We send in the profile (string-encoded)
  // (this variable is initialised in the HTML file)
  result = {"profile": profile_name};

  var all_axioms = document.getElementById("checkboxes").getElementsByClassName('axiom-checkbox');
  var checked_axioms = []; // list of checked axioms

  for (var i = 0; i < all_axioms.length; i++) {
    if (all_axioms[i].checked) {
      checked_axioms.push(all_axioms[i]);
    }
  }

  if (checked_axioms.length <= 0) {
     // If no axioms are selected, end. (This should not be possible, since
     // the submit button is rendered only when at least one is)
    return;
  }

  // for each checked axiom, add it to the request object
  // as: axiom_<axiomname>: <axioname>
  for (var i = 0; i < checked_axioms.length; i++) {
    // input validation (this should not happen unless the DOM was manipulated, since 
    // there was input validations before)
    if (bad_input(checked_axioms[i].id))
      return; 
    result["axiom_" + checked_axioms[i].id] = checked_axioms[i].id
  }

  // This is basically the same as what just happened for axioms
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


  // Hide the content and show the loading message while we wait...
  document.getElementById("true-content").style.visibility = "hidden";
  document.getElementById("loading").style.visibility = "visible";

  // Good! post the request object to the results page.
  post('/result', result);
}