import os
import json
import logging

from tornado.web import authenticated
from tornado import web, ioloop

from nojava_ipmi_kvm.kvm import start_kvm_container, WebserverNotReachableError, DockerNotInstalledError, DockerNotCallableError, DockerPortNotReadableError, DockerTerminatedError
from nojava_ipmi_kvm.config import config, DEFAULT_CONFIG_FILEPATH
from nojava_ipmi_kvm import utils

from login_handler import IFFLoginOAuth2Handler
from basehandler import BaseHandler, BaseWSHandler, authorized

WEBAPP_PORT = int(os.environ["WEBAPP_PORT"])
WEBAPP_BASE = os.environ['WEBAPP_BASE']
VNC_PORT_START = int(os.environ.get('VNC_PORT_START', 8800))
VNC_PORT_END = int(os.environ.get('VNC_PORT_END', 8900))
external_vnc_dns = os.environ.get('EXTERNAL_VNC_DNS', 'localhost')
CONFIG_PATH = os.environ.get('KVM_CONFIG_PATH', DEFAULT_CONFIG_FILEPATH)
IFRAME_PATH_FORMAT = os.environ.get('IFRAME_PATH_FORMAT', '{url}')

config.read_config(CONFIG_PATH)
used_ports = []

class MainHandler(BaseHandler):
    @authenticated
    @authorized
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
        self._current_session = None
        self._vnc_port = 0
        self._current_user = self.get_current_user()
        self._connecting = False
        self._is_closed = False

        if self._current_user is None or not self._current_user['is_admin']:
            return self.close(code=401, reason="Unauthorized")

        logging.info("Websocket opened by %s", self._current_user['name'])

    async def on_message(self, msg):
        logging.info("Websocket from %s said %s", self._current_user['name'], msg)

        try:
            msg = json.loads(msg)
        except json.decoder.JSONDecodeError:
            return self.write_message({
                'action': 'notice',
                'message': 'Invalid json received'
            })

        if 'action' in msg:
            if msg['action'] == 'connect':
                if self._connecting:
                    return self.write_message({
                        'action': 'notice',
                        'message': 'Already connected to a kvm!'
                    })
                self._connecting = True

                server = msg['server']
                password = msg['password']
                logging.info('%s wants to connect to %s', self._current_user['name'], server)

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

                def send_log_message(msg, *args, **kwargs):
                    if self._is_closed:
                        return
                    self.write_message({
                        'action': 'log',
                        'message': msg if len(args)  == 0 else msg % args
                    })

                try:
                    sess = self._current_session = await start_kvm_container(
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
                        send_log_message,
                    )
                except (
                    WebserverNotReachableError,
                    DockerNotInstalledError,
                    DockerNotCallableError,
                    IOError,
                    DockerTerminatedError,
                    DockerPortNotReadableError
                ) as ex:
                    logging.exception("Could not start KVM container")
                    return self.write_message({
                        'action': 'error',
                        'message': str(ex)
                    })

                return self.write_message({
                    'action': 'connected',
                    'url': IFRAME_PATH_FORMAT.format(
                        url = sess.url,
                        external_vnc_dns = sess.external_vnc_dns,
                        port = sess.vnc_web_port,
                        password = sess.vnc_password)
                })

        self.write_message({
            'action': 'notice',
            'message': 'Invalid msg received',
            'source': msg,
            'user': self.get_current_user()
        })

    def on_close(self):
        logging.info("WS from %s closed", None if self._current_user is None else self._current_user['name'])
        self._is_closed = True
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
