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

# Output from a test application (raspstats.py)
# edited for readability
MTTQ_PAYLOAD_TEXT = \
'''
#
# Load process skips everything up to the first left curly bracket
#
{
"hostname": "hostname",
"datetime": "2026-02-03 11:51:28",
"cpu_temp_min": 39,
"cpu_temp_max": 40,
"cpu_temp_warn": 60,
"cpu_temp_alert": 70,
"cpu_temp_avg": 39,
"cpu_load": 7,
"cpu_load_min": 5,
"cpu_load_max": 9,
"mem_tot": 16600,
"mem_used_avg": 10142,
"mem_used_min": 10131,
"mem_used_max": 10142,
"mem_used_warn": 13280,
"mem_used_alert": 14940,
"disk_total": 1877,
"disk_used": 115, 
"disk_used_warn": 1313,
"disk_used_alert": 1595,
"readings": 6,
"swap_tot": 16768368,
"swap_used": 0
}
'''

PACKAGE_ID = "host_stats"
MQTT_TOPIC_BASE = "hoststats/"

PACKAGE_IDX_START = 0
PACKAGE_COUNT = 2

gen = HaYamlGen (package = PACKAGE_ID ,
                 mqtt_topic_base = MQTT_TOPIC_BASE)

if False :
    gen.exclude_sensor (["cpu_load" ,
                        "cpu_load_min" ,
                        "cpu_load_max"])
if False :
    gen.include_sensor (["cpu_load" ,
                        "cpu_load_min" ,
                        "cpu_load_max"])

if True :
    gen.load_json_sensor_ids (MTTQ_PAYLOAD_TEXT)
else :
    gen.load_json_sensor_file ("raspstats.json")

if True :
    gen.build_range_list (start = PACKAGE_IDX_START ,
                            count = PACKAGE_COUNT)
else :
    gen.build_id_list (ids=["mainserver",
                            "backupserver"])

gen.add_card_template ("host_stats.card", "test")
gen.add_ha_template ("host_stats.tmpl")

gen.generate ()
