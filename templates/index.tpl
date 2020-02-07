<html>
 <head>
  <title>{{ title }}</title>
 </head>
 <body>
  <div id="container">
   <h4>Hello {{ user['name'] }} ({{ user['email'] }}) {% if user['is_admin'] %}(admin){% end %}</h4>

   Server Name: <select id="kvm-server">
    {% for server in servers %}
     <option value="{{ server }}">{{ server }}</option>
    {% end %}
   </select>
   Password: <input type="password" id="kvm-password" />
   <button onclick="start_kvm()">
    Connect!
   </button>
  </div>

  <script>
   var timerId = -1;

   var ws = new WebSocket("{{ websocket_uri }}/kvm");
   ws.onopen = function() {
    console.log('Websocket open!');
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
     clearInterval(timerId);
     document.getElementById('container').innerHTML =
     '<iframe src="' + data.url + '" style="position:fixed; top:0; left:0; bottom:0; right:0; width:100%; height:100%; border:none; margin:0; padding:0; overflow:hidden; z-index:999999;">' +
     'Your browser does not support iframes...' +
     '</iframe>';
    }
   };

   function start_kvm() {
    var amount = 0;
    timerId = setInterval(function() {
     document.getElementById('container').innerHTML = '<h1>Connecting' + '.'.repeat(amount++) + '</h1>';
     amount = amount % 4;
    }, 1000);
    ws.send(JSON.stringify({
     'action':   'connect',
     'server':   document.getElementById('kvm-server').value,
     'password': document.getElementById('kvm-password').value
    }));
   }
  </script>
 </body>
</html>
