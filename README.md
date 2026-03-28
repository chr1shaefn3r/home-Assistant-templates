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
- [Deploying to Home Assistant](#deploying-to-home-assistant)
  - [Precondition: File Editor app](#precondition-file-editor-app)
  - [Copying the templates](#copying-the-templates)
  - [Verifying the deployment](#verifying-the-deployment)
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

## Deploying to Home Assistant

### Precondition: File Editor app

The templates need to be placed inside the Home Assistant `config/` directory. The easiest way to manage files on your HA instance is the **File Editor** app.

**Install File Editor:**

1. Open Home Assistant and go to **Settings → Apps → App Store**.
2. Search for **File editor** and click **Install**.
3. After installation, enable **Show in sidebar** on the app's info page, then click **Start**.
4. Open **File editor** from the sidebar to confirm it works.

> File Editor only lets you browse within the `config/` directory. All paths below are relative to that root.

---

### Copying the templates

Home Assistant resolves `{% include %}` paths relative to the `config/` directory. The repository's `templates/` directory maps directly to `config/`. Copy each file using File Editor:

| Repository path | HA path |
|---|---|
| `templates/greeting/greeting.jinja` | `config/greeting/greeting.jinja` |
| `templates/weather/daily_weather_summary.jinja` | `config/weather/daily_weather_summary.jinja` |
| `templates/rain/daily_rain_summary.jinja` | `config/rain/daily_rain_summary.jinja` |
| `templates/family_calendar/daily_family_summary.jinja` | `config/family_calendar/daily_family_summary.jinja` |
| `templates/greeting_day_summary.jinja` | `config/greeting_day_summary.jinja` |

For each file:

1. Open **File editor** and navigate to the target folder (create sub-folders as needed via the folder icon).
2. Click the **+** icon to create a new file with the correct name.
3. Paste the contents from this repository and save.

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
