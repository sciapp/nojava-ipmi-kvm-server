"""
ifflogin_tornado - A demo for using iffLogin in a tornado app
"""
import os
import secrets
import json
from typing import Dict, Any
import tornado
import tornado.auth
import tornado.escape
import tornado.httputil
import tornado.httpclient
import tornado.ioloop
import tornado.web
try:
    import certifi
    ca_certs = certifi.where()
except:
    ca_certs = None
# print(ca_certs)
class IFFLoginOAuth2Mixin(tornado.auth.OAuth2Mixin):
    """
    OAuth2Mixin for use with iffLogin.
    Subclasses need to define the following variables:
    - IFFLOGIN_CLIENT_ID
    - IFFLOGIN_CLIENT_SECRET
    - IFFLOGIN_REDIRECT_URI
    """
    IFFLOGIN_HOST = 'https://ifflogin.fz-juelich.de'
    _OAUTH_AUTHORIZE_URL = IFFLOGIN_HOST + "/oauth/authorize"
    _OAUTH_ACCESS_TOKEN_URL = IFFLOGIN_HOST + "/oauth/token"
    async def get_authenticated_user(self, code: str) -> Dict[str, Any]:
        """

        Handles the login for the iffLogin user, returning the user info.
        """
        http_client = self.get_auth_http_client()
        # get the access token for this code
        url = tornado.httputil.url_concat(f"{self.IFFLOGIN_HOST}/oauth/token", {
            'client_id': self.IFFLOGIN_CLIENT_ID,
            'client_secret': self.IFFLOGIN_CLIENT_SECRET,
            'redirect_uri': self.IFFLOGIN_REDIRECT_URI,
            'grant_type': "authorization_code",
            'code': code,
        })
        request = tornado.httpclient.HTTPRequest(
            url,
            method="POST",
            headers={
                "Accept": "application/json"
            },
            validate_cert=True,
            body='',
            ca_certs=ca_certs)
        # response = await http_client.fetch(
        #     url,
        #     method="POST",
        #     headers={"Accept": "application/json"},
        #     validate_cert=True,
        #     body=''
        # )
        response = await http_client.fetch(request)
        response_data = json.loads(response.body.decode('utf8', 'replace'))
        access_token = response_data['access_token']
        # get the user information for this access token
        request = tornado.httpclient.HTTPRequest(
            self.IFFLOGIN_HOST + "/api/me",
            method="GET",
            validate_cert=True,
            headers={
                "Accept": "application/json",
                "User-Agent": "IFFLoginOAuth2Handler",
                "Authorization": "Bearer {}".format(access_token)
            },
            ca_certs=ca_certs
        )
        # response = await http_client.fetch(
        #     self.IFFLOGIN_HOST + "/api/me",
        #     method="GET",
        #     validate_cert=True,
        #     headers={
        #         "Accept": "application/json",
        #         "User-Agent": "IFFLoginOAuth2Handler",
        #         "Authorization": "Bearer {}".format(access_token)
        #     }
        # )
        response = await http_client.fetch(request)
        response_data = json.loads(response.body.decode('utf8', 'replace'))
        return response_data
