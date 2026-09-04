![Tests](https://github.com/tobias-terhaar/e3dc_rscp_connect/actions/workflows/tests.yml/badge.svg)

# E3DC RSCP Connect

<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=tobias-terhaar&repository=e3dc_rscp_connect"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open in HACS" /></a>

A [Home Assistant](https://www.home-assistant.io/) custom integration for **E3/DC** energy storage systems (S10 battery storage). It communicates directly with the device on your local network using the proprietary **RSCP** (Remote Storage Control  Protocol), giving you access to your battery storage, connected wallboxes and power meters — without going through the E3/DC cloud.

## Features

- Autodetection of connected storage systems and auto commissioning of all wallboxes connected to the storage system.
- Local polling over TCP (port `5033`) using Rijndael-256 encrypted RSCP frames — no cloud dependency.
- Live readings for the main storage system:
  - State of charge, battery power, battery state
  - PV production, grid import/export, house consumption
  - Energy counters (daily / total)
  - Emergency power status
  - Device state and firmware update state
- Wallbox support:
  - Charge power and charging state
  - Adjustable charging current
  - for every connected wallbox
- SG-Ready heat pump signal
- Sun mode / battery remote control
- UI-based configuration (no YAML required) with an options flow to update credentials and polling interval after setup.

## Requirements

- Home Assistant **2025.10.0** or newer
- An E3/DC S10 system reachable on your local network
- **RSCP password** (set on the device under `Personalize → User profile → RSCP password`)
- A E3/DC portal user account (username/email + password) or a configured password for local.user on the storage (`Personalize  → User profile → Password for offline RSCP User` )

## Installation

### Via HACS (recommended)

Since June 2026 E3DC RSCP Connect has been integrated into the default store of HACS.

One-Click Installation: <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=tobias-terhaar&repository=e3dc_rscp_connect"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open in HACS" /></a>

1. In Home Assistant open **HACS → Integrations**.
2. Search for **E3DC RSCP Connect**
3. Install **E3DC RSCP connect** and restart Home Assistant.

### Manual

1. Copy the `custom_components/e3dc_rscp_connect` folder into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

Add the integration via **Settings → Devices & services → Add integration → E3DC RSCP connect**
and provide:

| Field       | Description                                          | Default      |
|-------------|------------------------------------------------------|--------------|
| login_type  | *Local user* or *Portal user*                        | Local user   |
| host        | IP address or hostname of your E3/DC system          | —            |
| port        | RSCP TCP port                                        | `5033`       |
| username    | Your E3/DC portal email address (portal login only)  | —            |
| password    | Password of the portal or the local user             | —            |
| key         | RSCP password configured on the device               | —            |

The login method is a dropdown on the form itself, so it can be changed at any point before
submitting — also when you come back to a setup you left half finished:

- **Local user** — authenticates as the fixed user `local.user`; leave the username empty.
- **Portal user** — authenticates with your E3/DC portal credentials; the username is required.

Devices found via SSDP discovery are offered the same choice; host and port are taken from the
device's UPnP description.

The options flow lets you change these values and the polling interval (default: 10 seconds) without removing the integration.

## Architecture

All device communication lives in `e3dc_rscp_api`, a self-contained package with no Home Assistant
imports that is meant to become a standalone library. The integration above it never sees an RSCP
tag, frame or connection — it only reads the plain dataclasses the api returns.

This has been introduced to be prepared for a potential switch from a HACS integration to a core integration.

```
Home Assistant Config Entry
    ↓
E3dcRscpCoordinator (DataUpdateCoordinator)          ── integration
    ├─ polls every 10s (configurable)
    └─ device info refresh every 60 min
    ↓                                        ↑ plain dataclasses
─────────────────────────────────────────────────────────────────
RscpClient                                           ── e3dc_rscp_api
    ├─ RscpConnection  →  RscpEncryption  →  RscpFrame / RscpValue
    └─ RscpHandlerPipeline
         ├─ StorageRscpModel   →  StorageDataModel
         ├─ WallboxRscpModel   →  WallboxDataModel
         └─ SgReadyRscpModel   →  SgReadyDataModel
              ↓
         Sensor / Select / Number Entities
```

- **Coordinator** (`coordinator.py`) drives all periodic fetches; entities subscribe through `CoordinatorEntity`.
- **Api boundary**: everything the integration needs is re-exported from `e3dc_rscp_api/__init__.py` — the client, the data models, and the `E3dcRscpError` hierarchy. Errors of the underlying protocol never leave the package. `tests/test_architecture.py` fails if the integration imports `rscp_lib` or mentions an RSCP tag, or if the api imports Home Assistant.
- **Handler pipeline** (`e3dc_rscp_api/model/RscpHandlerPipeline.py`) routes raw RSCP frames to registered device models. Adding a new device type is a matter of implementing `RscpModelInterface` and registering it with the pipeline.
- **RSCP protocol** is provided by the [`rscp_lib`](https://pypi.org/project/rscp_lib/) PyPI package — magic `0xDCE3`, timestamp header, variable-length binary frames, Rijndael-256 CBC encryption with IV chaining.

### Repository layout

| Path | Purpose |
|------|---------|
| `custom_components/e3dc_rscp_connect/` | Integration root |
| `├─ e3dc_rscp_api/` | Communication layer (future standalone library) |
| `│  ├─ client.py` | High-level RSCP client: connect, request, dispatch |
| `│  ├─ exceptions.py` | Error hierarchy exposed to the integration |
| `│  └─ model/` | Tag handling per device type and the resulting data models |
| `├─ entities/` | Entity base class and sensor / select / number types |
| `├─ sensor.py`, `select.py`, `number.py`, `switch.py` | HA platform entry points |
| `├─ coordinator.py` | Polling coordinator |
| `└─ config_flow.py` | UI config & options flow |
| `tests/` | Unit tests (mocked, no device required) |

## Development

Home Assistant's `hassfest` validator runs automatically on pull requests via `.github/workflows/hassfest.yml` and checks `manifest.json` and the integration structure.

### Dependencies

- [`rscp_lib`](https://pypi.org/project/rscp_lib/) — RSCP protocol implementation (connection, encryption, framing, tags); pinned in `manifest.json`, installed by Home Assistant at runtime.
- `homeassistant` — provided by the Home Assistant runtime

## Contributing

Bug reports and pull requests are welcome on [GitHub](https://github.com/tobias-terhaar/e3dc_rscp_connect/issues). When adding support for a new device type, implement `RscpModelInterface` and register the handler with `RscpHandlerPipeline` — existing models in `model/` are good templates.

## Disclaimer

This integration is not affiliated with or endorsed by HagerEnergy GmbH. "E3/DC" and "S10" are trademarks of their respective owners. Use at your own risk.

## License

Released under the [MIT License](LICENSE).
