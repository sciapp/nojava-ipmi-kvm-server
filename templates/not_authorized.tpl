<html>
 <head>
  <title>Not authorized</title>
  <style>
   #container {
    max-width: 500px;
    margin: auto;
   }
  </style>
 </head>
 <body>
  <div id="container">
   <h4>Hello {{ user['name'] }} ({{ user['email'] }})</h4>
   <h5>You are not authorized to use this service. Please contact pgiadmin if you think that this is a mistake.</h5>
   <button onclick="deleteAllCookies(); document.location='https://ifflogin.fz-juelich.de/'">Logout.</button>
  </div>
  <script>
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
