import Status
import calcTime

import numpy as np
import re
import math
import os
import time
import pandas as pd

def parseConn(connFile):
    count = 0
    with open(connFile, 'r') as f:
        connList = f.read()
        connList = connList.split('||')
        for conn in connList:
            try:
                time = int(float(re.findall('(?<=time\": ).*?(?=,)', conn)[0]))
    
                ############################################
                # 计算connStartTime, startTime与endTime
                if calcTime.connStartTime == -1:
                    calcTime.connStartTime = time
                if calcTime.startTimes[calcTime.CONN] == -1:
                    calcTime.startTimes[calcTime.CONN] = time
                calcTime.endTimes[calcTime.CONN] = time
                ############################################

                pos = time - calcTime.connStartTime
                # 避免出现负数的pos污染最后时间戳的数据，直接丢弃这部分数据
                if pos < 0:
                    continue
                apMac = re.findall('(?<=Access ).*?(?= )', conn)[0]
                # Quality=100/100 level=78/100 level=0/100}"}||
                # Quality=33/70 level=-77 }"}||
                # Access Not-Associated dBm}"}||
                # Access Not-Associated Quality:0 level:0 level:0}"}||
                if re.findall('Not-Associated', conn):
                    apMac = 'Not-Associated'
                    level = 0
                    channel = 0.0
                elif len(re.findall('level', conn)) == 1:
                    level = int(re.findall('(?<=level=).*?(?= )', conn)[0])
                    channel = float(re.findall('(?<=Frequency:).*?(?= )', conn)[0])
                else:
                    # 根据公式quality = (level + 110) / 70 * 100还原level为接收信号强度
                    tmp = int(re.findall('(?<=level=).*?(?=/\d+ )', conn)[0])
                    level = int(tmp * 70 / 100 - 110)
                    channel = float(re.findall('(?<=Frequency:).*?(?= )', conn)[0])
                if re.findall('(?<=dev\": \").*?(?=\")', conn)[0] == 'wlan0':
                    if Status.sList[pos].W0level == 0 or Status.sList[pos].W0level < level:
                        Status.sList[pos].W0APMac = apMac
                        Status.sList[pos].W0level = level
                        Status.sList[pos].W0channel = channel
                elif re.findall('(?<=dev\": \").*?(?=\")', conn)[0] == 'wlan1':
                    if Status.sList[pos].W1level == 0 or Status.sList[pos].W1level < level:
                        Status.sList[pos].W1APMac = apMac
                        Status.sList[pos].W1level = level
                        Status.sList[pos].W1channel = channel
                else:
                    pass
            except:
                    count += 1
    print("try-except错误次数：{}".format(count))


# 统计缺失时段
def fillConn(sList, startTime, fillDir):
    w0FillTimes = []
    w0TxTime = -1

    w1FillTimes = []
    w1TxTime = -1
    print("统计conn数据缺失时段")
    for i in range(len(sList)):
        if sList[i].W0APMac == '':
            if w0TxTime == -1:
                w0TxTime = startTime + i
        else:
            if w0TxTime != -1:
                rxTime = startTime + i - 1
                w0FillTimes.append([w0TxTime, rxTime, rxTime - w0TxTime + 1])
                # 重置w0TxTime
                w0TxTime = -1
        
        if sList[i].W1APMac == '':
            if w1TxTime == -1:
                w1TxTime = startTime + i
        else:
            if w1TxTime != -1:
                rxTime = startTime + i - 1
                w1FillTimes.append([w1TxTime, rxTime, rxTime - w1TxTime + 1])
                # 重置w1TxTime
                w1TxTime = -1
    
    print("将WLAN0的conn数据空洞写入文件")
    w0HoleDf = pd.DataFrame(w0FillTimes, columns=['start', 'end', 'duration'])
    fileName = 'w0ConnHole-{}-{}.csv'.format(len(w0HoleDf), w0HoleDf['duration'].sum())
    w0HoleDf.to_csv(os.path.join(fillDir, fileName))
    
    print("将WLAN1的conn数据空洞写入文件")
    w1HoleDf = pd.DataFrame(w1FillTimes, columns=['start', 'end', 'duration'])
    fileName = 'w1ConnHole-{}-{}.csv'.format(len(w1HoleDf), w1HoleDf['duration'].sum())
    w1HoleDf.to_csv(os.path.join(fillDir, fileName))