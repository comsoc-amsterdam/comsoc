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

function htmlToElement(html) {
    var template = document.createElement('template');
    html = html.trim(); // Never return a text node of whitespace as the result
    template.innerHTML = html;
    return template.content.firstChild;
}

function add_candidate() {

  candidates = document.getElementById("candidates").getElementsByTagName('span');

  if (candidates.length >= 4) {
    return;
  }

  var new_candidate = document.getElementById("addCandidate").value;

  if (new_candidate == "") {
    return;
  }

  document.getElementById("addCandidate").value = "";

  new_node = htmlToElement("<span id=" + new_candidate + "><p class=\"boxed\">" + new_candidate + "</p><button class=\"button-2\" role=\"button\" onclick=\"remove(" + new_candidate + ");\">-</button><br></span>");

  for (var i = 0; i < candidates.length; i++) {
    if (candidates[i].id == new_candidate) {
      return;
    }
    if (candidates[i].id >  new_candidate) {

      document.getElementById("candidates").insertBefore(new_node, candidates[i]);
      return;
    }
  }

  document.getElementById("candidates").appendChild(new_node);
}

function remove(to_delete) {
  to_delete.remove();
}

function submit() {

  candidates = document.getElementById("candidates").getElementsByTagName('span');

  if (candidates.length <= 0) {
    return;
  }

  result = {};

  for (var i = 0; i < candidates.length; i++) {
    result["candidate_" + candidates[i].id] = candidates[i].id
  }

  post('/buildprofile', result)
}