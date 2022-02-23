function htmlToElement(html) {
    // Given an html string, return the corresponding DOM object 
    var template = document.createElement('template');
    html = html.trim(); // Never return a text node of whitespace as the result
    template.innerHTML = html;
    return template.content.firstChild;
}

// post a request object (dictionary) to a page (path). If inNewPage is true, open it in a new page
function post(path, params, method='post', inNewPage = false) {

  // The rest of this code assumes you are not using a library.
  // It can be made less verbose if you use one.
  const form = document.createElement('form');
  form.method = method;
  form.action = path;
  if (inNewPage)
    form.target = "_blank" //open in new page

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

// Check if an input is NOT alphabetical
function bad_input(inpt) {
  return (! /^[a-zA-Z]+$/.test(inpt));
}