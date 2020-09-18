from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler


def authorized(func):
    def wrapper(self, *args):
        user = self.get_current_user()
        if user is None or not user["is_admin"]:
            return self.render("not_authorized.tpl", user=user)
        return func(self, *args)

    return wrapper


class UserObject:
    def get_current_user(self):
        email = self.get_secure_cookie("user")
        name = self.get_secure_cookie("user_name")
        is_admin = self.get_secure_cookie("is_admin")

        if email is None or name is None or is_admin is None or not is_admin:
            return None
        ret = {
            "email": email.decode("utf-8"),
            "name": name.decode("utf-8"),
            "is_admin": is_admin.decode("utf-8") == "on",
        }
        return ret


class BaseHandler(UserObject, RequestHandler):
    pass


class BaseWSHandler(UserObject, WebSocketHandler):
    pass


__all__ = ["authorized", "BaseHandler", "BaseWSHandler"]
