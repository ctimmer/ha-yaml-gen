# ha-yaml-gen
Home Assistant sensor/template YAML generator

## Purpose
Generate multiple sensor code from sample sensor output JSON text.

## Notes:
- Not ready for general release.
- Initially built for MQTT input and Gauge Card Pro.
- Run ha_yaml_gen.py stand alone will create 2 (based on SENSOR_COUNT) example output files:
  - enviro_weather_0_pkg.yaml
  - enviro_weather_1_pkg.yaml
- This application was originally intended to create HA package files. As of yet, I haven't figured out hou to code packages. Some day? Until then the yaml code can be copy/pasted into the HA configuration file(s).
- Only the sensor YAML has been implemented.
