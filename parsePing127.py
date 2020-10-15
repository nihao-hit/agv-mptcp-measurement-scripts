# PING 30.113.127.254 (30.113.127.254) from 30.113.127.1 wlan1: 56(84) bytes of data.
# 127子网是wlan1
import numpy as np
import re
import random
import os
import time
import functools
import pandas as pd

import Status
import calcTime

def parsePing127(ping127File):
    count = 0
    with open(ping127File, 'r') as f:
        # PING 30.113.127.254 (30.113.127.254) from 30.113.127.1 wlan1: 56(84) bytes of data.
        # [1564962975.788517] 64 bytes from 30.113.127.254: icmp_seq=43 ttl=64 time=280 ms
        # [1564962986.739622] From 30.113.127.1 icmp_seq=51 Destination Host Unreachable
        for line in f.readlines():
            if 'time' in line:
                try:
                    #####################################################
                    # 从文件中提取数据，赋值变量
                    timestamp = int(float(re.findall('(?<=\[).*?(?=\])', line)[0]))
                    rtt = int(float(re.findall('(?<=time=).*?(?= )', line)[0]))
                    #####################################################
                    #####################################################
                    # 计算connStartTime, startTime与endTime
                    if calcTime.connStartTime == -1:
                        calcTime.connStartTime = timestamp
                    if calcTime.startTimes[calcTime.PING127] == -1:
                        calcTime.startTimes[calcTime.PING127] = timestamp
                    calcTime.endTimes[calcTime.PING127] = timestamp
                    #####################################################
                    #####################################################
                    pos = timestamp - calcTime.connStartTime
                    # 避免出现负数的pos污染最后时间戳的数据，直接丢弃这部分数据
                    if pos < 0:
                        continue
                    # 一秒可能有多条ping数据，选择rtt最小值记录
                    if Status.sList[pos].W1pingrtt == 0 or Status.sList[pos].W1pingrtt > rtt:
                        Status.sList[pos].W1pingrtt = rtt
                    #####################################################
                except:
                    count += 1
    print("try-except错误次数：{}".format(count))



# 返回填补统计信息
def fillPing127(sList, startTime, fillDir):
    # 按秒填充，后续处理会丢弃所有填充数据
    txTime = startTime + len(sList)
    fillTimes = []
    fillFlag = True
    for i in range(len(sList)-1, -1, -1):
        # W1pingrtt类型为int
        if sList[i].W1pingrtt == 0:
            rxTime = startTime + i
            if rxTime <= txTime:
                j = i
                while(j >= 0 and sList[j].W1pingrtt == 0):
                    j -= 1
                # txTime为缺失时段的起始第一秒
                txTime = startTime + j + 1
            # W1pingrtt单位为毫秒
            sList[i].W1pingrtt = (rxTime - txTime + 1)*1000
            if fillFlag:
                fillTimes.append([txTime, rxTime, rxTime-txTime+1])
                fillFlag = False
        else:
            fillFlag = True

    holeList = pd.DataFrame(fillTimes, columns=['start', 'end', 'duration'])
    fileName = 'fillPing127ForEvent-{}-{}.csv'.format(len(holeList), holeList['duration'].sum())
    holeList.to_csv(os.path.join(fillDir, fileName))