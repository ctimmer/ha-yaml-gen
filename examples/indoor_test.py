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

import time
from datetime import datetime, timezone
import socket
import json
import random
import paho.mqtt.publish as publish

# MQTT Broker details
BROKER_ADDRESS = "localhost"    # Replace with your broker's IP or hostname
BROKER_PORT = 1883              # Default MQTT port
# Message details
TOPIC = "enviro/"
HA_USERNAME = "ha"
HA_PASSWORD = "hapassword"

ROOMS = {
    "indoor_living_room" : {} ,
    "indoor_kitchen" : {} ,
    "indoor_computer_room" : {}
    }

def get_payload () :
    return {
            "nickname": "NEED",
            "model": "indoor",
            "uid": "e6614c775b8c4035",
            "timestamp": "2026-01-27T14:30:00Z",
            "readings": {
                "temperature":  7.45,
                "humidity": 45.12,
                "pressure": 1013.25,
                "gas_resistance": 125000,
                "light": 150.5,
                "voltage": 4.95
                }
            }

def get_temperature_c () :
    return round (random.uniform(7.0, 30.0), 2)

def get_humidity () :
    return round (random.uniform(30.0, 60.0), 2)

def get_gas_resistance () :
    return round (random.uniform(110000.0, 140000.0))

def send_data (topic, payload_dict) :
    try:
        #if True :
        #    print ("report_stats")
        #    print ("host/port", BROKER_ADDRESS, BROKER_PORT)
        #    print ("topic", TOPIC)
        #    print ("username/password", HA_USERNAME, HA_PASSWORD)
        #    print ("payload", mqtt_payload)
        payload = json.dumps (payload_dict)
        # Publish a single message
        ret = publish.single (topic ,
                                payload = payload ,
                                qos = 1 ,
                                hostname = BROKER_ADDRESS ,
                                port = BROKER_PORT ,
                                auth = {'username' : HA_USERNAME ,
                                        'password' : HA_PASSWORD})
        #print ("rep_stats: ret:", ret)
    except Exception as e:
        print(f"An error occurred: {e}")

for _, (sensor_id, sensor_data) in enumerate (ROOMS.items()) :
    topic = TOPIC + sensor_id
    sensor_dict = get_payload ()
    now_utc_aware = datetime.now(timezone.utc)
    iso_format_string = now_utc_aware.strftime("%Y-%m-%dT%H:%M:%SZ")
    sensor_dict["nickname"] = sensor_id
    sensor_dict["timestamp"] = iso_format_string
    sensor_dict["readings"]["temperature"] = get_temperature_c ()
    sensor_dict["readings"]["humidity"] = get_humidity ()
    sensor_dict["readings"]["gas_resistance"] = get_gas_resistance ()
    print (topic, sensor_dict)
    send_data (topic, sensor_dict)

