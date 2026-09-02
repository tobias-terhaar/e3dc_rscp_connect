"""Tests for the SSDP device description parsing in config_flow.py."""

from pathlib import Path
import sys

custom_components_path = (
    Path(__file__).parent.parent.parent.parent / "config" / "custom_components"
)
sys.path.insert(0, str(custom_components_path))

from e3dc_rscp_connect.config_flow import parse_rscp_port

DEVICE_DESCRIPTION = """<?xml version="1.0"?>
<root xmlns="urn:schemas-upnp-org:device-1-0">
  <specVersion><major>1</major><minor>0</minor></specVersion>
  <device>
    <friendlyName>S10-742210004447</friendlyName>
    <UDN>S10-742210004447</UDN>
    <deviceType>urn:schemas-upnp-org:device:HVAC_System:1</deviceType>
    <manufacturer>E3DC</manufacturer>
    <serialNumber>S10-742210004447</serialNumber>
    <serviceList>
      <service name="RSCP_SERVICE_PROVIDER">
        <ENCRYPTION>AES</ENCRYPTION>
        <INTERFACE>ETH</INTERFACE>
        <PORT>5033</PORT>
        <PROTOCOL>TCP</PROTOCOL>
      </service>
      <service name="IModBusService">
        <INTERFACE>ETH</INTERFACE>
        <PORT>502</PORT>
        <PROTOCOL>TCP</PROTOCOL>
      </service>
    </serviceList>
  </device>
</root>
"""


def test_parse_rscp_port_returns_rscp_service_port():
    assert parse_rscp_port(DEVICE_DESCRIPTION) == 5033


def test_parse_rscp_port_ignores_other_services():
    xml = DEVICE_DESCRIPTION.replace('name="RSCP_SERVICE_PROVIDER"', 'name="Other"')
    assert parse_rscp_port(xml) is None


def test_parse_rscp_port_handles_custom_port():
    xml = DEVICE_DESCRIPTION.replace("<PORT>5033</PORT>", "<PORT>5034</PORT>")
    assert parse_rscp_port(xml) == 5034


def test_parse_rscp_port_without_namespace():
    xml = DEVICE_DESCRIPTION.replace(' xmlns="urn:schemas-upnp-org:device-1-0"', "")
    assert parse_rscp_port(xml) == 5033


def test_parse_rscp_port_with_missing_port_element():
    xml = DEVICE_DESCRIPTION.replace("<PORT>5033</PORT>", "")
    assert parse_rscp_port(xml) is None


def test_parse_rscp_port_with_non_numeric_port():
    xml = DEVICE_DESCRIPTION.replace("<PORT>5033</PORT>", "<PORT>abc</PORT>")
    assert parse_rscp_port(xml) is None


def test_parse_rscp_port_with_invalid_xml():
    assert parse_rscp_port("not xml at all <<<") is None


def test_parse_rscp_port_with_empty_document():
    assert parse_rscp_port("") is None
