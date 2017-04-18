#!/usr/bin/python
import rrdtool, tempfile
import time
import subprocess
import re

epoch_time = int(time.time())
file_rrd = 'rpi-temp_freq-rrd.rrd'
rrd_length = 30

path_cpu_temp = '/sys/class/thermal/thermal_zone0/temp'
path_cpu_freq = '/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq'
path_gpu_temp = '/opt/vc/bin/vcgencmd'
path_gpu_temp_arg = 'measure_temp'

regex_gpu_temp = re.compile('(\d+.\d+)')

data_sources=[ 'DS:gpu_temp:GAUGE:2:0:128',
               'DS:cpu_temp:GAUGE:2:0:128',
               'DS:cpu_freq:GAUGE:2:0:1200000000' ]

rrdtool.create( file_rrd,
                 '--start', str(epoch_time),
                 '--step', '1',
                 data_sources,
                 'RRA:AVERAGE:0.5:1:%s' %(rrd_length))

for i in range(1, rrd_length+1):
  # get CPU temperature
  file_cpu_temp = open(path_cpu_temp, 'r')
  cpu_temp = float(file_cpu_temp.readline().rstrip())/1000
  file_cpu_temp.close()

  # get GPU temperature
  proc_get_gpu_temp = subprocess.Popen([path_gpu_temp, path_gpu_temp_arg], stdout=subprocess.PIPE)
  proc_get_gpu_temp_result = proc_get_gpu_temp.stdout.read()
  gpu_temp = regex_gpu_temp.search(proc_get_gpu_temp_result).group(1)

  # get CPU frequency
  file_cpu_freq = open(path_cpu_freq, 'r')
  cpu_freq = int(file_cpu_freq.readline().rstrip())
  file_cpu_freq.close()

  print 'gpu_temp: %s\ncpu_temp: %s\ncpu_freq: %s' %(gpu_temp, cpu_temp, cpu_freq)
  
  rrdtool.update(file_rrd, 'N:%s:%s:%s' %(gpu_temp, cpu_temp, cpu_freq))

  time.sleep(1) 


