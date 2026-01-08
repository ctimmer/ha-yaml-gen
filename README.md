# ha-yaml-gen
Home Assistant sensor/template YAML generator

## Purpose
Generate multiple sensor code from sample sensor output JSON text.

## Usage

### Creating the class object

```python
PACKAGE_ID = "weather"
MQTT_PATH_BASE = "enviro/"

gen = HaYamlGen (package = PACKAGE_ID ,
                  mqtt_topic_base = MQTT_PATH_BASE)
```

__package__
### Loading the JSON payload

```python
JSON_PAYLOAD_TEXT = \
'''
This will be ignored, use for documentation
{
"nickname": "weather_0",
"uid": "e66164084329b22b",
"timestamp": "2025-12-18T05:03:41Z",
"readings":
  {"temperature": 26.09,
  "humidity": 20.36,
  "pressure": 1005.18,
  "luminance": 4.65,
  "wind_speed": 0,
  "rain": 0,
  "rain_per_second": 0.0,
  "wind_direction": 135},
"model": "weather"}'''

#gen.exclude_sensor (["model", "uid", "readings.luminance"])
#gen.include_sensor (["model", "uid", "readings", "readings.temperature"])
gen.load_json_sensor_ids (JSON_PAYLOAD_TEXT)
```

__JSON_PAYLOAD_TEXT__

This is a copy of the json payload sent from the mqtt publisher application.
The object id's are used to build the HA sensor id's.
The id value affects the HA sensor parameters.

The JSON example is from a Pimoroni enviro outdoor. [^outdoorconfig]

### Setting the sensor name formats

```python
PACKAGE_IDX_START = 0
PACKAGE_COUNT = 2
PACKAGE_IDS = ["kitchen", "bedroom"]

gen.build_range_list (start = PACKAGE_IDX_START,
                        count = PACKAGE_COUNT)
#gen.build_id_list (ids = PACKAGE_IDS)
```

__gen.build_range_list__

This function will cause the generation of 2 files:

```text
weather_0_pkg.yaml
weather_1_pkg.yaml

# Example sensor YAML (from weather_0):
mqtt:
  sensor:

    - name: "weather_0 nickname"
      state_topic: "enviro/weather_0"
      value_template: "{{ value_json.nickname }}"
      unique_id: "weather_0_nickname"

    - name: "weather_0 temperature"
      state_topic: "enviro/weather_0"
      value_template: "{{ value_json.readings.temperature }}"
      state_class: "measurement"
      unique_id: "weather_0_temperature"
```
__gen.build_id_list__

This function will cause the generation of files:

```text
weather_backdoor_pkg.yaml
weather_garage_pkg.yaml

# Example sensor YAML (from weather_backdoor):
mqtt:
  sensor:

    - name: "weather_backdoor nickname"
      state_topic: "enviro/weather_backdoor"
      value_template: "{{ value_json.nickname }}"
      unique_id: "weather_backdoor_nickname"

    - name: "weather_backdoor temperature"
      state_topic: "enviro/weather_backdoor"
      value_template: "{{ value_json.readings.temperature }}"
      state_class: "measurement"
      unique_id: "weather_backdoor_temperature"
```

### Generating the YAML output

```python
gen.generate ()
```

## Notes:
- Not ready for general release.
- Initially built for MQTT input and Gauge Card Pro.
- Run ha_yaml_gen.py stand alone will create 2 (based on SENSOR_COUNT) example output files:
  - enviro_weather_0_pkg.yaml
  - enviro_weather_1_pkg.yaml
- This application was originally intended to create HA package files. As of yet, I haven't figured out hou to code packages. Some day? Until then the yaml code can be copy/pasted into the HA configuration file(s).
- Only the sensor YAML has been implemented.

[^outdoorconfig]: Pimironi outdoor config text.