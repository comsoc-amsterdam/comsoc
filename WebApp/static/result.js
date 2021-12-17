function htmlDecode(input) {
  var doc = new DOMParser().parseFromString(input, "text/html");
  return doc.documentElement.textContent;
}

function render_next()
{   
    if (curr.descendants.length > 0) {
        curr = curr.descendants[0];
        document.getElementById("content").innerHTML = htmlDecode(curr.reachedBy);
        document.getElementById("content").innerHTML += '<br><hr><br>'
        document.getElementById("content").innerHTML += htmlDecode(curr.value);
    }
}

function render_prev()
{   
    if (curr.parent != null) {
        curr = curr.parent;
        document.getElementById("content").innerHTML = htmlDecode(curr.reachedBy);
        document.getElementById("content").innerHTML += '<br><hr><br>'
        document.getElementById("content").innerHTML += htmlDecode(curr.value);
    }
}

