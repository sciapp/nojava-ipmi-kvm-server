<html>
 <head>
  <title>{{ title }}</title>
  <style>
   body {
    font-family: Helvetica, sans-serif;
    color: #222222;
    #margin: 25px;
    max-width: 1000px;
    margin: auto;
   }

   .time {
    font-style: oblique;
   }

    label {
     display: inline-block;
     min-width: 7em;
    }

    input, select {
     display: inline-block;
     width: 20em;
    }

    .submit-button {
     min-width: 12em;
    }

    .right-button {
     margin-left: 3em;
     min-width: 12em;
     #float: right;
    }

   .error-log {
    color: #cc2222;
   }

   .kvm-iframe {
    position:fixed;
    top:0;
    left:0;
    bottom:0;
    right:0;
    width:100%;
    height:100%;
    border:none;
    margin:0;
    padding:0;
    overflow:hidden;
    z-index:999999;
   }
  </style>
 </head>
 <body>
  <div id="container">
   <h4>Hello {{ user['name'] }} ({{ user['email'] }})</h4>

   <form>
    {% module xsrf_form_html() %}
    <label for="kvm-server">Server Name: </label>
    <datalist id="kvm-server-list">
     {% for server in servers %}
      <option value="{{ server }}">{{ server }}</option>
     {% end %}
    </datalist>
    <input id="kvm-server" autocomplete="on" list="kvm-server-list" placeholder="select server" name="server_name" />
    <br />

    <label for="kvm-password">Password: </label>
    <input type="password" id="kvm-password" name="password"/>
    <br />

    <label for="kvm-resolution">Resolution: </label>
    <select id="kvm-resolution" name="resolution">
      <option value="800x600">800 * 600</option>
      <option value="1024x768">1024 * 768</option>
      <option value="1280x960" selected="selected">1280 * 960</option>
      <option value="1600x1200">1600 * 1200</option>
    </select>
    <br />

    <button type="submit" class="submit-button" onclick="javascript:start_kvm();return false;">
     Connect!
    </button>
    <button type="submit" class="submit-button" formmethod="post" formtarget="_blank">
     Connect in new tab!
    </button>
    {% import os %}
    {% if 'OAUTH_HOST' in os.environ %}
    <button onclick="deleteAllCookies(); document.location='{{ os.environ['OAUTH_HOST'] }}'" class="right-button">Logout.</button>
    {% end %}
   </form>
  </div>
  <div id="logs">
   <ul id="logsul">
   </ul>
  </div>

  <script>
   var timerId = -1;
   var host_name = "";

   var ws = new WebSocket("{{ websocket_uri }}/kvm");
   ws.onopen = function() {
    console.log('Websocket open!');

    {% block ws_onopen %}
    {% end %}
   };
   ws.onmessage = function (evt) {
    console.log(evt.data);
    data = JSON.parse(evt.data);
    if (data.action && data.action == 'notice') {
     alert(data.message);
     if (data.refresh) {
      window.location = '/';
     }
    } else if (data.action && data.action == 'connected') {
     timerId !== -1 && clearInterval(timerId);
     timerId = -1;

     // delete logs container
     var element = document.getElementById('logs');
     element.parentNode.removeChild(element);

     document.title = 'Connected to ' + host_name;
     document.getElementById('container').innerHTML =
     '<iframe src="' + data.url + '" class="kvm-iframe" allowfullscreen>' +
     'Your browser does not support iframes...' +
     '</iframe>';
    } else if (data.action && (data.action == 'log' || data.action == 'error')) {
     logs = document.getElementById('logsul');
     elementclass = data.action == 'log' ? '' : 'class="error-log"';
     logs.innerHTML = logs.innerHTML + '<li><span class="time">' + (new Date()).toLocaleString('de-DE') + ': </span><span ' + elementclass + '>' + data.message + '</span></li>';
     if (data.action == 'error') {
      timerId !== -1 && clearInterval(timerId);
      timerId = -1;

      var text = 'Failed to connect.';
      document.getElementById('container').innerHTML = '<h1>' + text + '</h1>';
      document.title = text;
     }
    }
   };

   function start_kvm() {
    host_name = document.getElementById('kvm-server').value.trim();
    var amount = 0;
    function updateTitle() {
     var text = 'Connecting to ' + host_name + '.'.repeat(amount++);
     document.getElementById('container').innerHTML = '<h1>' + text + '</h1>';
     document.title = text;
     amount = amount % 4;
    }
    timerId = setInterval(updateTitle, 1000);
    ws.send(JSON.stringify({
     'action':   'connect',
     'server':   host_name,
     'password': document.getElementById('kvm-password').value,
     'resolution': document.getElementById('kvm-resolution').value
    }));
    updateTitle();
   }

   function deleteAllCookies() {
    var cookies = document.cookie.split(";");

    for (var i = 0; i < cookies.length; i++) {
     var cookie = cookies[i];
     var eqPos = cookie.indexOf("=");
     var name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
     document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT";
    }
   }
  </script>
 </body>
</html>
