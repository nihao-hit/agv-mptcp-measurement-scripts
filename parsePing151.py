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
                    timestamp = int(float(re.findall('(?<=\[).*?(?=\])', line)[0]))
                    ############################################
                    # 计算connStartTime, startTime与endTime
                    if calcTime.connStartTime == -1:
                        calcTime.connStartTime = timestamp
                    if calcTime.startTimes[calcTime.PING151] == -1:
                        calcTime.startTimes[calcTime.PING151] = timestamp
                    calcTime.endTimes[calcTime.PING151] = timestamp
                    ############################################
                    rtt = int(float(re.findall('(?<=time=).*?(?= )', line)[0]))
                    pos = timestamp - calcTime.connStartTime
                    # 避免出现负数的pos污染最后时间戳的数据，直接丢弃这部分数据
                    if pos < 0:
                        continue
                    # 一秒可能有多条ping数据，选择rtt最小值记录
                    if Status.sList[pos].W0pingrtt == 0 or Status.sList[pos].W0pingrtt > rtt:
                        Status.sList[pos].W0pingrtt = rtt
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


# 返回填补统计信息
def fillPing151Forward(sList, startTime, fillDir):
    # ping机制：linux默认发包间隔为1s，默认超时时间为4s。当前时刻rtt以之前某个时刻发包，当前时刻收包计算。
    #   
    # 前向填补rtt：保留6s内的缺失时段并使用前5秒rtt均值 + 0——1s的随机值填充，
    #             7s—40s时段直接填充用于判断掉线事件，但是不计入CDF图，40s以上数据丢弃。
    # 
    # 由于经csv处理后时间戳精度为秒级，所以填补rtt误差最大为1s。
    #
    # 注意：这里避免依赖curTimestamp
    fillTimes = []
    count = 0
    
    i = 0
    while i < len(sList):
        if sList[i].W0pingrtt == 0:
            txTime = startTime + i
            j = 1
            while i < len(sList) and sList[i].W0pingrtt == 0:
                if j <= 6:
                    # 使用前5s的均值填补，5s是不是偏多，3s会不会更好一些
                    k = i-1; meanRttCount = 5
                    meanRtt = 0
                    while k >= 0 and meanRttCount > 0 and sList[k].W0pingrtt < 7000:
                        meanRtt += sList[k].W0pingrtt
                        k -= 1
                        meanRttCount -= 1
                    meanRtt /= 5-meanRttCount if meanRttCount != 5 else 1
                    # 缺失1s的填补值偏大，但是1s的缺失有可能是偶发现象又居多，修正一下
                    if j == 1:
                        sList[i].W0pingrtt = int(meanRtt)
                    else:
                        sList[i].W0pingrtt = int(meanRtt) + random.randint(0, 1000)
                else:
                    sList[i].W0pingrtt = j*1000
                i += 1
                j += 1
                # 记录填补多少次
                count += 1
            # 记录填补时段
            rxTime = startTime + i
            fillTimes.append([txTime, rxTime, rxTime-txTime])
        else:
            i += 1
    
    fileName = 'fillPing151Forward-{}.txt'.format(count)
    with open (os.path.join(fillDir, fileName), 'w') as f:
        f.write('{},\t{},\t{}\n'.format('startTime', 'endTime', 'duration'))
        for tpl in fillTimes:
            f.write('{},\t{},\t{}\n'.format(
                time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(tpl[0])),
                time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(tpl[1])),
                tpl[1] - tpl[0]
                )
            )


def fillPing151Backward(sList, startTime, fillDir):
    # 后向填补rtt：记rtt为此刻到下一次有记录的收包时刻。
    prev = 0
    flag = 0
    fillTimes = []
    count = 0
    for i in range(len(sList)):
        if sList[i].W0pingrtt > 1e-6:
            if flag:
                for j in range(1, i - prev):
                    # 离散化填补值，[-500ms, 500ms]
                    tmpRtt = j*1000
                    sList[i - j].W0pingrtt = random.randrange(tmpRtt-500, tmpRtt+500)
                    count += 1
                fillTimes.append([startTime+prev, startTime+i-1, i-prev-1])
            flag = 0
            prev = i
        else:
            flag = 1
    
    fileName = 'fillPing151Backward-{}.txt'.format(count)
    with open (os.path.join(fillDir, fileName), 'w') as f:
        f.write('{},\t{},\t{}\n'.format('startTime', 'endTime', 'duration'))
        for tpl in fillTimes:
            f.write('{},\t{},\t{}\n'.format(
                time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(tpl[0])),
                time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(tpl[1])),
                tpl[1] - tpl[0]
                )
            )


if __name__ == '__main__':
    pass