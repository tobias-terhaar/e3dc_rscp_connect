"""Tests that every translation key used in the code exists in every language."""

import json
import re
import sys
from pathlib import Path

import pytest

# Add custom_components to path
custom_components_path = (
    Path(__file__).parent.parent.parent.parent / "config" / "custom_components"
)
sys.path.insert(0, str(custom_components_path))

INTEGRATION = (
    Path(__file__).parent.parent / "custom_components" / "e3dc_rscp_connect"
)
LANGUAGES = ("en", "de", "nl", "fr")


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def strings():
    return _load(INTEGRATION / "strings.json")


@pytest.fixture(scope="module")
def translations():
    return {
        lang: _load(INTEGRATION / "translations" / f"{lang}.json")
        for lang in LANGUAGES
    }


def _flatten(value, prefix=""):
    """All leaf paths of a nested dict, so two files can be compared."""
    if isinstance(value, dict):
        keys = set()
        for k, v in value.items():
            keys |= _flatten(v, f"{prefix}.{k}" if prefix else k)
        return keys
    return {prefix}


def _keys_used_in(filename, attribute):
    """Collects the literal translation keys assigned in a source file."""
    source = (INTEGRATION / filename).read_text(encoding="utf-8")
    return set(re.findall(rf'{attribute}\s*=\s*"([a-z0-9_]+)"', source))


def _platform_keys(platform_file):
    """The keys passed as the third argument of the entity constructors."""
    source = (INTEGRATION / platform_file).read_text(encoding="utf-8")
    return set(re.findall(r'^\s+"([a-z0-9_]+)",$', source, re.MULTILINE))


@pytest.mark.parametrize("lang", LANGUAGES)
def test_translation_has_the_same_keys_as_strings(lang, strings, translations):
    """A missing key means the English text leaks into a translated UI."""
    assert _flatten(translations[lang]) == _flatten(strings)


def test_every_sensor_key_is_translated(strings):
    """Entity names come from the translations now, so they must all exist."""
    translated = set(strings["entity"]["sensor"])

    missing = _platform_keys("sensor.py") - translated
    assert missing == set()


@pytest.mark.parametrize(
    "source,platform",
    [
        ("entities/cp_state_sensor.py", "sensor"),
        ("entities/sg_ready_sensor.py", "sensor"),
        ("entities/emergency_power_sensor.py", "sensor"),
        ("entities/state_of_charge_sensor.py", "sensor"),
        ("entities/sun_mode_sensor.py", "select"),
        ("entities/wallbox_current_number.py", "number"),
        ("entities/battery_remote_control.py", "number"),
    ],
)
def test_fixed_translation_keys_exist(source, platform, strings):
    used = _keys_used_in(source, "_attr_translation_key")
    available = set(strings["entity"][platform]) | set(
        strings["entity"]["switch"]
    )

    assert used
    assert used <= available


def test_device_state_keys_exist(strings):
    """Those keys are built from the device name at runtime."""
    for key in ("battery_state", "battery_update_state"):
        assert key in strings["entity"]["sensor"]
        assert "{index}" in strings["entity"]["sensor"][key]["name"]


@pytest.mark.parametrize("lang", LANGUAGES)
def test_placeholders_survive_translation(lang, translations):
    """A dropped {index} would break the name of the battery sensors."""
    sensors = translations[lang]["entity"]["sensor"]

    for key in ("battery_state", "battery_update_state"):
        assert "{index}" in sensors[key]["name"]


@pytest.mark.parametrize("lang", LANGUAGES)
def test_flow_placeholders_survive_translation(lang, translations):
    discovery = translations[lang]["config"]["step"]["discovery_confirm"]

    for placeholder in ("{name}", "{host}", "{port}"):
        assert placeholder in discovery["description"]


@pytest.mark.parametrize("lang", LANGUAGES)
def test_texts_are_actually_translated(lang, strings, translations):
    """Guards against a language file that is just a copy of the English one."""
    if lang == "en":
        return

    english = strings["entity"]["sensor"]["state_of_charge"]["name"]
    assert translations[lang]["entity"]["sensor"]["state_of_charge"]["name"] != english
