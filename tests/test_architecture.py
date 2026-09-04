"""Guards the boundary between the integration and the communication layer.

Home Assistant expects the whole device communication to live in a separate
library. ``e3dc_rscp_api`` is that library: the integration must not know how
the device is talked to, and the library must not know that it is used from
Home Assistant.
"""

from pathlib import Path
import sys

custom_components_path = (
    Path(__file__).parent.parent.parent.parent / "config" / "custom_components"
)
sys.path.insert(0, str(custom_components_path))

import ast

import e3dc_rscp_connect

INTEGRATION_ROOT = Path(e3dc_rscp_connect.__file__).parent
API_PACKAGE = "e3dc_rscp_api"
API_ROOT = INTEGRATION_ROOT / API_PACKAGE


def imported_modules(path: Path) -> set[str]:
    """Top level module names imported by the given source file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.add(node.module.split(".")[0])

    return modules


def integration_sources() -> list[Path]:
    """All integration files outside of the communication library."""
    return [
        path for path in INTEGRATION_ROOT.rglob("*.py") if API_ROOT not in path.parents
    ]


def api_sources() -> list[Path]:
    """All files of the communication library."""
    return list(API_ROOT.rglob("*.py"))


def test_both_sides_have_sources():
    """Guard the guards: a wrong root would make every test below pass."""
    assert integration_sources()
    assert api_sources()


def test_integration_does_not_import_the_rscp_protocol():
    offenders = [
        path.relative_to(INTEGRATION_ROOT).as_posix()
        for path in integration_sources()
        if "rscp_lib" in imported_modules(path)
    ]
    assert offenders == [], (
        f"RSCP protocol imports belong in {API_PACKAGE}: {offenders}"
    )


def test_integration_does_not_mention_rscp_tags():
    offenders = [
        path.relative_to(INTEGRATION_ROOT).as_posix()
        for path in integration_sources()
        if "TAG_" in path.read_text(encoding="utf-8")
    ]
    assert offenders == [], f"RSCP tags belong in {API_PACKAGE}: {offenders}"


def test_api_does_not_import_home_assistant():
    offenders = [
        path.relative_to(API_ROOT).as_posix()
        for path in api_sources()
        if "homeassistant" in imported_modules(path)
    ]
    assert offenders == [], (
        f"{API_PACKAGE} must stay usable outside Home Assistant: {offenders}"
    )


def test_api_public_surface_is_importable():
    """Everything the integration needs comes from the package itself."""
    from e3dc_rscp_connect import e3dc_rscp_api

    for name in e3dc_rscp_api.__all__:
        assert hasattr(e3dc_rscp_api, name), f"{name} is not exported"
