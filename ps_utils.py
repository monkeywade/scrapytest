# ! /usr/bin/python3
# -*- coding: utf-8 -*-

import psutil
import sys
import os
import time


class PsUtil:
    def __init__(self, pid, counts):
        self.pid = pid
        self.count = counts

    def cpu_statistic(self):
        p = psutil.Process(self.pid)
        cpu_percent = []
        for i in range(self.count):
            p_cpu_sts = p.cpu_percent(interval=1.0)
            cpu_percent.append(p_cpu_sts)
            print(p_cpu_sts)
        cpu_avg = sum(cpu_percent) / len(cpu_percent)
        print("cpu avg is " + str(cpu_avg))

    def proc_statistic(self):
        p = psutil.Process(self.pid)
        count = 0
        command = "jstat -gcutil %s |grep -v FGC |awk '{print $9}'" % self.pid
        gc_sts_old = int(os.popen(command).read().strip())
        print("count", "CPU", "MEM", "GC_TIMES", sep=",")
        while True:
            p_cpu_sts = p.cpu_percent(interval=1.0)
            p_mem_sts = p.memory_percent()
            gc_sts_new = os.popen(command).read().strip()
            gc_sts = int(gc_sts_new) - gc_sts_old
            time.sleep(1)
            count += 1
            gc_sts_old = int(gc_sts_new)
            print(count, p_cpu_sts, p_mem_sts, gc_sts, sep=",")


def check_sysargv():
    try:
        if sys.argv[1] and sys.argv[2]:
            return True
        else:
            return False

    except IndexError:
        return False


if __name__ == "__main__":
    if not check_sysargv():
        print("Usage: add pid and counts for args, like %s 1233 10" % sys.argv[0])
        sys.exit(0)
    pid = int(sys.argv[1])
    counts = int(sys.argv[2])
    ps_util = PsUtil(pid, counts)
    ps_util.proc_statistic()
