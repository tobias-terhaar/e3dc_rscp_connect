# Changelog

## 1.1.2

### Changed

- **Entity names now carry their device.** Home Assistant composes the displayed name as
  "<device> <entity>", so the sensors of two wallboxes can be told apart instead of both
  reading `Current power`. Existing entities keep their entity id and their history, only
  the displayed name gains the device in front of it.
- **The wallbox device name got shorter.** It was "Wallbox <name> connected to <serial>",
  which now sits in front of every entity name - it is just the wallbox name. The storage
  it belongs to is shown by Home Assistant itself, the wallbox appears below it in the
  device overview.
- **All entity names are translated now** and follow Home Assistant's naming rules. The
  names live in the translations instead of the code, and the integration ships English,
  German, Dutch and French - the config flow, the entity names and the entity states.
  Six entities used to be named in German regardless of the configured language
  (`Ladezustand`, `Lademodus`, `Max/Min Ladestrom`, `Fernsteuerung`,
  `Batterie Fernsteuerung Leistung`), the rest was English only and in mixed title case.
  Some names were also made clearer: `Additional Power` says
  `Additional generators power`, `Wallbox Sun Charge Energy` is `Wallbox PV charge energy`
  (it reports the same value as `Wallbox PV power`), `Home Consumption` gained the missing
  `energy`, and the wallbox sensors are grouped as `Charged energy`, `Charged energy today`
  and `Charged energy this session`. Entity ids and history are unaffected, only the
  displayed names change.

### Added

- **Each wallbox now has a `Charged energy` sensor.** Home Assistant's energy dashboard
  only accepts energy entities (kWh) as an individual device, so the existing
  `Charging power` in watts was never offered there. The new sensor integrates that power
  over time and can be added under *Settings → Dashboards → Energy → Individual devices*.
  The `Charging power` sensor also got a state class, so it is recorded in the long term
  statistics from now on.
- **A `Charged energy today` sensor per wallbox**, counting from 00:00 to 00:00 in the time
  zone Home Assistant is configured for. It is **disabled by default** - enable it under the
  wallbox device if you want it.
- **A `Charged energy this session` sensor per wallbox.** It starts at zero when a car is plugged
  in, counts up while it charges and keeps the final value once the car is unplugged, so the
  last session stays readable until the next one begins. Also **disabled by default**.

### Fixed

- **`Unhandled RSCP tag: TAG_BAT_DATA` was logged on every poll cycle** on systems with
  fewer batteries than the two slots the integration asks for — around 8.600 lines per day
  at the default 10 s interval. The storage answers for the empty slot as well, and that
  answer is now recognised as "slot not equipped": it is reported once at info level and
  stays at debug level afterwards. Nothing was broken by this, it was log noise only
  ([#12](https://github.com/tobias-terhaar/e3dc_rscp_connect/issues/12)).
- **The wallbox state was logged on every poll cycle.** `cp_state_sensor` reported the raw
  CP state at warning level on every update, around 8.600 lines per day and wallbox at the
  default interval - it is debug level now. An unknown state is still warned about, but
  only once per state instead of once per cycle, and a state that has not been read yet is
  no longer reported as unexpected.
- **Unhandled RSCP tags no longer repeat in the log.** Whatever tag remains unclaimed is
  warned about once per tag name and logged at debug level from then on, so a single
  unexpected tag can no longer flood the log.

## 1.1.1

### Added

- **Two new sensors for the total production:** **Total Production Power** and
  **Total Production Energy** add up the internal PV inverter and the additional
  generators, so the Energy Dashboard can be fed with a single value
  ([#13](https://github.com/tobias-terhaar/e3dc_rscp_connect/issues/13)).

### Fixed

- **Additional Power was reported as a negative value and Additional Production Energy
  never counted up.** The E3/DC EMS reports the output of additional generators inverted
  compared to the internal PV power; the value is now flipped so that production is
  positive everywhere, which also lets the energy counter accumulate
  ([#13](https://github.com/tobias-terhaar/e3dc_rscp_connect/issues/13)).
- **Setup no longer fails on an E3/DC One Storage with a wallbox.** The One Storage firmware
  reports the wallbox power-meter values as whole numbers where the S10 reports decimals.
  The integration insisted on the S10 format and aborted every update with
  `Data Type identifier not matching for tag: TAG_WB_PM_POWER_L1`, so setup ended in
  *Einrichtungsfehler, wird erneut versucht*. Both formats are now accepted
  (requires `rscp_lib` 1.0.1).
- **Wallbox charging power was wrong on three-phase charging.** Phase L2 was never read;
  phase L3 was counted twice instead.

## 1.0.8

Version 1.0.7 was never released, so this release contains everything since 1.0.6.

Setting up the integration got a lot easier: your E3/DC system is now found on the network
by itself, you pick how you want to log in instead of guessing the right username, and wrong
credentials no longer leave the integration in a dead end.

### Added

- **Automatic discovery.** E3/DC systems are detected on the local network via SSDP and show
  up under *Settings → Devices & services* ready to be set up. IP address and RSCP port are
  read from the device itself, so a system running on a non-standard port is configured
  correctly without you having to look the port up (falls back to `5033`).
- **Choose your login method.** A *Login method* dropdown lets you pick between:
  - **Local user** — authenticates as the fixed user `local.user`, so only the password of the
    offline RSCP user is required; leave the username empty.
  - **Portal user** — authenticates with your E3/DC portal credentials.

  The dropdown sits directly on the credentials form, so the choice can still be changed
  before submitting — including when you come back to a setup you left half finished. It is
  available for manual setup, for discovered devices and in the options.
- **Two new sensors** for the storage system: **Autarky** and **Self Consumption**, both in
  percent.

### Fixed

- **Wrong credentials or a wrong RSCP key no longer break the integration permanently.**
  Setup previously failed for good with no retry, and even entering correct credentials
  afterwards changed nothing until Home Assistant was restarted. The integration now asks you
  to re-authenticate and recovers as soon as the new credentials are entered.
- **Changed configuration now takes effect immediately.** Editing credentials or the polling
  interval in the options reloads the integration instead of silently keeping the old values.
- **A wrong RSCP key is reported as a credentials problem** rather than surfacing as an
  unspecific internal error.
- **The password and the RSCP key are no longer written to the Home Assistant log.**
- Fixed a translation error that broke the title of the re-authentication entry.

### Changed

- The entire device communication was moved into a self-contained `e3dc_rscp_api` package
  that contains no Home Assistant code. The integration no longer knows anything about RSCP
  tags, frames or connections, which prepares the project for a possible move from a HACS
  integration to a Home Assistant core integration, and for releasing the protocol part as a
  standalone library. There is no change in behaviour for users.
- `defusedxml` is now a requirement; it is used to safely parse the device description
  delivered during discovery.

### Upgrade notes

- Existing configurations keep working, no action required. Entity IDs are unchanged.
- If your integration was stuck because of wrong credentials, you will be asked to
  re-authenticate after the update instead of having to delete and re-add the device.

### For developers

- Tests run with `scripts/test` (or `python3 -m pytest`); the devcontainer image ships its own
  `pytest` on `PATH` that would otherwise mix two installations.
- `asyncio_mode = "auto"` is now set in `pyproject.toml`, as required by
  `pytest-homeassistant-custom-component`.
- The devcontainer was bumped to Python 3.14.
- `tests/test_architecture.py` enforces the boundary between the integration and
  `e3dc_rscp_api` in both directions.
