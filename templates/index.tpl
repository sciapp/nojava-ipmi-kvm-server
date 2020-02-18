<html>
 <head>
  <title>{{ title }}</title>
 </head>
 <body>
  <div id="container">
   <h4>Hello {{ user['name'] }} ({{ user['email'] }}) {% if user['is_admin'] %}(admin){% end %}</h4>

   <form onsubmit="start_kvm(); return false;">
    Server Name: <select id="kvm-server">
     {% for server in servers %}
      <option value="{{ server }}">{{ server }}</option>
     {% end %}
    </select>
    Password: <input type="password" id="kvm-password" />
    <button type="submit">
     Connect!
    </button>
   </div>
  </form>

  <script>
   var timerId = -1;
   var host_name = "";

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
     document.title = 'Connected to ' + host_name;
     document.getElementById('container').innerHTML =
     '<iframe src="' + data.url + '" style="position:fixed; top:0; left:0; bottom:0; right:0; width:100%; height:100%; border:none; margin:0; padding:0; overflow:hidden; z-index:999999;">' +
     'Your browser does not support iframes...' +
     '</iframe>';
    }
   };

   function start_kvm() {
    host_name = document.getElementById('kvm-server').value.trim();
    var amount = 0;
    timerId = setInterval(function() {
     var text = 'Connecting to ' + host_name + '.'.repeat(amount++);
     document.getElementById('container').innerHTML = '<h1>' + text + '</h1>';
     document.title = text;
     amount = amount % 4;
    }, 1000);
    ws.send(JSON.stringify({
     'action':   'connect',
     'server':   host_name,
     'password': document.getElementById('kvm-password').value
    }));
   }
  </script>
 </body>
</html>
