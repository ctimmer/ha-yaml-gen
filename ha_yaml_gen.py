# -*-coding:utf-8 -*-
#
################################################################################
# The MIT License (MIT)
#
# Copyright (c) 2026 Curt Timmerman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
################################################################################
#
#import time
from datetime import datetime
import io
import json
import re
import pprint

MQTT_SENSOR_HEADERS = \
'''

###### Begin: {{package}} Sensors ######
######    At: {{timestamp}}
# MQTT SENSORS
mqtt:
  sensor:
'''
TEMPLATE_SENSOR_HEADERS = \
'''

###### Begin: {{package}} Templates ######
######    At: {{timestamp}}
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
                package = "test_package" ,
                mqtt_topic_base = "test/" ,
                template_pattern = TMPL_VAR_RE) :
        self.package = package
        self.package_items = []
        self.package_data = None
        self.mqtt_topic_base = mqtt_topic_base
        self.template_variables = {}
        self.sensor_include_list = None
        self.sensor_exclude_list = []
        self.template_pattern = template_pattern
        self.yaml_indent = ""
        self.sensor_ids = {}
        self.sensor_id_list = None
        self.card_templates = None
        self.ha_templates = None

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

    def card_pro_sensor_vars (self) : #, suffix="_0") :
        package_id = self.package_data ["package"]
        self.template_variables = {"_PACKAGE_" : package_id ,
                                    "_TIMESTAMP_" : self.package_data ["timestamp"]}
        dest_dict = self.template_variables
        for _, (sensor_name, sensor_data) in enumerate (self.sensor_ids.items ()) :
            dest_dict [sensor_name] = sensor_data ["entity"]    # json ref
            entity = "sensor.{}_{}".format (self.package_data ["package"], sensor_name)
            # HA sensor values
            dest_dict [sensor_name + "_value"] = "states('{}')".format (entity)
            # Card Pro values
            dest_dict [sensor_name + "_ent"] = entity
            dest_dict [sensor_name + "_state"] = '${{states["{}"].state}}'.format (entity)
            dest_dict [sensor_name + "_id"] = '${{states["{}"].entity_id}}'.format (entity)
            dest_dict [sensor_name + "_type"] = sensor_data ["type"]
        #pprint.pprint(self.template_variables, width=2)

    def initialize (self) :
        self.sensor_id_list = {}
        self.sensor_ids = {}

    def exclude_sensor (self,
                        sensor_ids : str | list) :
        # Add sensor id(s) to exclude list
        sensor_list = None
        if isinstance (sensor_ids, str) :
            sensor_list = [sensor_ids]          # string input
        elif isinstance (sensor_ids, list) :
            sensor_list = sensor_ids            # list input
        else :
            # handle error?
            return 0
        for _, sensor_id in enumerate (sensor_list) :
            sensor_elements = sensor_id.split (".")
            sensor_id = sensor_elements [-1]    # only test the last element
            if sensor_id in self.sensor_exclude_list :
                continue
            self.sensor_exclude_list.append (sensor_id)
    def include_sensor (self,
                        sensor_ids : str | list) :
        # Add sensor id(s) to include list
        sensor_list = None
        if isinstance (sensor_ids, str) :
            sensor_list = [sensor_ids]
        elif isinstance (sensor_ids, list) :
            sensor_list = sensor_ids
        else :
            # handle error?
            return
        if self.sensor_include_list is None :
            self.sensor_include_list = []
        for _, sensor_id in enumerate (sensor_list) :
            sensor_elements = sensor_id.split (".")
            for _, element in enumerate (sensor_elements) :
                if element in self.sensor_include_list :
                    continue
                self.sensor_include_list.append (element)
        print (self.sensor_include_list)

    def sensor_is_included (self,
                            sensor_id : str) -> bool :
        # return true if sensor is to be included
        if sensor_id in self.sensor_exclude_list :
            return False
        if self.sensor_include_list is not None :
            if sensor_id not in self.sensor_include_list :
                return False
        return True
    def build_sensor_path (self, sensor_id, path) :
        if len (path) <= 0 :
            return sensor_id
        return path + "." + sensor_id

    def load_sensor_ids (self ,
                        payload : dict ,
                        path : str = "" ,
                        sensor_count : int = 0) :
        #print ("payload:", payload, path)
        for _, (s_id, s_data) in enumerate (payload.items()) :
            # Set sensor code based on data type
            sensor_path = self.build_sensor_path (s_id, path)
            if not self.sensor_is_included (s_id) :
                print ("Skipping:", sensor_path)
                continue
            # Handle number and booleans
            if isinstance (s_data, (int, float, bool)) :
                s_id = self.get_unique_id (s_id)
                self.sensor_ids [s_id] = {
                    "entity" : sensor_path ,
                    "type" : MQTT_SENSOR_MEASUREMENT    # default
                    }
                sensor_count += 1
            # Handle string and lists
            elif isinstance (s_data, (str, list)) :
                s_id = self.get_unique_id (s_id)
                self.sensor_ids [s_id] = {
                    "entity" : sensor_path ,
                    "type" : MQTT_SENSOR_BASIC    # default for array
                    }
                sensor_count += 1
            # Handle dictionary
            elif isinstance (s_data, dict) :
                sensor_count = self.load_sensor_ids (s_data,
                                                    sensor_path,
                                                    sensor_count)
            # Skip all other types
            else :
                pass
        return sensor_count

    def load_json_sensor_ids (self, json_text) :
        self.initialize ()
        # Strip leading/trailing text (documentation)
        start_idx = json_text.find ("{")
        if start_idx < 0 :
            print ("JSON text missing: '{'")
            return 0
        end_idx = json_text.rfind ("}")
        if end_idx < 0 :
            print ("JSON text missing: '}'")
            return 0
        try :
            json_dict = json.loads (json_text [start_idx:(end_idx + 1)])
        except :
            print ("JSON parse error")
            return None
        return self.load_sensor_ids (json_dict)

    def load_json_sensor_file (self, json_file_name) :
        json_text = None
        with open (json_file_name, "r") as json_file :
            json_text = json_file.read ()
        return self.load_json_sensor_ids (json_text)

    def generate (self) :
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for _, package_item in enumerate (self.package_items) :
            self.package_data = {
                "package" : self.package + package_item ["suffix"] ,
                "suffix" : package_item ["suffix"] ,
                "timestamp" : timestamp
                }
            #print (self.package_data)
            self.build_package_files ()

    def build_package_files (self) :
        package_id = self.package_data ["package"]
        #self.template_variables = {}
        self.card_pro_sensor_vars ()
        yaml_file_name = package_id + "_pkg.yaml"
        with open (yaml_file_name, "w") as yaml_file :
            self.generate_mqtt_sensors (yaml_file)
            self.generate_ha_templates (yaml_file)
        self.generate_cards (package_id)

    def generate_mqtt_sensors (self, yaml_file) :
        package_id = self.package_data ["package"]
        #self.card_pro_sensor_vars ()
        #yaml_file_name = package_id + "_pkg.yaml"
        #yaml_file = open (yaml_file_name, "w")
        with io.StringIO (MQTT_SENSOR_HEADERS) as t_buff :
            for t_line in t_buff :
                out_line = self.render_template_line (t_line, self.package_data)
                yaml_file.write (out_line)
        for _, (sensor_id,_) in enumerate (self.sensor_id_list.items()) :
            sensor_vars = {
                "NAME" : package_id + " " + sensor_id ,
                "ENTITY" : self.template_variables [sensor_id] ,
                "UNIQUE_ID" : package_id + "_" + sensor_id ,
                "STATE_TOPIC" : self.mqtt_topic_base + package_id
                }
            sensor_template = self.template_variables [sensor_id + "_type"]
            with io.StringIO (sensor_template) as s_buff :
                for sensor_line in s_buff :
                    out_line = self.render_template_line (sensor_line, sensor_vars)
                    yaml_file.write (out_line)

    def render_template_line (self ,
                        template : str ,
                        template_vars : dict = {}) -> str :
        # Template variable substitution function
        def handle_variable (match) :
            var_name = match.group(0)[2:][:-2]  # strip leading '{{' and ending '}}'
            if var_name not in template_vars :
                return match.group(0)           # return original text
            return template_vars [var_name]     # return substitute value
        # Return indentation + rendered template
        return self.yaml_indent + re.sub (self.template_pattern,
                                            handle_variable,
                                            template)

    def add_sensor_type (self,
                        sensor_id : str ,
                        sensor_type : str = "default") :
        if sensor_id not in self.sensor_id_list :
            print ("No sensor", sensor_id)
            return
        type = sensor_type
        if type not in MQTT_SENSOR_TEMPLATES :
            type = "default"
        self.sensor_id_list [sensor_id]["type"] = MQTT_SENSOR_TEMPLATES [type]

    def add_ha_template (self,
                           template_file_name) :
        template_text = None
        with open (template_file_name, "r") as t_file :
            template_text = t_file.read ()
        if self.ha_templates is None :
            self.ha_templates = []
        self.ha_templates.append ({
            "text" : template_text
            })
        #pprint.pprint (self.ha_templates)
        
    def generate_ha_templates (self, yaml_file) :
        if self.ha_templates is None :
            return
        #print ("#######", self.package_data)
        with io.StringIO (TEMPLATE_SENSOR_HEADERS) as t_buff :
            for t_line in t_buff :
                out_line = self.render_template_line (t_line, self.package_data)
                yaml_file.write (out_line)
        for ha_idx, ha_data in enumerate (self.ha_templates) :
            with io.StringIO (ha_data["text"]) as t_buff :
                for t_line in t_buff :
                    out_line = self.render_template_line (t_line, self.template_variables)
                    yaml_file.write (out_line)
            yaml_file.write ("###### End Templates ######\n")

    def add_card_template (self,
                           template_file_name,
                           card_suffix = "") :
        template_text = None
        suffix = card_suffix
        if len (suffix) > 0 :
            if suffix [0:1] != "_" :
                suffix = "_" + suffix
        with open (template_file_name, "r") as t_file :
            template_text = t_file.read ()
        if self.card_templates is None :
            self.card_templates = []
        self.card_templates.append ({
            "text" : template_text ,
            "suffix" : suffix
            })
        #pprint.pprint (self.card_templates)
        
    def generate_cards (self, package_id) :
        if self.card_templates is None :
            return
        for card_idx, card_data in enumerate (self.card_templates) :
            card_file_name = package_id + "_card" + card_data["suffix"] + ".yaml"
            #print (card_file_name)
            with open (card_file_name, "w") as out_file :
                with io.StringIO(card_data["text"]) as t_buff :
                    for card_line in t_buff :
                        out_line = self.render_template_line (card_line, self.template_variables)
                        out_file.write (out_line)

    def build_range_list (self, start = 0, count = 1) :
        for range_idx in range (start, (start + count)) :
            self.package_items.append ({
                "suffix" : "_" + str (range_idx)
                })

    def build_id_list (self, ids) :
        for _,id in enumerate (ids) :
            self.package_items.append ({
                "suffix" : "_" + id
                })

#
################################################################################
# main
################################################################################

def main () :

    # Output from Pimironi enviro outdoor weather sensors
    # JSON text edited for readability
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

    PACKAGE_ID = "weather"
    MQTT_PATH_BASE = "enviro/"
    PACKAGE_IDX_START = 0
    PACKAGE_COUNT = 2

    gen = HaYamlGen (package = PACKAGE_ID ,
                     mqtt_topic_base = MQTT_PATH_BASE)

    #gen.exclude_sensor (["model", "uid", "readings.luminance"])
    #gen.include_sensor (["model", "uid", "readings.temperature"])
    gen.load_json_sensor_ids (JSON_PAYLOAD_TEXT)

    if True :
        gen.build_range_list (start = PACKAGE_IDX_START,
                                count = PACKAGE_COUNT)
    else :
        gen.build_id_list (ids=["backdoor", "garage"])

    gen.generate ()

################################################################################

if __name__ == "__main__" :
    main ()
