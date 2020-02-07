from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler

class UserObject:
    def get_current_user(self):
        email = self.get_secure_cookie('user')
        name = self.get_secure_cookie('user_name')
        is_admin = self.get_secure_cookie('is_admin')

        if email is None or name is None or is_admin is None:
            return None
        ret = {
            'email': email.decode('utf-8'),
            'name': name.decode('utf-8'),
            'is_admin': is_admin.decode('utf-8')
        }
        print(ret)
        return ret

class BaseHandler(UserObject, RequestHandler):
    pass

class BaseWSHandler(UserObject, WebSocketHandler):
    pass

__all__ = ['BaseHandler', 'BaseWSHandler']
