#!/usr/bin/python
# -*- coding: utf-8 -*-

import rrdtool, tempfile
import time
import subprocess
import re

path_rrd = 'rpi-temp_freq.rrd'
path_rrd_export = 'rpi-temp_freq.png'

rrd_length = 100
rrd_intro_length = 30
rrd_outro_length = 30
rrd_res = 1

rrd_datapoints = rrd_length / rrd_res
rrd_datapoints_intro = rrd_intro_length / rrd_res
rrd_datapoints_outro = rrd_outro_length / rrd_res

path_cpu_temp = '/sys/class/thermal/thermal_zone0/temp'
path_cpu_freq = '/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq'
path_gpu_temp = '/opt/vc/bin/vcgencmd'
path_gpu_temp_arg = 'measure_temp'

regex_gpu_temp = re.compile('(\d+.\d+)')

epoch_time = int(time.time())


data_sources=[ 'DS:gpu_temp:GAUGE:2:0:128',
               'DS:cpu_temp:GAUGE:2:0:128',
               'DS:cpu_freq:GAUGE:2:0:1200000000' ]

rrdtool.create( path_rrd,
                 '--start', str(epoch_time),
                 '--step', str(rrd_res),
                 data_sources,
                 'RRA:AVERAGE:0.5:%s:%s' %(rrd_res, rrd_datapoints))

def collect_data(datapoints):
  for i in range(1, datapoints+1):
    # get CPU temperature
    file_cpu_temp = open(path_cpu_temp, 'r')
    cpu_temp = float(file_cpu_temp.readline().rstrip())/1000
    file_cpu_temp.close()

    # get GPU temperature
    proc_get_gpu_temp = subprocess.Popen([path_gpu_temp, path_gpu_temp_arg], stdout=subprocess.PIPE)
    proc_get_gpu_temp_result = proc_get_gpu_temp.stdout.read()
    print proc_get_gpu_temp_result
    gpu_temp = regex_gpu_temp.search(proc_get_gpu_temp_result).group(1)

    # get CPU frequency
    file_cpu_freq = open(path_cpu_freq, 'r')
    cpu_freq = int(file_cpu_freq.readline().rstrip())
    file_cpu_freq.close()

    print 'gpu_temp: %s\ncpu_temp: %s\ncpu_freq: %s' %(gpu_temp, cpu_temp, cpu_freq)
  
    rrdtool.update(path_rrd, 'N:%s:%s:%s' %(gpu_temp, cpu_temp, cpu_freq))

    time.sleep(rrd_res)

print rrd_datapoints_intro
print rrd_datapoints-(rrd_datapoints_intro+rrd_datapoints_outro)
print rrd_datapoints_outro

collect_data(rrd_datapoints_intro)
subprocess.Popen(["sysbench", "--test=cpu", "--num-threads=4", "--max-requests=1048576", "--max-time=%s" %(str(rrd_datapoints-rrd_datapoints_intro-rrd_datapoints_outro)), "run"])
collect_data(rrd_datapoints-(rrd_datapoints_intro+rrd_datapoints_outro))
collect_data(rrd_datapoints_outro)

rrdtool.graph(path_rrd_export,
              '--imgformat', 'PNG',
              '--width', '960',
              '--height', '540',
              '--start', str(epoch_time),
              '--end', "-1",
              '--vertical-label', 'Temperature in C',
              '--title', 'RPI Temperature Benchmark',
              '--lower-limit', '0',
              '--right-axis', '10000000:0',
              '--right-axis-label', 'Frequency in Hz',
              'DEF:rpi-gpu_temp=rpi-temp_freq.rrd:gpu_temp:AVERAGE',
              'DEF:rpi-cpu_temp=rpi-temp_freq.rrd:cpu_temp:AVERAGE',
              'DEF:rpi-cpu_freq=rpi-temp_freq.rrd:cpu_freq:AVERAGE',
              'CDEF:scaled_rpi-cpu_freq=rpi-cpu_freq,10000,/',
              'LINE1:rpi-gpu_temp#0000FF:"gpu_temp"',
              'LINE1:rpi-cpu_temp#00FF00:"cpu_temp"',
              'LINE1:scaled_rpi-cpu_freq#FF0000:"cpu_freq"')
