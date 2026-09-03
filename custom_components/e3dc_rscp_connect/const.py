"Constant definitions for e3dc rscp connect."

DOMAIN = "e3dc_rscp_connect"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_KEY = "key"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_LOGIN_TYPE = "login_type"

DEFAULT_PORT = 5033
DEFAULT_UPDATE_INTERVAL = 10

# Login against the device with the fixed local user, or with E3/DC portal
# credentials. The local user always authenticates as LOCAL_USERNAME.
LOGIN_TYPE_LOCAL = "local"
LOGIN_TYPE_PORTAL = "portal"
LOCAL_USERNAME = "local.user"

# Name of the service element in the UPnP device description that carries the
# RSCP port of the device.
RSCP_SERVICE_NAME = "RSCP_SERVICE_PROVIDER"
