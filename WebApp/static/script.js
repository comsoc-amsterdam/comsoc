function allowDrop (ev) {
   ev.preventDefault ();
}

function drag (ev) {
  ev.dataTransfer.setData ("src", ev.target.id);
}

function drop (ev) {
  ev.preventDefault ();
  var src = document.getElementById (ev.dataTransfer.getData ("src"));
  var srcParent = src.parentNode;
  var tgt = ev.currentTarget.firstElementChild;
  var tgtParent = tgt.parentNode;

  if (srcParent.parentNode == tgtParent.parentNode) {
    ev.currentTarget.replaceChild (src, tgt);
    srcParent.appendChild (tgt);
  }
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

function collectProfile (ev) {

  var selectableElements = document.getElementsByClassName("selectable").length
  var grayedOutElements = document.getElementsByClassName("dulled").length

  if (grayedOutElements < selectableElements) {

    var profileString = "";

    var voters = document.getElementsByClassName("voter");

    for(var v = 0; v < voters.length; v++){
      let ballot = []
      var positions = voters[v].getElementsByClassName("position");
      for(var i = 0; i < positions.length; i++){
        profileString += positions[i].getElementsByTagName("img")[0].classList[0]
        if (i < positions.length - 1)
          profileString += ","
      }
      if (v < voters.length -1)
        profileString += ";"
    }
    
    var outcomeString = "";

    var alternatives = document.getElementsByClassName("selectable");

    for(var a = 0; a < alternatives.length; a++){
      if (! alternatives[a].classList.contains("dulled")) {
        for(var c = 0; c < alternatives[a].classList.length; c++){
          if (alternatives[a].classList[c] != "selectable") {
            if (outcomeString != "") 
              outcomeString += ",";

            outcomeString += alternatives[a].classList[c];
          }
        }
      }
    }

    post('/result', {profile: profileString, outcome: outcomeString});
  }
  
}

function greyOut (id) {
  document.getElementById(id).classList.toggle('dulled');
}

function removeVoter (voter) {
  if (document.getElementsByClassName("voter").length > 1) 
    voter.remove()
}

function copyVoter (voter) {
  var clone = voter.cloneNode(true); // the true is for deep cloning

  voter_n = document.getElementsByClassName("voter").length + 1

  clone.id = "voter" + voter_n
  
  var spans = clone.getElementsByTagName("span")

  for(var s = 0; s < spans.length; s++) {
    spans[s].id = "position" + voter_n + "_" + s
    spans[s].getElementsByTagName("img")[0].id = "draggable" + voter_n + "_" + s
  }

  voter.parentNode.insertBefore(clone, voter.nextSibling);
}