import os
import json

from tornado.web import authenticated
from tornado import web, ioloop

from nojava_ipmi_kvm.kvm import start_kvm_container
from nojava_ipmi_kvm.config import config, DEFAULT_CONFIG_FILEPATH
from nojava_ipmi_kvm import utils

from login_handler import IFFLoginOAuth2Handler
from basehandler import BaseHandler, BaseWSHandler

WEBAPP_PORT = int(os.environ["WEBAPP_PORT"])
WEBAPP_BASE = os.environ['WEBAPP_BASE']
VNC_PORT_START = int(os.environ.get('VNC_PORT_START', 8800))
VNC_PORT_END = int(os.environ.get('VNC_PORT_END', 8900))
external_vnc_dns = os.environ.get('EXTERNAL_VNC_DNS', 'localhost')

config.read_config(DEFAULT_CONFIG_FILEPATH)
used_ports = []

class MainHandler(BaseHandler):
    @authenticated
    def get(self):
        self.render(
            "index.tpl",
            title="Remote KVM via WebVNC",
            user=self.get_current_user(),
            servers=config.get_servers(),
            base_uri=WEBAPP_BASE,
            websocket_uri = "ws" + WEBAPP_BASE[4:]
        )

class KVMHandler(BaseWSHandler):
    _instance_counter = 0

    def open(self):
        print("WebSocket opened")
        self._current_session = None
        self._vnc_port = 0
        self._current_user = self.get_current_user()

    def on_message(self, msg):
        print("WS said: " + msg)

        if self._current_user is None:
            return self.write_message({
                'action': 'login',
                'url': '/auth/ifflogin'
            })

        try:
            msg = json.loads(msg)
        except json.decoder.JSONDecodeError:
            return self.write_message({
                'action': 'notice',
                'message': 'Invalid json received'
            })

        if 'action' in msg:
            if msg['action'] == 'connect':
                if self._current_session is not None:
                    return self.write_message({
                        'action': 'notice',
                        'message': 'Already connected to a kvm!'
                    })

                server = msg['server']
                password = msg['password']
                print('Connecting to ' + server)

                if server not in config.get_servers():
                    return self.write_message({
                        'action': 'notice',
                        'message': 'The specified hostname is not valid.',
                        'refresh': True
                    })
                host_config = config[server]

                vnc_port = 1;
                for p in range(VNC_PORT_START, VNC_PORT_END):
                    if p not in used_ports:
                        self._vnc_port = p
                        vnc_port = p
                        used_ports.append(p)
                        break
                else:
                    return self.write_message({
                        'action': 'notice',
                        'message': 'No unused port available. Please notify admins.',
                        'refresh': True
                    })

                self._current_session = start_kvm_container(
                    host_config.full_hostname,
                    host_config.login_user,
                    password,
                    host_config.login_endpoint,
                    host_config.download_endpoint,
                    host_config.allow_insecure_ssl,
                    host_config.user_login_attribute_name,
                    host_config.password_login_attribute_name,
                    host_config.java_version,
                    host_config.session_cookie_key,
                    external_vnc_dns,
                    self._vnc_port,
                )
                return self.write_message({
                    'action': 'connected',
                    'url': self._current_session.url
                })

        self.write_message({
            'action': 'notice',
            'message': 'Invalid msg received',
            'source': msg
        })

    def on_close(self):
        print("WS closed")
        if self._current_session is not None:
            used_ports.remove(self._vnc_port)
            self._current_session.kill_process()

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
    }
    return web.Application(
        [
            web.url(r"/oauth/login", IFFLoginOAuth2Handler),
            web.url(r"/", MainHandler),
            web.url(r"/kvm", KVMHandler),
        ],
        **settings
    )

if __name__ == "__main__":
    APP = make_app()
    APP.listen(WEBAPP_PORT)
    print("Started app on port {}".format(WEBAPP_PORT))
    ioloop.IOLoop.current().start()
