#!/usr/bin/env python3

__version__ = "0.2.2"
__author__ = "M. Heuwes <m.heuwes@fz-juelich.de>"

import os
import json
import logging

from tornado.web import authenticated
from tornado import web, ioloop

from nojava_ipmi_kvm.config import config, DEFAULT_CONFIG_FILEPATH
from nojava_ipmi_kvm import utils

from login_handler import OAuth2LoginHandler
from basehandler import BaseHandler, authorized
from kvm_handler import KVMHandler

WEBAPP_PORT = int(os.environ["WEBAPP_PORT"])
WEBAPP_BASE = os.environ["WEBAPP_BASE"]
CONFIG_PATH = os.environ.get("KVM_CONFIG_PATH", DEFAULT_CONFIG_FILEPATH)
WSPING_INTERVAL = os.environ.get("WSPING_INTERVAL", 5)
WSPING_TIMEOUT = os.environ.get("WSPING_TIMEOUT", 30)

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

config.read_config(CONFIG_PATH)


class MainHandler(BaseHandler):
    @authenticated
    @authorized
    def get(self):
        self.render(
            "index.tpl",
            title="Remote KVM",
            user=self.get_current_user(),
            servers=config.get_servers(),
            base_uri=WEBAPP_BASE,
            websocket_uri="ws" + WEBAPP_BASE[4:],
        )

    @authenticated
    @authorized
    def post(self):
        self.render(
            "index_instant.tpl",
            title="Remote KVM",
            user=self.get_current_user(),
            servers=config.get_servers(),
            base_uri=WEBAPP_BASE,
            websocket_uri="ws" + WEBAPP_BASE[4:],
            server_name=json.dumps(self.get_body_argument("server_name")),
            password=json.dumps(self.get_body_argument("password")),
            resolution=json.dumps(self.get_body_argument("resolution")),
        )


def make_app():
    """
    returns a tornado.web.Application
    """
    settings = {
        "template_path": "templates",
        "static_path": "static",
        "debug": True,
        "cookie_secret": utils.generate_temp_password(32),
        "login_url": "/oauth/login",
        "xsrf_cookies": True,
        "default_handler_class": MainHandler,
        "websocket_ping_interval": WSPING_INTERVAL,
        "websocket_ping_timeout": WSPING_TIMEOUT,
    }
    return web.Application(
        [web.url(r"/oauth/login", OAuth2LoginHandler), web.url(r"/", MainHandler), web.url(r"/kvm", KVMHandler)],
        **settings
    )


if __name__ == "__main__":
    APP = make_app()
    APP.listen(WEBAPP_PORT)
    print("Started app on port {}".format(WEBAPP_PORT))
    ioloop.IOLoop.current().start()
