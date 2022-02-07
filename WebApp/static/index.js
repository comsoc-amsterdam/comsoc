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

function handle_keypress() {
  if(document.getElementById("addCandidate").value === "") submit();
  else add_candidate();
}

function htmlToElement(html) {
    var template = document.createElement('template');
    html = html.trim(); // Never return a text node of whitespace as the result
    template.innerHTML = html;
    return template.content.firstChild;
}

function add_candidate() {

  candidates = document.getElementById("candidates").getElementsByTagName('div');

  if (candidates.length >= 4) {
    return;
  }

  var new_candidate = document.getElementById("addCandidate").value;

  if (new_candidate == "") {
    return;
  }

  document.getElementById("addCandidate").value = "";

  new_node = htmlToElement("<div class=\"a-candidate-div\" id=" + new_candidate + "><label><span class=\"a-candidate-span\">"+ new_candidate + "</span></label><button class=\"a-candidate-button\" onclick=\"remove(" + new_candidate + ");\">x</button></div>");
  new_node.style.opacity = 0;

  var added = 0;

  for (var i = 0; i < candidates.length; i++) {
    if (candidates[i].id.toLowerCase() == new_candidate.toLowerCase()) {
      return;
    }
    if (candidates[i].id.toLowerCase() > new_candidate.toLowerCase()) {
      document.getElementById("candidates").insertBefore(new_node, candidates[i]);
      added = 1;
      break;
    }
  }
  
  if (added == 0) {
    document.getElementById("candidates").appendChild(new_node);
  }

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

function remove(to_delete) {
  to_delete.remove();
}

function submit() {

  candidates = document.getElementById("candidates").getElementsByTagName('div');

  if (candidates.length <= 0) {
    return;
  }

  result = {};

  for (var i = 0; i < candidates.length; i++) {
    result["candidate_" + candidates[i].id] = candidates[i].id
  }

  post('/buildprofile', result)
}