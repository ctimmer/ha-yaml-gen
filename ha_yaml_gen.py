
import time
import json
import re
import pprint

MQTT_SENSOR_HEADERS = \
'''
# MQTT SENSORS
mqtt:
  sensor:
'''
TEMPLATE_SENSOR_HEADERS = \
'''
# TEMPLATES
template:
  - sensor:
'''


TMPL_VAR_RE = r"\{\{\w+\}\}"


MQTT_SENSOR_BASIC = \
'''
    - name: "{{NAME}}"
      state_topic: "{{STATE_TOPIC}}"
      value_template: "{{ value_json.{{ENTITY}} }}"
      unique_id: "{{UNIQUE_ID}}"
'''
MQTT_SENSOR_MEASUREMENT = \
'''
    - name: "{{NAME}}"
      state_topic: "{{STATE_TOPIC}}"
      value_template: "{{ value_json.{{ENTITY}} }}"
      state_class: "measurement"
      unique_id: "{{UNIQUE_ID}}"
'''
MQTT_SENSOR_TEMPERATURE_C = \
'''
    - name: "{{NAME}}"
      state_topic: "{{STATE_TOPIC}}"
      value_template: "{{ value_json.{{ENTITY}} }}"
      state_class: "measurement"
      unit_of_measurement: "°C"
      device_class: "temperature"
      unique_id: "{{UNIQUE_ID}}"
'''
MQTT_SENSOR_TEMPERATURE_F = \
'''
    - name: "{{NAME}}"
      state_topic: "{{STATE_TOPIC}}"
      value_template: "{{ value_json.{{ENTITY}} }}"
      state_class: "measurement"
      unit_of_measurement: "°F"
      device_class: "temperature"
      unique_id: "{{UNIQUE_ID}}"
'''
MQTT_SENSOR_DEFAULT = MQTT_SENSOR_BASIC
MQTT_SENSOR_TEMPLATES = {
    "default" : MQTT_SENSOR_DEFAULT ,
    "min" : MQTT_SENSOR_BASIC ,
    "meas" : MQTT_SENSOR_MEASUREMENT ,
    "temp_c" : MQTT_SENSOR_TEMPERATURE_C ,
    "temp_f" : MQTT_SENSOR_TEMPERATURE_F
}

################################################################################
# class HaYamlGen
################################################################################

class HaYamlGen :

    def __init__(self,
                mqtt_topic = "mqtt_topic" ,
                template_pattern=TMPL_VAR_RE) :
        self.template_variables = {}
        self.sensor_include_list = None
        self.sensor_exclude_list = []
        self.mqtt_topic_base = mqtt_topic
        self.template_pattern = template_pattern
        self.sensor_ids = {}
        self.sensor_id_list = None

    def get_unique_id (self, sensor_name) :
        if sensor_name not in self.sensor_id_list :
            self.sensor_id_list[sensor_name] = {
                "count" : 0
                }
            return sensor_name
        self.sensor_id_list[sensor_name]["count"] += 1
        #print (self.sensor_id_list)
        new_name = sensor_name + "_" + str (self.sensor_id_list[sensor_name]["count"])
        self.sensor_id_list[new_name] = {
                "count" : 0
                }
        return new_name

    def card_pro_sensor_vars (self, suffix="_0") : #, sensor_id, path) :
        dest_dict = self.template_variables
        for _, (sensor_name, sensor_data) in enumerate (self.sensor_ids.items ()) :
            entity = sensor_data ["entity"]
            if sensor_name not in dest_dict :
                dest_dict [sensor_name] = entity
            entity = entity + suffix
            dest_dict [sensor_name + "_ent"] = entity
            dest_dict [sensor_name + "_state"] = '${{states["{}"].state}}'.format (entity)
            dest_dict [sensor_name + "_id"] = '${{states["{}"].entity_id}}'.format (entity)
            dest_dict [sensor_name + "_type"] = sensor_data ["type"]
        #pprint.pprint(self.template_variables, width=2)

    def sub_var (self, match):
        tmpl_var = match.group(0)           # get matched string '{{...}}'
        tmpl_var = tmpl_var[2:][:-2]        # strip leading '{{' and ending '}}'
        if tmpl_var not in self.template_variables :
            return match.group(0)           # return original text
        return self.template_variables[tmpl_var]           # return substitute value

    def initialize (self) :
        self.sensor_id_list = {}
        self.sensor_ids = {}

    def exclude_sensor (self, sensor_ids) :
        sensor_list = None
        if isinstance (sensor_ids, str) :
            sensor_list = [sensor_ids]
        elif isinstance (sensor_ids, list) :
            sensor_list = sensor_ids
        else :
            # handle error
            return
        for _, sensor_id in enumerate (sensor_list) :
            if sensor_id in self.sensor_exclude_list :
                return
            self.sensor_exclude_list.append (sensor_id)
    def include_sensor (self, sensor_ids) :
        sensor_list = None
        if isinstance (sensor_ids, str) :
            sensor_list = [sensor_ids]
        elif isinstance (sensor_ids, list) :
            sensor_list = sensor_ids
        else :
            # handle error
            return
        if self.sensor_include_list is None :
            self.sensor_include_list = []
        for _, sensor_id in enumerate (sensor_list) :
            if sensor_id in self.sensor_include_list :
                return
            self.sensor_include_list.append (sensor_id)
    def sensor_is_included (self, sensor_id) :
        if sensor_id in self.sensor_exclude_list :
            return False
        if self.sensor_include_list is not None :
            if sensor_id not in self.sensor_include_list :
                return False
        return True
    def load_sensor_ids (self, payload, path="") :
        #print ("payload:", payload, path)
        for _, (s_id, s_data) in enumerate (payload.items()) :
            # Set sensor code based on data type
            new_path = path
            if len (new_path) > 0 :
                new_path += "."
            #print ("PARSE: s_id", s_id, s_data)
            if isinstance (s_data, (int, float, bool)) :
                if not self.sensor_is_included (s_id) :
                    continue
                s_id = self.get_unique_id (s_id)
                self.sensor_ids [s_id] = {
                    "entity" : new_path + s_id ,
                    "type" : MQTT_SENSOR_MEASUREMENT    # default
                    }
            elif isinstance (s_data, (str, list)) :
                if not self.sensor_is_included (s_id) :
                    continue
                s_id = self.get_unique_id (s_id)
                self.sensor_ids [s_id] = {
                    "entity" : new_path + s_id ,
                    "type" : MQTT_SENSOR_BASIC    # default for array
                    }
            elif isinstance (s_data, dict) :
                new_path += s_id
                #print ("NEW:", new_path)
                self.load_sensor_ids (s_data, new_path)

    def load_json_sensor_ids (self, json_text) :
        self.initialize ()
        json_dict = json.loads (json_text)
        self.load_sensor_ids (json_dict)
        #print (self.sensor_ids)

    def build_package_files (self, sensor_data) :
        sensor_id = sensor_data ["sensor_id"]
        suffix = sensor_data ["suffix"]
        #print ("SENSOR_ID:",sensor_id)
        self.template_variables = {"S_ID" : sensor_id + suffix}
        self.card_pro_sensor_vars (suffix=suffix)
        #print (self.template_variables)
        yaml_file_name = sensor_id + suffix + "_pkg.yaml"
        yaml_file = open (yaml_file_name, "w")
        package = sensor_data["sensor_id"]
        yaml_file.write (MQTT_SENSOR_HEADERS)
        for _, (sensor_id,_) in enumerate (self.sensor_id_list.items()) :
            #print (sensor_id, self.template_variables [sensor_id])
            #if sensor_id not in self.template_variables :
            #    continue
            self.mqtt_template_variables = {
                "NAME" : package + suffix + " " + sensor_id ,
                "ENTITY" : self.template_variables [sensor_id] ,
                "UNIQUE_ID" : package + suffix + "_" + sensor_id ,
                "STATE_TOPIC" : self.mqtt_topic_base + suffix
                }
            sensor_text = self.template_variables [sensor_id + "_type"]
            out_line = re.sub (self.template_pattern, self.mqtt_sub_var, sensor_text)
            yaml_file.write (out_line)
        yaml_file.write (TEMPLATE_SENSOR_HEADERS)
        yaml_file.close ()

    def mqtt_sub_var (self, match):
        tmpl_var = match.group(0)           # get matched string '{{...}}'
        tmpl_var = tmpl_var[2:][:-2]        # strip leading '{{' and ending '}}'
        if tmpl_var not in self.mqtt_template_variables :
            return match.group(0)           # return original text
        return self.mqtt_template_variables[tmpl_var]           # return substitute value

    def add_sensor_type (self, sensor_id, sensor_type="default") :
        if sensor_id not in self.sensor_id_list :
            print ("No sensor", sensor_id)
            return
        type = sensor_type
        if type not in MQTT_SENSOR_TEMPLATES :
            type = "default"
        self.sensor_id_list [sensor_id]["type"] = MQTT_SENSOR_TEMPLATES [type]

    def generate (self, sensor_ids) :
        for _, (sensor_id,_) in enumerate (self.sensor_id_list.items()) :  # temporary fix
            self.add_sensor_type (sensor_id)
        for _, sensor_data in enumerate (sensor_ids) :
            self.build_package_files (sensor_data)

    def build_range_list (self, sensor_id, start = 0, count = 1) :
        range_list = []
        for range_idx in range (start, (start + count)) :
            range_list.append ({
                "sensor_id" : sensor_id ,
                "suffix" : "_" + str (range_idx)
                })
        return range_list
#
################################################################################
# main
################################################################################

def main () :

    # Output from Pimironi enviro outdoor weather sensors
    MTTQ_PAYLOAD_TEXT = \
'''{
"nickname": "weather_0",
"uid": "e66164084329b22b",
"timestamp": "2025-12-18T05:03:41Z",
"readings": {"temperature": 26.09,
"humidity": 20.36, "pressure": 1005.18,
"luminance": 4.65,
"wind_speed": 0,
"rain": 0,
"rain_per_second": 0.0,
"wind_direction": 135},
"model": "weather"}'''

    SENSOR_ID = "enviro_weather"
    VERSION = ""

    gen = HaYamlGen (mqtt_topic="enviro_weather")

    #gen.exclude_sensor (["model", "uid"])
    gen.include_sensor (["model", "uid"])
    gen.load_json_sensor_ids (MTTQ_PAYLOAD_TEXT)

    sensor_ids = gen.build_range_list (sensor_id=SENSOR_ID, count=2)

    gen.generate (sensor_ids)

################################################################################

if __name__ == "__main__" :
    main ()
