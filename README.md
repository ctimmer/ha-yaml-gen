# ha-yaml-gen
Home Assistant sensor/template YAML generator

## Purpose
Generate multiple sensor code from sample sensor output JSON text.
Currently set up for mosquitto [^mqtt_config] message queuing.

## Usage

### Creating the class object

```python
from ha_yaml_gen import HaYamlGen

PACKAGE_ID = "weather"
MQTT_PATH_BASE = "enviro/"

gen = HaYamlGen (package = PACKAGE_ID ,
                  mqtt_topic_base = MQTT_PATH_BASE)
```

__package__

This ID will be used to generate
- Sensor names
- Sensor unique id's
- Sensor state topics

__mqtt_topic_base__
- This ID and the package id are used to create the sensors "state_topic"
- Example: state_topic: "enviro/weather_0"

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

exclude_sensor and include_sensor must be called before this function.

The JSON example is from a Pimoroni enviro outdoor. [^outdoorconfig]

### Setting the sensor naming formats

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

## Templates and Cards

__ha_yaml_gen templating__

ha_yaml_gen has it's own inbuilt templating to
substitute template variables with the required values.

- The format is __{{TEMP_VAR}}__
  - 2 left curly braces
  - TEMP_VAR
    - No spaces
    - See table below
  - 2 right curly braces

__Template variables (self.template_variables)__

Examples from weather_0 temperature.

|template variable|Substitute value|Usage|
|-|-|-|
|{{\_PACKAGE\_}}|weather_0|Documentation|
|{{\_TIMESTAMP\_}}|YYYY-MM-DD HH:MM:SS|Documentation|
|{{temperature}}|readings.temperature|JSON sensor value|
|{{temperature_value}}|states('sensor.weather_0_temperature')|Card value|
|{{temperature_ent}}|sensor.weather_0_temperature|Card entity|
|{{temperature_id}}|${states["sensor.weather_0_temperature"].entity_id}|Gauge Card Pro|
|{{temperature_state}}|${states["sensor.weather_0_temperature"].state}|Gauge Card Pro|


## Notes:
- Not quite ready for general release.
- Initially built for MQTT input and Gauge Card Pro.
- Run ha_yaml_gen.py stand alone will create 2 (based on SENSOR_COUNT) example output files:
  - enviro_weather_0_pkg.yaml
  - enviro_weather_1_pkg.yaml
- This application was originally intended to create HA package files. As of yet, I haven't figured out hou to code packages. Some day? Until then the yaml code can be copy/pasted into the HA configuration file(s).
- Only the sensor YAML has been implemented.
- Template and card yaml's are in the works. There are working (maybe) examples in the examples directory.
  - [HA template](/examples/host_stats.tmpl)
  - [HA Card](/examples/host_stats.card)

[^mqtt_config]:
  The default configuration for MQTT does not allow anonymous connections.
  I added this file (local.conf) to the /etc/mosquitto/conf.d (linux) directory.

  \# local.conf\
  \# Allow publishers to send to broker without authentication\
  \#\
  listener 1883 0.0.0.0\
  allow_anonymous true\
  \# end local.conf

[^outdoorconfig]: Pimironi outdoor config settings.

  __Only includes entries for mqtt and Home Assistant  
  enviro config file__

  __This setting prevents the module from going into configuration mode__\
  provisioned = True

  __enter a nickname for this board\
  The mqtt published topic will be 'enviro/weather_0'__\
  nickname = 'weather_0'

  __how often to wake up and take a reading (in minutes)__\
  reading_frequency = 5

  __Send updates via mqtt__\
  destination = 'mqtt'

  __how often to upload data (number of cached readings)\
  Always set to 1\
  HA only uses the received time for graphing, only send 1 reading at a time__\
  upload_frequency = 1

  __mqtt broker settings\
  Needs to match HA MQTT setup parameters__\
  mqtt_broker_address = '192.168.0.XXX'  
  mqtt_broker_username = 'HAusername'  
  mqtt_broker_password = 'HApassword'
