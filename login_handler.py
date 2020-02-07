import os

import ldap3
from login_mixin import IFFLoginOAuth2Mixin
from basehandler import BaseHandler

class IFFLoginOAuth2Handler(BaseHandler, IFFLoginOAuth2Mixin): #BaseRequestHandler, IFFLoginOAuth2Mixin):
    """
    Handler for authorization at ifflogin
    """
    IFFLOGIN_CLIENT_ID = os.environ["IFFLOGIN_ID"]
    IFFLOGIN_CLIENT_SECRET = os.environ["IFFLOGIN_CLIENT_SECRET"]
    IFFLOGIN_REDIRECT_URI = "{}/oauth/login".format(os.environ['WEBAPP_BASE'])
    async def get(self):
        """
        Cheks wether the user is logged in or not and handles authentication
        """
        if self.get_argument("code", ""):
            user_data = await self.get_authenticated_user(self.get_argument("code", ""))
            # Use user_data to find the user in your user database or use their data directly
            email = user_data["email"]
            uid = user_data["username"]
            self.set_secure_cookie("user", email)
            self.set_secure_cookie("user_name", uid)
            try:
                server = ldap3.Server(
                    'ldaps://ldap.iff.kfa-juelich.de', use_ssl=True, get_info=ldap3.ALL)
                fallback_server = ldap3.Server(
                    'ldaps://ldaps.iff.kfa-juelich.de', use_ssl=True, get_info=ldap3.ALL)
                base_dn = 'cn=users,cn=accounts,dc=iff,dc=kfa-juelich,dc=de'
                user_dn = 'uid=max,cn=users,cn=accounts,dc=iff,dc=kfa-juelich,dc=de'
                password = os.environ['LDAP_PASSWORD']
                connection = ldap3.Connection(
                    [server, fallback_server], user=user_dn, password=password, auto_bind=True)
                reader = ldap3.Reader(connection, ldap3.ObjectDef('posixaccount', connection), base_dn,
                                      '(&(objectClass=inetOrgPerson)(mail={email})(uid={uid}))'.format(email=email, uid=uid))
                user_infos = reader.search()
                self.set_secure_cookie("is_admin", "off")
                if user_infos:
                    for user in user_infos:
                        if 'gidNumber' in user and user['gidNumber'] == 60400:
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
                redirect_uri=self.IFFLOGIN_REDIRECT_URI,
                client_id=self.IFFLOGIN_CLIENT_ID,
                client_secret=self.IFFLOGIN_CLIENT_SECRET,
                scope=["api"],
                response_type="code",
            )
