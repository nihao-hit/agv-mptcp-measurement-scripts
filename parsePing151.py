# PING 30.113.151.254 (30.113.151.254) from 30.113.151.1 wlan0: 56(84) bytes of data.
# 151子网是wlan0
import numpy as np
import re
import random
import os
import time
import functools
import pandas as pd

import Status
import calcTime

def parsePing151(ping151File):
    count = 0
    with open(ping151File, 'r') as f:
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
                    if calcTime.startTimes[calcTime.PING151] == -1:
                        calcTime.startTimes[calcTime.PING151] = timestamp
                    calcTime.endTimes[calcTime.PING151] = timestamp
                    #####################################################
                    #####################################################
                    pos = timestamp - calcTime.connStartTime
                    # 避免出现负数的pos污染最后时间戳的数据，直接丢弃这部分数据
                    if pos < 0:
                        continue
                    # 一秒可能有多条ping数据，选择rtt最小值记录
                    if Status.sList[pos].W0pingrtt == 0 or Status.sList[pos].W0pingrtt > rtt:
                        Status.sList[pos].W0pingrtt = rtt
                    #####################################################
                except:
                    count += 1
    print("try-except错误次数：{}".format(count))



# 返回填补统计信息
def fillPing151ForEvent(sList, startTime, fillDir):
    # 按秒填充，后续处理会丢弃所有填充数据
    txTime = startTime + len(sList)
    fillTimes = []
    fillFlag = True
    for i in range(len(sList)-1, -1, -1):
        # W0pingrtt类型为int
        if sList[i].W0pingrtt == 0:
            rxTime = startTime + i
            if rxTime <= txTime:
                j = i
                while(j >= 0 and sList[j].W0pingrtt == 0):
                    j -= 1
                # txTime为缺失时段第一秒
                txTime = startTime + j + 1
            # W0pingrtt单位为毫秒
            sList[i].W0pingrtt = (rxTime - txTime + 1)*1000
            if fillFlag:
                fillTimes.append([txTime, rxTime, rxTime-txTime+1])
                fillFlag = False
        else:
            fillFlag = True

    holeList = pd.DataFrame(fillTimes, columns=['start', 'end', 'duration'])
    fileName = 'fillPing151ForEvent-{}-{}.csv'.format(len(holeList), holeList['duration'].sum())
    holeList.to_csv(os.path.join(fillDir, fileName))