# ha-yaml-gen
Home Assistant sensor/template YAML generator

## Purpose
Generate multiple sensor code and HA templates yaml files from sample sensor output JSON text
in a HA package [^hapackage] format.
Optionally card yaml file(s) [^hacards] can be generated from card templates.
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
"model": "weather"}
'''

#gen.exclude_sensor (["model", "uid", "readings.luminance"])
#gen.include_sensor (["model", "uid", "readings.temperature"])
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
weather_0:
#### Generated: 2026-01-31 12:48:47
  
  ###### Begin: weather_0 Sensors ######
  # MQTT SENSORS
  mqtt:
    sensor:

      - name: 'weather_0 nickname'
        unique_id: 'weather_0_nickname'
        state_topic: 'enviro/weather_0'
        value_template: '{{ value_json.nickname }}'

      - name: 'weather_0 uid'
        unique_id: 'weather_0_uid'
        state_topic: 'enviro/weather_0'
        value_template: '{{ value_json.uid }}'
```
__gen.build_id_list__

This function will cause the generation of files:

```text
weather_backdoor_pkg.yaml
weather_garage_pkg.yaml

# Example sensor YAML (from weather_backdoor):
weather_backdoor:
#### Generated: 2026-01-31 12:52:35
  
  ###### Begin: weather_backdoor Sensors ######
  # MQTT SENSORS
  mqtt:
    sensor:

      - name: 'weather_backdoor nickname'
        unique_id: 'weather_backdoor_nickname'
        state_topic: 'enviro/weather_backdoor'
        value_template: '{{ value_json.nickname }}'

      - name: 'weather_backdoor uid'
        unique_id: 'weather_backdoor_uid'
        state_topic: 'enviro/weather_backdoor'
        value_template: '{{ value_json.uid }}'
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
|{{timestamp_unique_id}}|weather_backdoor_timestamp|templates|
|{{temperature}}|readings.temperature|JSON sensor value|
|{{temperature_value}}|states('sensor.weather_0_temperature')|Card value|
|{{temperature_ent}}|sensor.weather_0_temperature|Card entity|
|{{temperature_id}}|${states["sensor.weather_0_temperature"].entity_id}|Gauge Card Pro|
|{{temperature_state}}|${states["sensor.weather_0_temperature"].state}|Gauge Card Pro|

__Note:__ The variable ids do not include the full json sensor path.

## Module Interfaces

__init (package, mqtt_topic_base)__

- Parameters
  - package
    - Used to create sensor names and output file names
    - Example: "weather"
  - mqtt_topic_base
    - Topic name base used to create the HA mqtt topic
    - Example: "enviro/"

__include_sensor ([ sensor id list... ])__

- Parameters
  - Full path of sensors to be included in the generated mqtt sensors
  - If used, all required sensors must be included in the list
  - Notes
    - Must be called before load_json_sensor_* interface
    - parameter may be a string or list.
    - This interface can be called multiple times.

__exclude_sensor ([ sensor id list... ])__

- Parameters
  - Full path of sensors to be excluded in the generated mqtt sensors
  - Notes
    - Must be called before load_json_sensor_* interface
    - parameter may be a string or list.
    - This interface can be called multiple times.
    - If include_sensor and exclude_sensor are used, excluded sensors will override.

__load_json_sensor_ids (json_payload)\
load_json_sensor_file (json_payload_file_name)__

- load_json_sensor_ids loads json text, usually copied from the publisher output.
- load_json_sensor_file same as above but from file input
- Notes:
  - Input before the first "{" and after the last "}" is ignored.
  - The ignored text can be used for documentation.

__build_range_list (start, count)__
- Parameters
  - start Starting suffix index
  - count number of suffixes to add to list
- Determines how many sensor group yaml's will be generated
- Example output list: "_0", "_1", "_2" ...

__build_id_list (ids)__
- Parameters
  - ids List of suffix ids to add to suffix list
- Determines how many sensor group yaml's will be generated
- Id's will be prepended with "_"
- Example output list: "_kitchen", "_bedroom" ...

__add_ha_template (file_name)__

- Parameters
  - file_name HA template file name.
- Output will be included in the sensor yaml file.

__add_card_template (file_name, suffix)__

- Parameters
  - file_name Template card file name.
  - suffix Used to make output yaml card file names unique.
- More than 1 card template can be used. A different card yaml could be generated multiple displays. For example: display cards for the desktop, a tablet, and a phone. 

__generate ()__

- Generates output HA yaml file(s).

## Example applications:

### examples/enviro_indoor_gen.py
- Generates HA yaml files for Pimironi indoor sensor devices.
- Input files:
  - "indoor.tmpl" - Templates are included with package yaml.
  - "indoor.card" - Generates card file that can be pasted into dashboard card edit.

### examples/host_stats_gen.py
- Generates HA yaml for input from python application.
- Files:
  - host_stats.tmpl
  - host_stats.card
  - host_stats.json - optional raspstats.py mqtt json output text.
  - raspstats.py - Sends host stats (memory, cpu load/temperature, ...) from Raspberry Pi host.
- Notes:
  - This is used for testing and may change a lot.

## Notes:
- Not quite ready for general release.
- Initially built for MQTT input and Gauge Card Pro.
- Run ha_yaml_gen.py stand alone will create 2 (based on SENSOR_COUNT) example output files:
  - enviro_weather_0_pkg.yaml
  - enviro_weather_1_pkg.yaml
- This application was originally intended to create HA package files.
- Only the sensor YAML has been implemented.
- Template and card yaml's are in the works. There are working (maybe) examples in the examples directory.
  - [HA template](/examples/host_stats.tmpl)
  - [HA Card](/examples/host_stats.card)

## Footnotes

[^hapackage]:
  __HAconfigdir/configuration.yaml__ :

  \# Loads default set of integrations. Do not remove.
  default_config:

  \# Load frontend themes from the themes folder\
  frontend:\
    themes: !include_dir_merge_named themes\

  automation: !include automations.yaml\
  script: !include scripts.yaml\
  scene: !include scenes.yaml\
  \#sensor: !include mqtt/sensors.yaml\
  homeassistant:\
    packages: !include_dir_merge_named packages

  The last 2 lines enable packages.
  Create the "packages" directory and add the "enviro" sub directory.

  Copy the generated *.yaml files (not any card files) to:

  HAconfigdir/packages/enviro/

  Restart HA or reload the ha YAML files.

[^hacards]:__Card Templates__

  The easiest way to create a card template file is to build the card in a test __dashboard__.\
  Copy the __Show visual editor__ text to a card template file.\
  Edit the card template file replacing the sensor references with template variables.\
  Example card template file: __example/indoor.card__\.
  The original sensor references have been commented out.

[^mqtt_config]:__mosquitto configuration__\
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
