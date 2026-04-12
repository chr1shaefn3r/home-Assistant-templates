# Home Assistant Templates

> **Disclaimer:** This codebase was entirely written by [Claude](https://www.anthropic.com/claude) (Anthropic's AI assistant) under human supervision.

A collection of Jinja2 templates for [Home Assistant](https://www.home-assistant.io/), together with a lightweight Python test harness that lets you unit-test them without a running HA instance.

## Table of contents

- [Template groups](#template-groups)
  - [Greeting](#greeting-templatesgreeting)
  - [Weather](#weather-templatesweather)
  - [Rain](#rain-templatesrain)
  - [Family Calendar](#family-calendar-templatesfamily_calendar)
  - [Integration: Morning Summary](#integration-morning-summary-templatesgreeting_day_summaryjinja)
  - [Battery-powered Sensors](#battery-powered-sensors-templatesbattery_sensors)
- [Deploying to Home Assistant](#deploying-to-home-assistant)
  - [Precondition: File Editor app](#precondition-file-editor-app)
  - [Setting up the custom_templates directory](#setting-up-the-custom_templates-directory)
  - [Copying the templates](#copying-the-templates)
  - [Reloading custom templates](#reloading-custom-templates)
  - [Verifying the deployment](#verifying-the-deployment)
- [Automated deployment](#automated-deployment)
  - [How it works](#how-it-works)
  - [Precondition: Terminal & SSH app](#precondition-terminal--ssh-app)
  - [Local deploy script](#local-deploy-script)
  - [GitHub Actions auto-deploy](#github-actions-auto-deploy)
  - [Samba alternative](#samba-alternative)
- [Developer guide](#developer-guide)
  - [Prerequisites](#prerequisites)
  - [Local setup](#local-setup)
  - [Running the tests](#running-the-tests)
  - [VSCode setup](#vscode-setup)
  - [CI](#ci)

## Template groups

### Greeting (`templates/greeting/`)

| Template | Purpose |
|---|---|
| `greeting.jinja` | Produces a German-language time-of-day greeting with the current time |

**Input:** the current time via HA's `now()` global.

**Output examples:**

| Time range | Output |
|---|---|
| before 11:00 | `Guten Morgen, es ist 5Uhr 55.` |
| 11:00 – 12:59 | `Guten Mittag, es ist 11Uhr 30.` |
| 13:00 – 17:59 | `Guten Nachmittag. es ist 15Uhr 5.` |
| 18:00 and later | `Guten Abend, es ist 20Uhr 0.` |

**Home Assistant usage:**

```yaml
action: notify.mobile_app
data:
  message: >
    {% include 'greeting.jinja' %}
```

---

### Weather (`templates/weather/`)

| Template | Purpose |
|---|---|
| `daily_weather_summary.jinja` | Produces a German-language summary of today's weather condition and high temperature |

**Input:** the `forecast` list from a `weather.get_forecasts` action call (daily resolution). Uses `forecast[0]` (today's entry).

**Output examples:**

| Scenario | Output |
|---|---|
| Cloudy, 8.8 °C | `Das Wetter ist aktuell bewölkt und es wird höchstens 8.8 Grad warm.` |

**Condition mapping (HA condition → German):**

| HA condition | German |
|---|---|
| `clear-night` | eine klare Nacht |
| `cloudy` | bewölkt |
| `exceptional` | außergewöhnlich |
| `fog` | neblig |
| `hail` | Hagel |
| `lightning` | Gewitter |
| `lightning-rainy` | Gewitter mit Regen |
| `partlycloudy` | Teilweise bewölkt |
| `pouring` | Starker Regen |
| `rainy` | regnerisch |
| `snowy` | Schnee |
| `snowy-rainy` | Schneeregen |
| `sunny` | sonnig |
| `windy` / `windy-variant` | windig |

**Home Assistant usage:**

```yaml
action: weather.get_forecasts
target:
  entity_id: weather.forecast_home
data:
  type: daily
response_variable: daily_forecast

action: notify.mobile_app
data:
  message: >
    {% set forecast = daily_forecast['weather.forecast_home']['forecast'] %}
    {% include 'daily_weather_summary.jinja' %}
```

---

### Rain (`templates/rain/`)

| Template | Purpose |
|---|---|
| `daily_rain_summary.jinja` | Produces a German-language rain summary for the day based on an hourly forecast |

**Input:** the `forecast` list from a `weather.get_forecasts` action call (hourly resolution).

**Output examples:**

| Scenario | Output |
|---|---|
| No precipitation at all | `Heute bleibt es trocken` |
| No precipitation today, rain tomorrow | `Heute bleibt es trocken` |
| Rain in one window | `Heute regnet es von 10 bis 12 Uhr` |
| Rain in multiple windows | `Heute regnet es von 10 bis 12 Uhr und von 14 bis 16 Uhr` |
| Rain all day | `Heute regnet es den ganzen Tag` |

**Home Assistant usage:**

```yaml
action: weather.get_forecasts
target:
  entity_id: weather.forecast_home
data:
  type: hourly
response_variable: hourly_forecast

action: notify.mobile_app
data:
  message: >
    {% set forecast = hourly_forecast['weather.forecast_home']['forecast'] %}
    {% include 'daily_rain_summary.jinja' %}
```

---

### Family Calendar (`templates/family_calendar/`)

| Template | Purpose |
|---|---|
| `daily_family_summary.jinja` | Produces a German-language summary of today's family calendar events |

**Input:** the `events` list from a `calendar.get_events` action call.

**Output examples:**

| Scenario | Output |
|---|---|
| No events | `Es sind keine Familientermine für den Rest des Tages geplant.` |
| One full-day event | `Folgende Familientermine sind für heute noch geplant:`<br>`Osterfeier, Ganztagestermin` |
| One timed appointment | `Folgende Familientermine sind für heute noch geplant:`<br>`Kinderarzt von 10 Uhr 30 bis 11 Uhr` |
| Multiple events | Each event on its own line, sorted chronologically |

Time formatting: minutes are shown only when non-zero (`10 Uhr 30`, `11 Uhr`). Events are always rendered in chronological order regardless of the order returned by HA.

**Home Assistant usage:**

```yaml
action: calendar.get_events
target:
  entity_id: calendar.familienkalender
data:
  duration:
    hours: 24
response_variable: agenda

action: notify.mobile_app
data:
  message: >
    {% set events = agenda['calendar.familienkalender']['events'] %}
    {% include 'daily_family_summary.jinja' %}
```

**Required entities:**

| Entity | Purpose |
|---|---|
| `calendar.familienkalender` | Source calendar (adjust entity ID to match your setup) |

---

### Integration: Morning Summary (`templates/greeting_day_summary.jinja`)

Composes all four groups into a single morning briefing: greeting → weather → rain → family calendar.

**Output example:**

```
Guten Morgen, es ist 5Uhr 55.
Das Wetter ist aktuell bewölkt und es wird höchstens 8.8 Grad warm.
Heute bleibt es trocken
Folgende Familientermine sind für heute noch geplant:
Kinderarzt von 10 Uhr 30 bis 11 Uhr
```

**Home Assistant usage:**

```yaml
action: weather.get_forecasts
target:
  entity_id: weather.forecast_home
data:
  type: daily
response_variable: daily_forecast_response

action: weather.get_forecasts
target:
  entity_id: weather.forecast_home
data:
  type: hourly
response_variable: hourly_forecast_response

action: calendar.get_events
target:
  entity_id: calendar.familienkalender
data:
  duration:
    hours: 24
response_variable: agenda

action: notify.mobile_app
data:
  message: >
    {% set daily_forecast = daily_forecast_response['weather.forecast_home']['forecast'] %}
    {% set hourly_forecast = hourly_forecast_response['weather.forecast_home']['forecast'] %}
    {% set events = agenda['calendar.familienkalender']['events'] %}
    {% include 'greeting_day_summary.jinja' %}
```

---

### Battery-powered Sensors (`templates/battery_sensors/`)

| Template | Purpose |
|---|---|
| `low_battery_summary.jinja` | Reports all battery-powered sensors below a configurable threshold |

**How battery sensors are discovered:** The template reads `states.sensor` at render time and automatically finds every entity with `device_class: battery`. No manual list is required — new battery-powered devices are picked up immediately.

To see which entities will be included, paste this into **Developer Tools → Template**:

```jinja2
{{ states.sensor
   | selectattr('attributes.device_class', 'eq', 'battery')
   | map(attribute='entity_id') | list }}
```

**Input:** no variables required. Optionally pass `threshold` (integer, default `20`) to change the low-battery cut-off.

**Excluding rechargeable devices (phones, tablets, …):**

HA does not expose battery type metadata natively, so rechargeable devices must be excluded via an HA label. One-time setup:

1. Go to **Settings → Labels** and create a label called `rechargeable`.
2. Go to **Settings → Devices & Services**, open the device (e.g. your phone), and assign the `rechargeable` label to its battery sensor entity.

The template automatically skips any entity carrying that label. New rechargeable devices are excluded the moment you label them.

**Showing the battery type:**

Assign a battery type label to each sensor entity so the template can include it in the output. Supported labels:

| Label | Displayed as |
|---|---|
| `battery_aa` | AA |
| `battery_aaa` | AAA |
| `battery_cr2032` | CR2032 |
| `battery_cr2450` | CR2450 |
| `battery_9v` | 9V |
| `battery_d` | D |

One-time setup per device: **Settings → Devices & Services** → open device → assign the matching label to its battery sensor entity. If no battery type label is set, the type is simply omitted from the output.

To preview which entities carry a given battery type label, use **Developer Tools → Template**:

```jinja2
{{ label_entities('battery_aa') }}
```

**Showing remaining runtime:**

The template can estimate how many days of battery life remain based on the observed discharge rate since the last battery replacement. This requires one `input_datetime` helper per device.

Naming convention: `input_datetime.<entity_suffix>_replaced`

| Sensor entity | Helper entity |
|---|---|
| `sensor.motion_battery` | `input_datetime.motion_battery_replaced` |
| `sensor.door_battery` | `input_datetime.door_battery_replaced` |

One-time setup per device:

1. Go to **Settings → Devices & Services → Helpers** and create a **Date/Time** helper named after the convention above.
2. After replacing the batteries, set the helper value to today's date.

The template computes `days_remaining = current_level / (capacity_used / days_since_replacement)` and appends `~N Tage` to the alert. Guards: if the helper is missing or unavailable, the replacement was less than a day ago, or the sensor is still at 100%, no estimate is shown.

**Output examples:**

| Scenario | Output |
|---|---|
| No battery sensors registered | `Keine batteriebetriebenen Sensoren gefunden.` |
| All sensors above threshold | *(empty — no notification)* |
| One sensor low, no labels | `Folgendes Gerät hat einen niedrigen Akkustand: Bewegungsmelder (8%)` |
| One sensor low, type labelled | `Folgendes Gerät hat einen niedrigen Akkustand: Bewegungsmelder (8%, CR2032)` |
| One sensor low, with runtime estimate | `Folgendes Gerät hat einen niedrigen Akkustand: Bewegungsmelder (ungefähr 8 Tage)` |
| One sensor low, type + runtime | `Folgendes Gerät hat einen niedrigen Akkustand: Bewegungsmelder (ungefähr 8 Tage, CR2032)` |
| Multiple sensors low | `Folgende Geräte haben niedrigen Akkustand: Bewegungsmelder (8%, AA), Türsensor (12%)` |
| Low sensor is labelled `rechargeable` | *(excluded — no notification)* |

**Home Assistant usage:**

```yaml
action: notify.mobile_app
data:
  message: >
    {% set threshold = 20 %}
    {% include 'battery_sensors/low_battery_summary.jinja' %}
```

To use a custom threshold:

```yaml
action: notify.mobile_app
data:
  message: >
    {% set threshold = 30 %}
    {% include 'battery_sensors/low_battery_summary.jinja' %}
```

---

## Deploying to Home Assistant

### Precondition: File Editor app

The templates need to be placed inside the Home Assistant `config/custom_templates/` directory. The easiest way to manage files on your HA instance is the **File Editor** app.

**Install File Editor:**

1. Open Home Assistant and go to **Settings → Apps → App Store**.
2. Search for **File editor** and click **Install**.
3. After installation, enable **Show in sidebar** on the app's info page, then click **Start**.
4. Open **File editor** from the sidebar to confirm it works.

> File Editor only lets you browse within the `config/` directory. All paths below are relative to that root.

---

### Setting up the custom_templates directory

Home Assistant looks for `{% include %}` targets in `config/custom_templates/`. Create the directory if it does not exist yet:

1. Open **File editor**.
2. Click the folder icon in the top-left to open the directory browser.
3. Navigate to the root (`/config/`).
4. Create a new folder called `custom_templates`.

---

### Copying the templates

The repository's `templates/` directory maps directly to `config/custom_templates/`. Copy each file using File Editor:

| Repository path | HA path |
|---|---|
| `templates/greeting/greeting.jinja` | `custom_templates/greeting/greeting.jinja` |
| `templates/weather/daily_weather_summary.jinja` | `custom_templates/weather/daily_weather_summary.jinja` |
| `templates/rain/daily_rain_summary.jinja` | `custom_templates/rain/daily_rain_summary.jinja` |
| `templates/family_calendar/daily_family_summary.jinja` | `custom_templates/family_calendar/daily_family_summary.jinja` |
| `templates/battery_sensors/low_battery_summary.jinja` | `custom_templates/battery_sensors/low_battery_summary.jinja` |
| `templates/greeting_day_summary.jinja` | `custom_templates/greeting_day_summary.jinja` |

For each file:

1. Open **File editor** and navigate to the target folder (create sub-folders as needed via the folder icon).
2. Click the **+** icon to create a new file with the correct name.
3. Paste the contents from this repository and save.

---

### Reloading custom templates

After adding or changing any file in `custom_templates/`, Home Assistant must reload the directory before the changes take effect. Trigger the reload action once from **Developer Tools → Actions**:

- Action: `homeassistant.reload_custom_templates`

No data payload is required. Click **Perform action** to confirm. HA will re-read all files in `custom_templates/` immediately — no restart needed.

---

### Verifying the deployment

Use the **Template editor** built into Home Assistant to confirm the templates render correctly before wiring them into automations:

1. Go to **Developer Tools → Template**.
2. Paste the following into the template editor and check the output:

```jinja2
{% include 'greeting/greeting.jinja' %}
```

You should see the appropriate greeting for the current time. Repeat for other templates, passing any required variables through `{% set %}` statements.

---

## Automated deployment

### How it works

`scripts/deploy.sh` automates the full deployment cycle:

1. **Change detection** — compares the current `templates/` tree against `.last-deployed` (a file that records the last deployed git commit hash) and lists only what changed. If nothing changed it exits early; pass `--force` to override.
2. **Transfer** — `rsync` over SSH pushes only the changed files to `config/custom_templates/` on your HA instance (fast, delta-only).
3. **Reload** — calls `homeassistant.reload_custom_templates` via the HA REST API so changes take effect immediately, no restart needed.
4. **Record** — writes the current commit hash to `.last-deployed` (gitignored) for the next run.

`.github/workflows/deploy.yml` runs the same script automatically after every successful test run on `main`.

---

### Precondition: Terminal & SSH app

The deploy script connects to HA over SSH. One-time setup:

1. In HA go to **Settings → Apps → App Store**, search for **Terminal & SSH** and install it.
2. Enable **Advanced Mode** in your user profile (**Profile → Advanced Mode**) — the app is hidden without it.
3. Generate an ECDSA key pair on your local machine if you don't have one:
   ```bash
   ssh-keygen -t ecdsa -f ~/.ssh/id_ecdsa
   ```
4. Open the **Terminal & SSH** app configuration and paste the contents of `~/.ssh/id_ecdsa.pub` into the **Authorized keys** field.
5. Start the app and confirm you can connect:
   ```bash
   ssh -i ~/.ssh/id_ecdsa root@homeassistant.local
   ```

---

### Local deploy script

1. Copy `.env.example` to `.env` and fill in the values:

   ```bash
   cp .env.example .env
   ```

   | Variable | Description |
   |---|---|
   | `HA_HOST` | Hostname or IP of your HA instance (e.g. `homeassistant.local`) |
   | `HA_USER` | SSH user — always `root` on HA OS |
   | `HA_SSH_PORT` | SSH port — default `22` |
   | `HA_SSH_KEY` | Path to your ECDSA private key — default `~/.ssh/id_ecdsa` |
   | `HA_TOKEN` | Long-lived access token — create one at **Profile → Security → Long-lived access tokens** |

2. Run the script:
   ```bash
   bash scripts/deploy.sh
   ```

   First run deploys everything. Subsequent runs deploy only what changed since the last deploy. Use `--force` to redeploy all files regardless:
   ```bash
   bash scripts/deploy.sh --force
   ```

---

### GitHub Actions auto-deploy

The workflow in `.github/workflows/deploy.yml` triggers automatically after every successful test run on `main`. It requires five **GitHub Secrets** (Settings → Secrets and variables → Actions):

| Secret | Value |
|---|---|
| `HA_HOST` | Hostname or IP of your HA instance — **must be reachable from GitHub's runners** (public IP or port-forwarded) |
| `HA_USER` | SSH user (`root`) |
| `HA_SSH_PORT` | SSH port (usually `22`) |
| `HA_SSH_KEY` | Full contents of your ECDSA **private** key (`cat ~/.ssh/id_ecdsa`) |
| `HA_TOKEN` | Long-lived access token |

> **Note on reachability:** GitHub Actions runners are hosted on Microsoft Azure and cannot reach a private home network directly. Options to make your HA reachable:
> - **Port forwarding** — forward the SSH port (and optionally 8123) on your router to your HA machine.
> - **Tailscale** — install the Tailscale add-on on HA and the [Tailscale GitHub Action](https://github.com/tailscale/github-action) in the workflow for a zero-config VPN tunnel (no port forwarding needed, recommended).
> - **Cloudflare Tunnel** — expose HA via a Cloudflare Tunnel without opening router ports.

---

### Samba alternative

If you prefer not to set up SSH, the **Samba** app lets you access `config/` as a network share. Install it from **Settings → Apps → App Store**, then:

1. Mount the share on your machine (`\\<ha-ip>\homeassistant` on Windows, `smb://<ha-ip>/homeassistant` on macOS).
2. Copy the contents of `templates/` into `homeassistant/custom_templates/` in the mounted share.
3. Trigger a reload manually: **Developer Tools → Actions → `homeassistant.reload_custom_templates`**.

This approach is LAN-only and does not support automated deployment from GitHub Actions.

---

## Developer guide

### Prerequisites

- Python 3.10 or newer
- [pip](https://pip.pypa.io/)

### Local setup

```bash
git clone https://github.com/chr1shaefn3r/home-Assistant-templates.git
cd home-Assistant-templates
pip install jinja2 pytest
```

### Running the tests

```bash
pytest -v
```

All template tests live under `tests/`. Test files mirror the `templates/` directory structure:

```
templates/greeting/greeting.jinja                    →  tests/greeting/test_*.py
templates/weather/daily_weather_summary.jinja        →  tests/weather/test_*.py
templates/rain/daily_rain_summary.jinja              →  tests/rain/test_*.py
templates/family_calendar/daily_family_summary.jinja →  tests/family_calendar/test_*.py
templates/greeting_day_summary.jinja                 →  tests/test_greeting_day_summary.py
```

The shared `tests/conftest.py` provides a `render()` pytest fixture that sets up a Jinja2 environment with all Home Assistant globals and filters stubbed out (`states`, `is_state`, `state_attr`, `now`, `as_datetime`, `float`, `int`, …). Pass entity states, attributes, the current time, or arbitrary template variables directly in each test:

```python
def test_example(render):
    result = render(
        "rain/daily_rain_summary.jinja",
        variables={"forecast": [...]},
    )
    assert "Heute bleibt es trocken" in result
```

### VSCode setup

Install the following extensions:

| Extension | ID | Purpose |
|---|---|---|
| [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) | `ms-python.python` | Python language support, IntelliSense |
| [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) | `ms-python.vscode-pylance` | Fast type checking and auto-imports |
| [Python Test Explorer](https://marketplace.visualstudio.com/items?itemName=ms-python.python) | built into the Python extension | Discover and run pytest tests from the sidebar |
| [Better Jinja](https://marketplace.visualstudio.com/items?itemName=samuelcolvin.jinjahtml) | `samuelcolvin.jinjahtml` | Syntax highlighting for `.jinja` template files |
| [Home Assistant Config Helper](https://marketplace.visualstudio.com/items?itemName=keesschollaart.vscode-home-assistant) | `keesschollaart.vscode-home-assistant` | HA-aware autocomplete and validation in YAML files |

#### Recommended workspace settings

Create `.vscode/settings.json` in the project root:

```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["-v"],
  "python.testing.unittestEnabled": false,
  "files.associations": {
    "*.jinja": "jinja-html"
  }
}
```

This enables the built-in pytest test runner in the sidebar and associates `.jinja` files with the Better Jinja syntax highlighter.

### CI

A GitHub Actions workflow (`.github/workflows/test.yml`) runs the full test suite on every push to `main` and on every pull request targeting `main`. No configuration is required — GitHub provides free runner minutes for public repositories.
