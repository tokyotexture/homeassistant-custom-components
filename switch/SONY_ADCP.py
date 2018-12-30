"""
Support for Sony ADCP compatible projectors controlled as a swtich using a telnet connection.

For more details about this custom component, please refer to the documentation at
https://github.com/tokyotexture/homeassistant-custom-components
"""
from datetime import timedelta
import logging
import telnetlib
import hashlib

import voluptuous as vol

from homeassistant.components.switch import (
    ENTITY_ID_FORMAT, PLATFORM_SCHEMA, SwitchDevice)
from homeassistant.const import (
    CONF_COMMAND_OFF, CONF_COMMAND_ON, CONF_COMMAND_STATE, CONF_NAME,
    CONF_PORT, CONF_RESOURCE, CONF_SWITCHES, CONF_VALUE_TEMPLATE, CONF_PASSWORD)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

# Set defaults as per ADCP standard
DEFAULT_COMMAND_OFF = "power \"off\""
DEFAULT_COMMAND_ON = "power \"on\""
DEFAULT_COMMAND_STATE = "power_status ?"
DEFAULT_VALUE_TEMPLATE = "{{ value != '\"standby\"' }}"
DEFAULT_NAME = 'Projector'
DEFAULT_PORT = 53595

# Validation of the user's configuration
SWITCH_SCHEMA = vol.Schema({
    vol.Required(CONF_COMMAND_OFF, default=DEFAULT_COMMAND_OFF): cv.string,
    vol.Required(CONF_COMMAND_ON, default=DEFAULT_COMMAND_ON): cv.string,
    vol.Required(CONF_RESOURCE): cv.string,
    vol.Optional(CONF_VALUE_TEMPLATE, default=DEFAULT_VALUE_TEMPLATE): cv.template,
    vol.Optional(CONF_COMMAND_STATE, default=DEFAULT_COMMAND_STATE): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_PASSWORD): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_SWITCHES): vol.Schema({cv.slug: SWITCH_SCHEMA}),
})

# Polling interval for checking on/off (standby) of projector
SCAN_INTERVAL = timedelta(seconds=10)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Find and return projectors controlled by ADCP commands."""
    devices = config.get(CONF_SWITCHES, {})
    switches = []

    for object_id, device_config in devices.items():
        value_template = device_config.get(CONF_VALUE_TEMPLATE)

        if value_template is not None:
            value_template.hass = hass

        switches.append(
            TelnetSwitch(
                hass,
                object_id,
                device_config.get(CONF_RESOURCE),
                device_config.get(CONF_PORT),
                device_config.get(CONF_PASSWORD),
                device_config.get(CONF_NAME, object_id),
                device_config.get(CONF_COMMAND_ON),
                device_config.get(CONF_COMMAND_OFF),
                device_config.get(CONF_COMMAND_STATE),
                value_template
            )
        )

    if not switches:
        _LOGGER.error("No switches added")
        return

    add_entities(switches)


class TelnetSwitch(SwitchDevice):
    """Representation of a projector as a switch, that can be toggled using ADCP commands."""

    def __init__(self, hass, object_id, resource, port, password, friendly_name,
                 command_on, command_off, command_state, value_template):
        """Initialize the switch."""
        self._hass = hass
        self.entity_id = ENTITY_ID_FORMAT.format(object_id)
        self._resource = resource
        self._port = port
        self._password = password
        self._name = friendly_name
        self._state = False
        self._command_on = command_on
        self._command_off = command_off
        self._command_state = command_state
        self._value_template = value_template

    def _encrypt_string(self, hash_string):
        sha_signature = \
            hashlib.sha256(hash_string.encode()).hexdigest()
        return sha_signature

    def _telnet_command(self, command):
        try:
            telnet = telnetlib.Telnet(self._resource, self._port)
            initial_hash = telnet.read_until(b"\r\n", 5).decode('ASCII')
            initial_hash = str.rstrip(initial_hash)

            authenticated = 0
            password = self._password

            if 'NOKEY' in initial_hash:
                authenticated = 1
                _LOGGER.debug(
                'Received NOKEY. No authentication needed.')
            else:
                encrypt_hash = self._encrypt_string(initial_hash + password)
                telnet.write(encrypt_hash.encode('ASCII') + b"\r\n")
                auth_reply = telnet.read_until(b"\r\n", 5).decode('ASCII')
                auth_reply = str.rstrip(auth_reply)
                if 'OK' in auth_reply:
                    authenticated = 1
                    _LOGGER.debug(
                    "Successfully provided password hash and received \"OK\" reply.")
                elif 'err_auth' in auth_reply:
                    if password is None:
                        _LOGGER.error(
                        "Server asked for password authentication, but password has not been set. Auth error.")
                    else:
                        _LOGGER.error(
                        "Authentication error received by server. Most likely incorrect password.")
                else:
                    _LOGGER.error(
                    "Something unexpected happened authenticating.")

            telnet.write(command.encode('ASCII') + b'\r\n')
            response = telnet.read_until(b"\r\n", 5)
            _LOGGER.debug(
                "Client sent command: \"%s\", and server response was: \"%s\"", 
                command.encode('ASCII'), response.decode('ASCII'))
            return response.decode('ASCII').strip()
        except IOError as error:
            _LOGGER.error(
                "Command \"%s\" failed with exception: %s",
                command, repr(error))
            return None

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def should_poll(self):
        """Only poll if we have state command."""
        return self._command_state is not None

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    @property
    def assumed_state(self):
        """Return true if no state command is defined, false otherwise."""
        return self._command_state is None

    def update(self):
        """Update device state."""
        response = self._telnet_command(self._command_state)
        if response:
            rendered = self._value_template \
                .render_with_possible_json_value(response)
            self._state = rendered == "True"
        else:
            _LOGGER.warning(
                "Empty response for command: %s", self._command_state)

    def turn_on(self, **kwargs):
        """Turn the device on."""
        self._telnet_command(self._command_on)
        if self.assumed_state:
            self._state = True

    def turn_off(self, **kwargs):
        """Turn the device off."""
        self._telnet_command(self._command_off)
        if self.assumed_state:
            self._state = False