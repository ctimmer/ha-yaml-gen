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

from ha_yaml_gen import HaYamlGen

# Output from pimironi enviro indoor device
# edited for readability
MTTQ_PAYLOAD_TEXT = \
'''
#
# Pimironi enviro indoor json example
#
{
  "nickname": "living-room-sensor",
  "model": "indoor",
  "uid": "e6614c775b8c4035",
  "timestamp": "2023-10-27T14:30:00Z",
  "readings": {
    "temperature": 22.45,
    "humidity": 45.12,
    "pressure": 1013.25,
    "gas_resistance": 125000,
    "light": 150.5,
    "voltage": 4.95
  }
}
'''

PACKAGE_ID = "indoor"
MQTT_TOPIC_BASE = "enviro/"

ROOM_LIST = [
    "kitchen" ,
    "living_room" ,
    "bedroom_up" ,
    "bedroom_down_1" ,
    "bedroom_down_2" ,
    "bathroom_up" ,
    "bathroom_down" ,
    "entry" ,
    "laundry_room" ,
    "upstairs" ,
    "computer_room" ,
    "crawl_space"
    ]

gen = HaYamlGen (package = PACKAGE_ID ,
                 mqtt_topic_base = MQTT_TOPIC_BASE)

gen.exclude_sensor (["model",               # Skip generation of these json values
                     "uid",
                     "readings.voltage"])

gen.load_json_sensor_ids (MTTQ_PAYLOAD_TEXT)  # Generate sensors template variables

if True :
    gen.build_id_list (ids = ROOM_LIST)     # Room name suffixes
else :
    gen.build_range_list (start = 0,        # integer suffixes
                          count = len (ROOM_LIST))

gen.add_ha_template ("indoor.tmpl")
gen.add_card_template ("indoor.card")

gen.generate ()
