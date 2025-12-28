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
import io
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
                package = "test_package" ,
                mqtt_topic_base = "test/" ,
                template_pattern = TMPL_VAR_RE) :
        self.package = package
        self.mqtt_topic_base = mqtt_topic_base
        self.template_variables = {}
        self.sensor_include_list = None
        self.sensor_exclude_list = []
        self.template_pattern = template_pattern
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

    def card_pro_sensor_vars (self, suffix="_0") :
        dest_dict = self.template_variables
        package_id = self.package + suffix
        for _, (sensor_name, sensor_data) in enumerate (self.sensor_ids.items ()) :
            entity = sensor_data ["entity"]
            dest_dict [sensor_name] = "sensor." + entity    # json ref
            entity = "sensor.{}_{}".format (package_id, entity)
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
    def build_sensor_path (self, sensor_id, path) :
        if len (path) <= 0 :
            return sensor_id
        return path + "." + sensor_id

    def load_sensor_ids (self, payload, path="") :
        #print ("payload:", payload, path)
        for _, (s_id, s_data) in enumerate (payload.items()) :
            # Set sensor code based on data type
            new_path = path
            if len (new_path) > 0 :
                new_path += "."
            #print ("PARSE: s_id", s_id, s_data)
            if isinstance (s_data, (int, float, bool)) :
                if not self.sensor_is_included (self.build_sensor_path (s_id, path)) :
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

    def build_package_files (self, package_data) :
        suffix = package_data ["suffix"]
        package_id = self.package + suffix
        self.template_variables = {}
        self.card_pro_sensor_vars (suffix = suffix)
        yaml_file_name = package_id + "_pkg.yaml"
        yaml_file = open (yaml_file_name, "w")
        yaml_file.write (MQTT_SENSOR_HEADERS)
        for _, (sensor_id,_) in enumerate (self.sensor_id_list.items()) :
            self.mqtt_template_variables = {
                "NAME" : package_id + " " + sensor_id ,
                "ENTITY" : self.template_variables [sensor_id] ,
                "UNIQUE_ID" : package_id + "_" + sensor_id ,
                "STATE_TOPIC" : self.mqtt_topic_base + package_id
                }
            sensor_text = self.template_variables [sensor_id + "_type"]
            out_line = re.sub (self.template_pattern, self.mqtt_sub_var, sensor_text)
            yaml_file.write (out_line)
        self.generate_ha_templates (package_id, yaml_file)
        yaml_file.close ()
        self.generate_cards (package_id)

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

    def generate (self, package_items) :
        #print ("gen:", package_items)
        for _, (sensor_id,_) in enumerate (self.sensor_id_list.items()) :  # temporary fix
            self.add_sensor_type (sensor_id)
        for _, package_data in enumerate (package_items) :
            self.build_package_files (package_data)

    def add_ha_template (self,
                           template_file_name,
                           template_suffix = "") :
        template_text = None
        suffix = template_suffix
        if len (suffix) > 0 :
            if suffix [0:1] != "_" :
                suffix = "_" + suffix
        with open (template_file_name, "r") as t_file :
            template_text = t_file.read ()
        if self.ha_templates is None :
            self.ha_templates = []
        self.ha_templates.append ({
            "text" : template_text ,
            "suffix" : suffix           # this is not needed?
            })
        #pprint.pprint (self.ha_templates)
        
    def generate_ha_templates (self, package_id, yaml_file) :
        if self.ha_templates is None :
            return
        yaml_file.write (TEMPLATE_SENSOR_HEADERS)
        for template_idx, template_data in enumerate (self.ha_templates) :
            # probably need some code here
            pass
        return

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
            card_file_name = package_id + "_card" + card_data["suffix"] + ".txt"
            print (card_file_name)
            out_file = open (card_file_name, "w")
            t_buff = io.StringIO(card_data["text"])
            #self.mqtt_template_variables = self.template_variables
            card_line = t_buff.readline ()
            while card_line :
                out_line = re.sub (self.template_pattern, self.sub_var, card_line)
                out_file.write (out_line)
                #print (card_line)
                card_line = t_buff.readline ()
            out_file.close ()

    def build_range_list (self, start = 0, count = 1) :
        package_list = []
        for range_idx in range (start, (start + count)) :
            package_list.append ({
                "suffix" : "_" + str (range_idx)
                })
        return package_list
    def build_id_list (self, ids) :
        package_list = []
        for _,id in enumerate (ids) :
            package_list.append ({
                "suffix" : "_" + id
                })
        return package_list
#
################################################################################
# main
################################################################################

def main () :

    # Output from Pimironi enviro outdoor weather sensors
    # JSON text edited for readability
    MTTQ_PAYLOAD_TEXT = \
'''{
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

    PACKAGE_ID = "enviro_weather"
    MQTT_PATH_BASE = "enviro/"
    PACKAGE_IDX_START = 0
    PACKAGE_COUNT = 1

    gen = HaYamlGen (package = PACKAGE_ID ,
                     mqtt_topic_base = MQTT_PATH_BASE)

    #gen.exclude_sensor (["model", "uid"])
    #gen.include_sensor (["model", "uid"])
    gen.load_json_sensor_ids (MTTQ_PAYLOAD_TEXT)

    if True :
        package_data = gen.build_range_list (start = PACKAGE_IDX_START,
                                            count = PACKAGE_COUNT)
    else :
        package_data = gen.build_id_list (ids=["kitchen", "bedroom"])
    gen.generate (package_data)

    #gen.generate_cards (package_data)

################################################################################

if __name__ == "__main__" :
    main ()
