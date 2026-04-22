# E3DC RSCP Connect

A [Home Assistant](https://www.home-assistant.io/) custom integration for **E3/DC** energy storage systems (S10 battery storage). It communicates directly with the device on your local network using the proprietary **RSCP** (Remote Storage Control  Protocol), giving you access to your battery storage, connected wallboxes and power meters — without going through the E3/DC cloud.

## Features

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

1. In Home Assistant open **HACS → Integrations**.
2. Choose **Custom repositories** and add `https://github.com/tobias-terhaar/e3dc_rscp_connect` as type *Integration*.
3. Install **E3DC RSCP connect** and restart Home Assistant.

### Manual

1. Copy the `custom_components/e3dc_rscp_connect` folder into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

Add the integration via **Settings → Devices & services → Add integration → E3DC RSCP connect** and provide:

| Field    | Description                                          | Default      |
|----------|------------------------------------------------------|--------------|
| host     | IP address or hostname of your E3/DC system          | —            |
| port     | RSCP TCP port                                        | `5033`       |
| username | Your E3/DC portal email address                      | `local.user` |
| password | Your E3/DC portal password                           | —            |
| key      | RSCP password configured on the device               | —            |

The options flow lets you change these values and the polling interval (default: 10 seconds) without removing the integration.

## Architecture

```
Home Assistant Config Entry
    ↓
E3dcRscpCoordinator (DataUpdateCoordinator)
    ├─ polls every 10s (configurable)
    └─ device info refresh every 60 min
         ↓
RscpClient
    ├─ RscpConnection  →  RscpEncryption  →  RscpFrame / RscpValue
    └─ RscpHandlerPipeline
         ├─ StorageRscpModel   →  StorageDataModel
         ├─ WallboxRscpModel   →  WallboxDataModel
         └─ SgReadyRscpModel
              ↓
         Sensor / Select / Number Entities
```

- **Coordinator** (`coordinator.py`) drives all periodic fetches; entities subscribe through `CoordinatorEntity`.
- **Handler pipeline** (`model/RscpHandlerPipeline.py`) routes raw RSCP frames to registered device models. Adding a new device type is a matter of implementing `RscpModelInterface` and registering it with the pipeline.
- **RSCP protocol** (`e3dc/`) — magic `0xDCE3`, timestamp header, variable-length binary frames, tags defined in `e3dc/RscpTags.py`, Rijndael-256 CBC encryption with IV chaining.

### Repository layout

| Path | Purpose |
|------|---------|
| `custom_components/e3dc_rscp_connect/` | Integration root |
| `├─ e3dc/` | RSCP protocol (connection, encryption, framing, tags) |
| `├─ model/` | Device data models and handler pipeline |
| `├─ entities/` | Entity base class and sensor / select / number types |
| `├─ sensor.py`, `select.py`, `number.py`, `switch.py` | HA platform entry points |
| `├─ coordinator.py` | Polling coordinator |
| `├─ client.py` | High-level RSCP client |
| `└─ config_flow.py` | UI config & options flow |
| `tests/` | Unit tests (mocked, no device required) |

## Development

Home Assistant's `hassfest` validator runs automatically on pull requests via `.github/workflows/hassfest.yml` and checks `manifest.json` and the integration structure.

### Dependencies

- [`py3rijndael==0.3.3`](https://pypi.org/project/py3rijndael/) — Rijndael encryption (pinned in `manifest.json`)
- `homeassistant` — provided by the Home Assistant runtime

## Contributing

Bug reports and pull requests are welcome on [GitHub](https://github.com/tobias-terhaar/e3dc_rscp_connect/issues). When adding support for a new device type, implement `RscpModelInterface` and register the handler with `RscpHandlerPipeline` — existing models in `model/` are good templates.

## Disclaimer

This integration is not affiliated with or endorsed by HagerEnergy GmbH. "E3/DC" and "S10" are trademarks of their respective owners. Use at your own risk.

## License

Released under the [MIT License](LICENSE).
