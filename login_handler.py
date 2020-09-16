import os

import ldap3
from login_mixin import OAuth2LoginMixin
from basehandler import BaseHandler

class OAuth2LoginHandler(BaseHandler, OAuth2LoginMixin):
    """
    Handler for authorization for oauth servers
    """

    def __init__(self, *args, **kwargs):
        BaseHandler.__init__(self, *args, **kwargs)
        OAuth2LoginMixin.__init__(self, *args, oauth_host=os.environ.get('OAUTH_HOST', ''), **kwargs)
        self.OAUTH_CLIENT_ID = os.environ.get('OAUTH_CLIENT_ID', None)
        self.OAUTH_CLIENT_SECRET = os.environ.get('OAUTH_CLIENT_SECRET', None)
        self.OAUTH_REDIRECT_URI = "{}/oauth/login".format(os.environ['WEBAPP_BASE'])


    async def get(self):
        """
        Cheks wether the user is logged in or not and handles authentication
        """
        if not self.OAUTH_CLIENT_ID:
            self.set_secure_cookie("user", "anonymous-email")
            self.set_secure_cookie("user_name", "anonymous")
            self.set_secure_cookie("is_admin", "on")
            return self.redirect("/dashboard")

        if self.get_argument("code", ""):
            user_data = await self.get_authenticated_user(self.get_argument("code", ""))
            # Use user_data to find the user in your user database or use their data directly
            email = user_data["email"]
            uid = user_data["username"]
            self.set_secure_cookie("user", email)
            self.set_secure_cookie("user_name", uid)

            # Skip LDAP authorization checking if not defined -> all users are allowed
            if "LDAP_DEFAULT_SERVER" not in os.environ:
                self.set_secure_cookie("is_admin", "on")
            else:
                # Connect to ldap to check access of group
                try:
                    if 'LDAP_FALLBACK_SERVER' in os.environ:
                        pool = [
                            ldap3.Server(os.environ['LDAP_DEFAULT_SERVER'], use_ssl=True, get_info=ldap3.ALL),
                            ldap3.Server(os.environ['LDAP_FALLBACK_SERVER'], use_ssl=True, get_info=ldap3.ALL)
                        ]
                    else:
                        pool = ldap3.Server(os.environ['LDAP_DEFAULT_SERVER'], use_ssl=True, get_info=ldap3.ALL)
                    base_dn = os.environ['LDAP_BASE_DN']
                    user_dn = os.environ['LDAP_USER_DN']
                    password = os.environ['LDAP_PASSWORD']
                    connection = ldap3.Connection(pool, user=user_dn, password=password, auto_bind=True)
                    reader = ldap3.Reader(connection, ldap3.ObjectDef('inetUser', connection), base_dn,
                                        '(&(objectClass=inetOrgPerson)(mail={email})(uid={uid}))'.format(email=email, uid=uid))
                    user_infos = reader.search()
                    self.set_secure_cookie("is_admin", "off")
                    if user_infos:
                        for user in user_infos:
                            if 'memberOf' in user:
                                if os.environ['LDAP_GROUP_DN'] in user['memberOf']:
                                    self.set_secure_cookie("is_admin", "on")
                                    break
                    else:
                        print("Error")  # TODO Error handling
                except Exception as e:
                    print(e)
            return self.redirect("/dashboard")
        if self.get_argument("error", ""):
            self.write(self.get_argument("error", ""))
        else:
            return self.authorize_redirect(
                redirect_uri=self.OAUTH_REDIRECT_URI,
                client_id=self.OAUTH_CLIENT_ID,
                client_secret=self.OAUTH_CLIENT_SECRET,
                scope=["api"],
                response_type="code",
            )
