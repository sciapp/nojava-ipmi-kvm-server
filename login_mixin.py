import os
import json
from typing import Dict, Any
import tornado
import tornado.auth
import tornado.escape
import tornado.httputil
import tornado.httpclient
import tornado.ioloop
import tornado.web
import urllib
try:
    import certifi
    ca_certs = certifi.where()
except:
    ca_certs = None

class OAuth2LoginMixin(tornado.auth.OAuth2Mixin):
    """
    OAuth2Mixin for use with oauth authentication providers.
    Subclasses need to define the following variables:
    - OAUTH_CLIENT_ID
    - OAUTH_CLIENT_SECRET
    - OAUTH_REDIRECT_URI
    """

    def __init__(self, *args, oauth_host="", **kwargs):
        super(OAuth2LoginMixin, self).__init__()
        self._OAUTH_AUTHORIZE_URL = oauth_host + "/oauth/authorize"
        self._OAUTH_ACCESS_TOKEN_URL = oauth_host + "/oauth/token"
        self._OAUTH_USER_INFO_URL = oauth_host + "/api/me"


    async def get_authenticated_user(self, code: str) -> Dict[str, Any]:
        """

        Handles the login for the oauth user, returning the user info.
        """
        http_client = self.get_auth_http_client()
        # get the access token for this code
        response = await http_client.fetch(
            self._OAUTH_ACCESS_TOKEN_URL,
            method="POST",
            headers={"Accept": "application/json"},
            validate_cert=True,
            body=urllib.parse.urlencode([
                ('client_id', self.OAUTH_CLIENT_ID),
                ('client_secret', self.OAUTH_CLIENT_SECRET),
                ('redirect_uri', self.OAUTH_REDIRECT_URI),
                ('grant_type', "authorization_code"),
                ('code', code)
            ])
        )

        response_data = json.loads(response.body.decode('utf8', 'replace'))
        access_token = response_data['access_token']
        # get the user information for this access token
        request = tornado.httpclient.HTTPRequest(
            self._OAUTH_USER_INFO_URL,
            method="GET",
            validate_cert=True,
            headers={
                "Accept": "application/json",
                "User-Agent": "OAuth2LoginHandler",
                "Authorization": "Bearer {}".format(access_token)
            },
            ca_certs=ca_certs
        )

        response = await http_client.fetch(request)
        response_data = json.loads(response.body.decode('utf8', 'replace'))
        return response_data
