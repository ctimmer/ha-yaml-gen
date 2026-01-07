#
import time
from datetime import datetime
import socket
import netifaces
import json
import paho.mqtt.publish as publish
import psutil

HOSTNAME = socket.gethostname ()
HOSTID = "host_stats_3"
HOSTID = "host_stats_backupserver"
CPU_TEMP_PATH = "/sys/devices/virtual/thermal/thermal_zone0/temp"
CPU_FREQ_PATH = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"
CPU_TEMP_WARN = None
FAN_PATH = "/sys/class/thermal/cooling_device0/cur_state"
MEMORY_TOT = None
MEMORY_AVAIL_WARN = None
MEMORY_PATH = "/proc/meminfo"

DISK_TOTAL = None
DISK_WARN_LEVEL = None
DISK_CRITICAL_LEVEL = None

# MQTT Broker details
BROKER_ADDRESS = "localhost"    # Replace with your broker's IP or hostname
BROKER_PORT = 1883              # Default MQTT port
# Message details
TOPIC = "hoststats/" + HOSTID
#TOPIC = "enviro/test"
HA_USERNAME = "ha"
HA_PASSWORD = "hapassword"

CAPTURE_INTERVAL = 1        # sample seconds
REPORT_INTERVAL = 10        # report seconds

next_report_time = None
stat_data = None
stat_data_aux = None

MEMORY_STAT_LIST = {
    "MemTotal:" : "mem_tot" ,
    "MemAvailable:" : "mem_avail" ,
    "SwapCached:" : "swap_cached" ,
    "SwapTotal:" : "swap_tot" ,
    "SwapFree:" : "swap_free"
    }
def get_memory_stats (stats) :
    memory_data = {}
    with open(MEMORY_PATH, "r") as f:
        mem_stat = f.readline ()
        while mem_stat :
            #print (mem_stat)
            mem_fields = mem_stat.split ()
            if mem_fields[0] in MEMORY_STAT_LIST :
                #print (mem_fields)
                mem_id = MEMORY_STAT_LIST [mem_fields[0]]
                #print (mem_id)
                stats [mem_id] = int (mem_fields[1])
                '''
                if mem_id == "mem_tot" :
                    stats ["mem_tot"] = int (mem_fields[1])
                elif mem_id == "mem_avail" :
                    stats ["mem_avail"] = int (mem_fields[1])
                '''
            mem_stat = f.readline ()
    if "mem_avail" in stats \
    and "mem_tot" in stats :
        stats ["mem_tot"] = stats ["mem_tot"] // 1000
        stats ["mem_avail"] = stats ["mem_avail"] // 1000
        stats ["mem_used"] = stats ["mem_tot"] - stats ["mem_avail"]
        #print ("used:",stats ["mem_used"])
    stats ["swap_used"] = stats ["swap_tot"] - stats ["swap_free"]
    #print ("mem:", stats)

def get_stats () -> dict :
    stats = {}
    data = None
    with open(CPU_FREQ_PATH, "r") as f:
        data = f.read()
    stats ["cpu_freq"] = int(data)
    with open(CPU_TEMP_PATH, "r") as f:
        data = f.read()
    stats ["cpu_temp"] = int(data) // 1000
    get_memory_stats (stats)
    #print ("stats:", stats)
    return stats

def get_cpu_times():
    with open('/proc/stat', 'r') as f:
        line = f.readline()
    parts = line.split()
    # user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice
    cpu_times = [int(x) for x in parts[1:]]
    return sum(cpu_times), cpu_times[3] # total_time, idle_time

def add_disk_stats () :
    global stat_data
    global DISK_TOTAL
    global DISK_WARN_LEVEL
    global DISK_CRITICAL_LEVEL
    disk_info = psutil.disk_usage("/")
    if DISK_TOTAL is None :
        DISK_TOTAL =  disk_info.total // (1024**3)
        DISK_WARN_LEVEL = int (DISK_TOTAL * 0.70)
        DISK_CRITICAL_LEVEL = int (DISK_TOTAL * 0.85)
    stat_data ["disk_total"] = DISK_TOTAL
    stat_data ["disk_used"]  = disk_info.used // (1024**3)
    stat_data ["disk_free"] = disk_info.free // (1024**3)
    stat_data ["disk_warn_level"] = DISK_WARN_LEVEL
    stat_data ["disk_critical_level"] = DISK_CRITICAL_LEVEL

def init_stats (stats) :
    global stat_data
    global stat_data_aux
    global HOSTNAME
    global MEMORY_AVAIL_WARN
    stat_data = {
        "hostname" : HOSTNAME ,
        "datetime" : None ,
        "cpu_temp_min" : stats["cpu_temp"] ,
        "cpu_temp_max" : stats["cpu_temp"] ,
        "cpu_temp_max_warn" : CPU_TEMP_WARN ,
        "cpu_temp_avg" : stats["cpu_temp"] ,
        "cpu_freq_min" : stats["cpu_freq"] ,
        "cpu_freq_max" : stats["cpu_freq"] ,
        "cpu_freq_avg" : stats["cpu_freq"] ,
        "cpu_load" : 0 ,
        "cpu_load_min" : None ,
        "cpu_load_max" : None ,
        "mem_tot" : MEMORY_TOT ,
        "mem_avail_min" : stats ["mem_avail"] ,
        "mem_avail_max" : stats ["mem_avail"] ,
        "mem_avail_min_warn" : MEMORY_AVAIL_WARN ,
        "mem_used_avg" : stats ["mem_used"] ,
        "mem_used_min" : stats ["mem_used"] ,
        "mem_used_max" : stats ["mem_used"] ,
        #"mem_used_min_warn" : MEMORY_AVAIL_WARN ,
        "mem_used_avg" : stats ["mem_used"] ,
        "disk_total" : 0 ,
        "disk_used" : 0 ,
        "disk_total" : 0 ,
        "readings" : 1
        }
    stat_data_aux = {
        "cpu_temp_tot" : stats["cpu_temp"] ,
        "cpu_freq_tot" : stats["cpu_freq"] ,
        "cpu_total_time" : [0, 0] ,
        "cpu_idle_time" : [0, 0] ,
        "cpu_curr_total_time" : 0 ,
        "cpu_curr_idle_time" : 0 ,
        "mem_avail_tot" : stats ["mem_avail"]
        }
    stat_data_aux ["cpu_total_time"][0], stat_data_aux ["cpu_idle_time"][0] \
        = get_cpu_times ()
    stat_data_aux ["cpu_curr_total_time"] \
        = stat_data_aux ["cpu_total_time"][0]
    stat_data_aux ["cpu_curr_idle_time"] \
        = stat_data_aux ["cpu_idle_time"][0]

def report_stats (stats) :
    global stat_data
    stat_data ["datetime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if stat_data ["readings"] > 1 :
        stat_data ["cpu_temp_avg"] = stat_data_aux ["cpu_temp_tot"] \
                                        // stat_data ["readings"]
        stat_data ["cpu_freq_avg"] = stat_data_aux ["cpu_freq_tot"] \
                                        // stat_data ["readings"]
        stat_data ["mem_avail_avg"] = stat_data_aux ["mem_avail_tot"] \
                                        // stat_data ["readings"]
    stat_data_aux ["cpu_total_time"][1], stat_data_aux ["cpu_idle_time"][1] \
        = get_cpu_times ()
    if stat_data_aux ["cpu_total_time"][1] \
        > stat_data_aux ["cpu_total_time"][0] :
        cpu_total = stat_data_aux ["cpu_total_time"][1] \
                    - stat_data_aux ["cpu_total_time"][0]
        cpu_idle = stat_data_aux ["cpu_idle_time"][1] \
                    - stat_data_aux ["cpu_idle_time"][0]
        stat_data ["cpu_load"]  = (((cpu_total - cpu_idle) * 100) // cpu_total)
    #print ("aux:",stat_data_aux)
    #print ("Sending:", stat_data)
    add_disk_stats ()
    try:
        if True :
            print ("report_stats")
            print ("host/port", BROKER_ADDRESS, BROKER_PORT)
            print ("topic", TOPIC)
            print ("username/password", HA_USERNAME, HA_PASSWORD)
            print ("payload", stat_data)
        payload = json.dumps (stat_data)
        # Publish a single message
        ret = publish.single (TOPIC ,
                        payload = payload ,
                        qos = 1 ,
                        hostname = BROKER_ADDRESS ,
                        port = BROKER_PORT ,
                        auth = {'username' : HA_USERNAME ,
                                'password' : HA_PASSWORD})
        #print ("rep_stats: ret:", ret)
    except Exception as e:
        print(f"An error occurred: {e}")
    init_stats (stats)

def update_reading (stats) :
    global stat_data
    # CPU temperature
    if stats["cpu_temp"] > stat_data ["cpu_temp_max"] :
        stat_data ["cpu_temp_max"] = stats["cpu_temp"]
    elif stats["cpu_temp"] < stat_data ["cpu_temp_min"] :
        stat_data ["cpu_temp_min"] = stats["cpu_temp"]
    stat_data_aux ["cpu_temp_tot"] += stats["cpu_temp"]

    # CPU Load
    cpu_total_time, cpu_idle_time = get_cpu_times ()
    cpu_total = cpu_total_time - stat_data_aux ["cpu_curr_total_time"]
    if cpu_total > 0 :
        cpu_idle = cpu_idle_time - stat_data_aux ["cpu_curr_idle_time"]
        cpu_load  = (((cpu_total - cpu_idle) * 100) // cpu_total)
        if stat_data ["cpu_load_min"] is None :
            stat_data ["cpu_load_min"] = cpu_load
            stat_data ["cpu_load_max"] = cpu_load
        elif cpu_load < stat_data ["cpu_load_min"] :
            stat_data ["cpu_load_min"] = cpu_load
        elif cpu_load > stat_data ["cpu_load_max"] :
            stat_data ["cpu_load_max"] = cpu_load
        stat_data_aux ["cpu_curr_total_time"] = cpu_total_time
        stat_data_aux ["cpu_curr_idle_time"] = cpu_idle_time

    # CPU frequency
    if stats["cpu_freq"] > stat_data ["cpu_freq_max"] :
        stat_data ["cpu_freq_max"] = stats["cpu_freq"]
    elif stats["cpu_freq"] < stat_data ["cpu_freq_min"] :
        stat_data ["cpu_freq_min"] = stats["cpu_freq"]
    stat_data_aux ["cpu_freq_tot"] += stats["cpu_freq"]
    # Memory
    if stats["mem_avail"] > stat_data ["mem_avail_max"] :
        stat_data ["mem_avail_max"] = stats["mem_avail"]
    elif stats["mem_avail"] < stat_data ["mem_avail_min"] :
        stat_data ["mem_avail_min"] = stats["mem_avail"]
    if stats["mem_used"] > stat_data ["mem_used_max"] :
        stat_data ["mem_used_max"] = stats["mem_used"]
    elif stats["mem_used"] < stat_data ["mem_used_min"] :
        stat_data ["mem_used_min"] = stats["mem_used"]
    stat_data_aux ["mem_avail_tot"] += stats["mem_avail"]
    stat_data ["swap_tot"] = stats ["swap_tot"]
    stat_data ["swap_free"] = stats ["swap_free"]
    stat_data ["swap_used"] = stats ["swap_used"]
    # Other
    stat_data ["readings"] += 1

def init (stats) :
    global stat_data
    global TOPIC
    global CPU_TEMP_WARN
    global MEMORY_TOT
    global MEMORY_AVAIL_WARN
    #TOPIC = TOPIC + HOSTNAME
    CPU_TEMP_WARN = 70
    MEMORY_TOT = stats["mem_tot"]
    MEMORY_AVAIL_WARN = int (MEMORY_TOT * 0.25)

def get_ip () :
#def get_wifi_ip_netifaces():
    # Get the name of the default network interface
    gws = netifaces.gateways()
    iface = gws['default'][netifaces.AF_INET][1]
    
    # Get the IP address for that interface
    ip_info = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]
    IP = ip_info['addr']
    return IP
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except socket.error:
        return "?.?.?.?"

def main():
    global stat_data
    global next_report_time
    print (get_ip())
    stats = get_stats ()
    init (stats)
    init_stats (stats)
    next_report_time = time.time () + REPORT_INTERVAL
    while True :
        stats = get_stats ()
        update_reading (stats)
        if time.time () >= next_report_time :
            report_stats (stats)
            next_report_time = time.time () + REPORT_INTERVAL
        time.sleep (2)
        
if __name__ == "__main__":
    main()

