# NoJava-IPMI-KVM-Server

## Introduction

NoJava-IPMI-KVM-Server is a python-based server designed to centrally provide instances of [sciapp/nojava-ipmi-kvm](https://github.com/sciapp/nojava-ipmi-kvm) via the browser. This means that no installation of either Java or nojava-ipmi-kvm is required on the administrator's machine.
A typical usage might be:
1. Optional login using oauth, optionally secured by ldap group membership
2. Selection of desired target machine, resolution and prompt for required kvm password
3. Start of a docker container using nojava-ipmi-kvm to provide console access via novnc's web interface/the kvm's html5 interface
4. The docker container is stopped and deleted after the administrator closes the tab/window.

## Installation

NoJava-IPMI-KVM-Server can either be installed using Git or installed as a docker container.

### Standalone using git:
 - Install Python3 and pip
 - [Install Docker](https://www.docker.com/) on the server if not done already.
 - Ensure the user that shall run nojava-ipmi-kvm-server has permissions to access docker (usually being in the `docker` group suffices)
 - Clone the repository, f.e. `git clone https://github.com/sciapp/nojava-ipmi-kvm-server.git` into a directory of your choice
 - Install the dependencies, f.e. `pip install -r requirements.txt`
 - Write a configuration file for nojava-ipmi-kvm (in [this](https://github.com/sciapp/nojava-ipmi-kvm/blob/master/README.md#configuration-file) format) and place it somewhere accessible
 - Start the service using `python3 main.py` with the required env variables set.


### As a container:
 - Write a configuration file for nojava-ipmi-kvm (in [this](https://github.com/sciapp/nojava-ipmi-kvm/blob/master/README.md#configuration-file) format) and place it somewhere accessible
 - Start a docker container based on the `sciapp/nojava-ipmi-kvm-server` image with the required env variables set and the configuration file mounted into the container. Make sure to mount the docker socket into the container.

Example:

```bash
docker run -d \
           --restart always \
           --name nojava-ipmi-kvm-server \
           --env-file ~/nojava-ipmi-kvm.envfile \
           -v /var/run/docker.sock:/var/run/docker.sock \
           -v ~/nojava-ipmi-kvmrc.yaml:/nojava-ipmi-kvmrc.yaml \
           sciapp/nojava-ipmi-kvm-server:latest
```

## Configuration

### Authentication
Three authentication options are available:
1. No authentication. This requires that no `OAUTH_*` or `LDAP_*` option is set
2. OAUTH-only authentication. This requires that all `OAUTH_*` options are set while no `LDAP_*` option is set
3. OAUTH authentication + LDAP authorization. This requires that all `OAUTH_*` and all `LDAP_*` (except `LDAP_FALLBACK_SERVER`) options are set. This requires that signed in users are in a specific LDAP group.

LDAP-Identification is performed using the email.

### Environment variables
| Name                       | Description                                                                                                                                                         | Example                                   |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| `LOGLEVEL`                 | Log level to use (one of `DEBUG`, `INFO`, `WARNING` (default), `ERROR`, `CRITICAL`)                                                                                 | `INFO`                                    |
| `KVM_CONFIG_PATH`          | Absolute path to a configuration file for nojava-ipmi-kvm                                                                                                           | `/data/nojava-ipmi-kvmrc.yaml`            |
| `WEBAPP_BASE`              | The final address the service is published                                                                                                                          | `https://nojava-ipmi-kvm.corporate.local` |
| `WEBAPP_PORT`              | The port to listen on                                                                                                                                               | `8080`                                    |
| `EXTERNAL_WEB_DNS`         | Custom address for checking availability and passed to `IFRAME_PATH_FORMAT`. Should be set to the external address of the docker host                               | `nojava-ipmi-kvm.corporate.local`         |
| `WEB_PORT_START`           | The first port to be allocated to kvm containers                                                                                                                    | `8800`                                    |
| `WEB_PORT_END`             | The first port outside the range                                                                                                                                    | `8900`                                    |
| `JAVA_IFRAME_PATH_FORMAT`  | This format specifies the iframe url used for java kvm hosts, useful if you have a reverse proxy                                                                    | (see section [IFRAME_PATH_FORMAT](#IFRAME_PATH_FORMAT))          |
| `HTML5_IFRAME_PATH_FORMAT` | This format specifies the iframe url used for html5 kvm hosts, useful if you have a reverse proxy                                                                   | (see section [IFRAME_PATH_FORMAT](#IFRAME_PATH_FORMAT))          |
| `HTML5_AUTHORIZATION`      | Authorization cookie required to access html5 consoles. `generate`: auto-generated, `use_server`: Uses the `is_admin` cookie set by server, `[key]:[value]`: Manual | `kvm_authorization:abcdefgh`              |
| `HTML5_SUBDIR_FORMAT`      | Format to generate `{subdirectoy}` value replaced in `rewrites` html5 host config; Parameters: `external_web_dns`, `port`, `hostname`                               | `/{port}`                                 |
| `OAUTH_HOST`               | Base URL of the oauth provider                                                                                                                                      | `https://oauth-provider`                  |
| `OAUTH_CLIENT_ID`          | Client ID of nojava-ipmi-kvm-server-app in oauth provider                                                                                                           | `abcdef...`                               |
| `OAUTH_CLIENT_SECRET`      | Client secret to fit `OAUTH_CLIENT_ID`                                                                                                                              | `abcdef...`                               |
| `LDAP_DEFAULT_SERVER`      | If set, verifies the account authenticated using oauth is in a specific group                                                                                       | `ldap.corporate.local`                    |
| `LDAP_FALLBACK_SERVER`     | If set, defines a fallback server if the default server is undefined                                                                                                | `ldap-fallback.corporate.local`           |
| `LDAP_BASE_DN`             | Base DN to search users in                                                                                                                                          | `cn=users,dc=....`                        |
| `LDAP_USER_DN`             | The account used to login at the ldap server                                                                                                                        | `cn=ipmi-kvm,dc=...`                      |
| `LDAP_PASSWORD`            | The password for `LDAP_USER_DN` account                                                                                                                             | `abcdef...`                               |
| `LDAP_GROUP_DN`            | FQDN of group to search in the `memberOf` property of the authenticated user                                                                                        | `cn=kvm-access,dc=...`                    |

### IFRAME_PATH_FORMAT
You can use the following placeholders within the format string:
| Placeholder             | Description                                                                                 |
| ----------------------- | ------------------------------------------------------------------------------------------- |
| `{url}`                 | Autogenerated url generated using `EXTERNAL_WEB_DNS` and the selected web port              |
| `{external_web_dns}`    | The value of `EXTERNAL_WEB_DNS`                                                             |
| `{port}`                | The port selected for the started container                                                 |
| Java-only Options:      |                                                                                             |
| `{password}`            | Generated VNC password                                                                      |
| HTML5-only Options:     |                                                                                             |
| `{subdir}`              | The subdirectory formatted using `HTML5_SUBDIR_FORMAT`                                      |
| `{authorization_key}`   | The cookie-key used to authorize the user, might be unset/None if authorization is disabled |
| `{authorization_value}` | The cookie-value used to authorize the user.                                                |
| `{html5_endpoint}`      | HTML5-Endpoint configured in `.nojava-ipmi-kvm.yaml`                                        |

Some examples:
- `{url}`: No special network configuration, `EXTERNAL_WEB_DNS` is set to the external address of the docker host
- `https://outside-address/{port}/vnc.html?host={outside-address}&autoconnect=true&password={password}&path={port}/websockify`: Java Example using a reverse proxy proxying WebVNC Ports
- `https://{external_web_dns}/{subdir}{html5_endpoint}`: HTML5 Example using a reverse proxy
