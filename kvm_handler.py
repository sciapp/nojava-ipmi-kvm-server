import json, logging, os

try:
    from typing import List
except ImportError:
    pass

from nojava_ipmi_kvm.kvm import (
    start_kvm_container,
    WebserverNotReachableError,
    DockerNotInstalledError,
    DockerNotCallableError,
    DockerPortNotReadableError,
    DockerTerminatedError,
    HTML5KvmViewer,
    JavaKvmViewer,
)
from nojava_ipmi_kvm.config import config, HTML5HostConfig
from nojava_ipmi_kvm import utils
from tornado.websocket import WebSocketError
from basehandler import BaseWSHandler

WEB_PORT_START = int(os.environ.get("WEB_PORT_START", 8800))
WEB_PORT_END = int(os.environ.get("WEB_PORT_END", 8900))
external_web_dns = os.environ.get("EXTERNAL_WEB_DNS", "localhost")
HTML5_AUTHORIZATION = os.environ.get("HTML5_AUTHORIZATION", "disabled")
JAVA_IFRAME_PATH_FORMAT = os.environ.get("JAVA_IFRAME_PATH_FORMAT", "{url}")
HTML5_IFRAME_PATH_FORMAT = os.environ.get("HTML5_IFRAME_PATH_FORMAT", "{url}")
HTML5_SUBDIR_FORMAT = os.environ.get("HTML5_SUBDIR_FORMAT", "")

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

used_ports: List[int] = []


class KVMHandler(BaseWSHandler):
    def open(self):
        self._current_session = None
        self._web_port = 0
        self._current_user = self.get_current_user()
        self._connecting = False
        self._is_closed = False

        if self._current_user is None or not self._current_user["is_admin"]:
            return self.close(code=401, reason="Unauthorized")

        logging.info("Websocket opened by %s", self._current_user["name"])

    async def on_message(self, msg):
        logging.info("Websocket from %s said %s", self._current_user["name"], msg)

        try:
            msg = json.loads(msg)
        except json.decoder.JSONDecodeError:
            return self.write_message({"action": "notice", "message": "Invalid json received"})

        if "action" in msg:
            if msg["action"] == "connect":
                if self._connecting:
                    return self.write_message({"action": "notice", "message": "Already connected to a kvm!"})
                self._connecting = True

                started = False
                server = msg["server"]
                password = msg["password"]
                resolution = msg["resolution"] if "resolution" in msg else None
                logging.info("%s wants to connect to %s with res %s", self._current_user["name"], server, resolution)

                if server not in config.get_servers():
                    return self.write_message(
                        {"action": "notice", "message": "The specified hostname is not valid.", "refresh": True}
                    )
                host_config = config[server]

                web_port = 1
                for p in range(WEB_PORT_START, WEB_PORT_END):
                    if p not in used_ports:
                        self._web_port = p
                        web_port = p
                        used_ports.append(p)
                        break
                else:
                    return self.write_message(
                        {
                            "action": "notice",
                            "message": "No unused port available. Please notify admins.",
                            "refresh": True,
                        }
                    )

                def send_log_message(msg, *args, **kwargs):
                    if self._is_closed:
                        return
                    self.write_message({"action": "log", "message": msg if len(args) == 0 else msg % args})

                try:
                    authorization_key = None
                    authorization_value = None
                    if isinstance(host_config, HTML5HostConfig):
                        if HTML5_AUTHORIZATION == "generate":
                            authorization_key = "kvm_auth_" + self._web_port
                            authorization_value = utils.generate_temp_password(20)
                        elif HTML5_AUTHORIZATION == "use_server":
                            authorization_key = "is_admin"
                            authorization_value = self.get_cookie("is_admin")
                        elif ":" in HTML5_AUTHORIZATION:
                            authorization_key = HTML5_AUTHORIZATION.split(":")[0]
                            authorization_value = HTML5_AUTHORIZATION.split(":", 1)[1]

                    sess = self._current_session = await start_kvm_container(
                        host_config=host_config,
                        login_password=password,
                        external_vnc_dns=external_web_dns,
                        docker_port=self._web_port,
                        additional_logging=send_log_message,
                        selected_resolution=resolution,
                        authorization_key=authorization_key,
                        authorization_value=authorization_value,
                        subdir=HTML5_SUBDIR_FORMAT.format(
                            external_web_dns=external_web_dns, port=self._web_port, hostname=host_config.full_hostname
                        ),
                    )
                    started = True
                except WebSocketError as ex:
                    logging.exception("Could not start KVM container: WebSocket closed unexpectedly?")
                    return
                except Exception as ex:
                    logging.exception("Could not start KVM container: %s" % ex)
                    return self.write_message({"action": "error", "message": str(ex)})
                finally:
                    try:
                        if not started:
                            used_ports.remove(web_port)
                            self._current_session.kill_process()
                    except:
                        pass

                if isinstance(sess, HTML5KvmViewer):
                    return self.write_message(
                        {
                            "action": "connected",
                            "url": HTML5_IFRAME_PATH_FORMAT.format(
                                url=sess.url,
                                external_web_dns=external_web_dns,
                                port=sess.web_port,
                                subdir=sess.subdir,
                                authorization_key=sess.authorization_key,
                                authorization_value=sess.authorization_value,
                                html5_endpoint=sess.html5_endpoint,
                            ),
                            "authorization_key": sess.authorization_key,
                            "authorization_value": sess.authorization_value,
                        }
                    )
                else:
                    return self.write_message(
                        {
                            "action": "connected",
                            "url": JAVA_IFRAME_PATH_FORMAT.format(
                                url=sess.url,
                                external_web_dns=external_web_dns,
                                port=sess.web_port,
                                password=sess.vnc_password,
                            ),
                        }
                    )

        self.write_message(
            {"action": "notice", "message": "Invalid msg received", "source": msg, "user": self.get_current_user()}
        )

    def on_close(self):
        logging.info("WS from %s closed", None if self._current_user is None else self._current_user["name"])
        self._is_closed = True
        if self._current_session is not None:
            used_ports.remove(self._web_port)
            self._current_session.kill_process()


__all__ = ["KVMHandler"]
