# Home Assistant Templates

A collection of Jinja2 templates for [Home Assistant](https://www.home-assistant.io/), together with a lightweight Python test harness that lets you unit-test them without a running HA instance.

## Template groups

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

Call the `weather.get_forecasts` action first, then render the template with the response stored in a variable:

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

### Sensors (`templates/sensors/`)

| Template | Purpose |
|---|---|
| `time_of_day.jinja` | Returns the current period of day: `morning`, `afternoon`, `evening`, or `night` |

**Home Assistant usage** (template sensor in `configuration.yaml`):

```yaml
template:
  - sensor:
      - name: "Time of Day"
        state: "{{ states('sensor.time_of_day') }}"
        # or inline:
        state: >
          {% include 'time_of_day.jinja' %}
```

---

### Automations (`templates/automations/`)

| Template | Purpose |
|---|---|
| `good_morning.jinja` | Personalised good-morning message including outdoor temperature and weather condition |

**Required entities:**

| Entity | Purpose |
|---|---|
| `person.resident` | `friendly_name` attribute used for personalised greeting |
| `sensor.outdoor_temperature` | Current outdoor temperature in °C |
| `weather.forecast_home` | Current weather condition |

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
templates/rain/daily_rain_summary.jinja  →  tests/rain/test_*.py
templates/sensors/time_of_day.jinja      →  tests/test_time_of_day.py
templates/automations/good_morning.jinja →  tests/test_good_morning.py
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
