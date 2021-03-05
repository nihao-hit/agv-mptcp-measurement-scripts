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
                #####################################################
                # 从文件中提取数据，赋值变量
                time = float(re.findall('(?<=time\": ).*?(?=,)', conn)[0])
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
                #####################################################
                #####################################################
                # 计算connStartTime, startTime与endTime
                if calcTime.connStartTime == -1:
                    calcTime.connStartTime = int(time)
                if calcTime.startTimes[calcTime.CONN] == -1:
                    calcTime.startTimes[calcTime.CONN] = int(time)
                calcTime.endTimes[calcTime.CONN] = int(time)
                #####################################################
                #####################################################
                # 解析数据写入StatusList
                pos = int(time) - calcTime.connStartTime
                # 避免出现负数的pos污染最后时间戳的数据，直接丢弃这部分数据
                if pos < 0:
                    continue
                
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
                #####################################################
            except:
                    count += 1
    print("try-except错误次数：{}".format(count))



# 2020/11/26:11: 分离StatusList与ConnStatusList数据提取
def parseConnForConnStatusList(connFile):
    count = 0
    with open(connFile, 'r') as f:
        connList = f.read()
        connList = connList.split('||')
        for conn in connList:
            try:
                #####################################################
                # 从文件中提取数据，赋值变量
                time = float(re.findall('(?<=time\": ).*?(?=,)', conn)[0])
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
                #####################################################
                #####################################################
                # 解析数据写入ConnStatusList
                connStatus = Status.ConnStatus()

                connStatus.timestamp = int(time * 1e6)

                if re.findall('(?<=dev\": \").*?(?=\")', conn)[0] == 'wlan0':
                    connStatus.W0APMac = apMac
                    connStatus.W0level = level
                    connStatus.W0channel = channel
                elif re.findall('(?<=dev\": \").*?(?=\")', conn)[0] == 'wlan1':
                    connStatus.W1APMac = apMac
                    connStatus.W1level = level
                    connStatus.W1channel = channel
                else:
                    pass

                Status.ConnStatusList.append(connStatus)
                #####################################################
            except:
                    count += 1
    print("try-except错误次数：{}".format(count))



# 统计缺失时段
# 2020/11/26:11: 基于conn测量脚本只记录基站变化的逻辑，填充data.csv
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
            
            # 2020/11/26:11: 配合进行修改
            w0StatusIdx = w0TxTime - 1 - startTime
            if w0StatusIdx >= 0 and sList[w0StatusIdx].W0APMac != 'Not-Associated':
                sList[i].W0APMac = sList[w0StatusIdx].W0APMac
                sList[i].W0channel = sList[w0StatusIdx].W0channel
                sList[i].W0level = sList[w0StatusIdx].W0level
        else:
            if w0TxTime != -1:
                rxTime = startTime + i - 1
                w0FillTimes.append([w0TxTime, rxTime, rxTime - w0TxTime + 1])
                # 重置w0TxTime
                w0TxTime = -1
        
        if sList[i].W1APMac == '':
            if w1TxTime == -1:
                w1TxTime = startTime + i
            
            # 2020/11/26:11: 配合进行修改
            w1StatusIdx = w1TxTime - 1 - startTime
            if w1StatusIdx >= 0 and sList[w1StatusIdx].W1APMac != 'Not-Associated':
                sList[i].W1APMac = sList[w1StatusIdx].W1APMac
                sList[i].W1channel = sList[w1StatusIdx].W1channel
                sList[i].W1level = sList[w1StatusIdx].W1level
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