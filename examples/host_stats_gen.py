#

from ha_yaml_gen import HaYamlGen

# Output from a test application (raspstats.py)
# edited for readability
MTTQ_PAYLOAD_TEXT = \
'''
#
# Load process skips everything up to the first left curly bracket
#
{"hostname": "localhost",
"datetime": "2025-12-24 11:51:17",
"cpu_temp_min": 39,
"cpu_temp_max": 41,
"cpu_temp_max_warn": 70,
"cpu_temp_avg": 39,
"cpu_freq_min": 1600000,
"cpu_freq_max": 3000000,
"cpu_freq_avg": 2766666,
"cpu_load": 10,
"cpu_load_min": 6,
"cpu_load_max": 16,
"mem_tot": 16608,
"mem_avail_min": 9874,
"mem_avail_max": 9881,
"mem_avail_min_warn": 4152,
"mem_avail_avg": 9877,
"mem_used_avg": 5190,
"mem_used_min": 5190,
"mem_used_max": 5206,
"disk_total": 1877,
"disk_used": 98,
"readings": 6,
"swap_tot": 16768368,
"swap_free": 16768368,
"swap_used": 0,
"disk_free": 1701,
"disk_warn_level": 1313,
"disk_critical_level": 1595}
'''

PACKAGE_ID = "host_stats"
MQTT_TOPIC_BASE = "hoststats/"

PACKAGE_IDX_START = 0
PACKAGE_COUNT = 1

gen = HaYamlGen (package = PACKAGE_ID ,
                 mqtt_topic_base = MQTT_TOPIC_BASE)

if True :
    gen.exclude_sensor (["cpu_freq_min","cpu_freq_max","cpu_freq_avg"])
else :
    gen.include_sensor (["cpu_freq_min","cpu_freq_max","cpu_freq_avg"])

if True :
    gen.load_json_sensor_ids (MTTQ_PAYLOAD_TEXT)
else :
    gen.load_json_sensor_file ("raspstats.json")

if True :
    gen.build_range_list (start = PACKAGE_IDX_START ,
                            count = PACKAGE_COUNT)
else :
    gen.build_id_list (ids=["mainserver", "backupserver"])

gen.add_card_template ("host_stats.card", "test")
gen.add_ha_template ("host_stats.tmpl")

gen.generate ()
