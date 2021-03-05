import numpy as np
import re
import gzip
import random
import os
import time
import functools
import pandas as pd

import Status
import calcTime

#src, srcPort, dst, dstPort, length, snd_nxt, snd_una, snd_cwnd, ssthresh, snd_wnd
# srtt, rcv_wnd, path_index, map_data_len, map_data_seq, map_subseq, snt_isn, rcv_isn
def parseTcpprobe(tcpprobeFile):
    count = 0
    with open(tcpprobeFile, 'r') as f:
        for line in f.readlines():
            info = line.strip().split(' ')
            try:
                #####################################################
                # 从文件中提取数据，赋值变量
                # StatusList对齐时间戳使用int(timestamp)
                # TcpprobeStatusList使用int(timestamp * 1e6)
                timestamp = float(info[0])
                srtt = int(float(info[9]) / 1000)
                #####################################################
                #####################################################
                # 计算connStartTime, startTime与endTime
                if calcTime.connStartTime == -1:
                    calcTime.connStartTime = int(timestamp)
                if calcTime.startTimes[calcTime.TCPPROBE] == -1:
                    calcTime.startTimes[calcTime.TCPPROBE] = int(timestamp)
                calcTime.endTimes[calcTime.TCPPROBE] = int(timestamp)
                #####################################################
                #####################################################
                # 解析数据写入StatusList
                pos = int(timestamp) - calcTime.connStartTime
                # 避免出现负数的pos污染最后时间戳的数据，直接丢弃这部分数据
                if pos < 0:
                    continue

                srtt = int(float(info[9]) / 1000)

                if Status.sList[pos].srtt == 0 or Status.sList[pos].srtt > srtt:
                    if 'ffff' in info[1]: 
                        Status.sList[pos].src = info[1].split('[')[1].split(']')[0].split(':')[3]
                        Status.sList[pos].srcPort = int(info[1].split(':')[4])
                        Status.sList[pos].dst = info[2].split('[')[1].split(']')[0].split(':')[3]
                        Status.sList[pos].dstPort = int(info[2].split(':')[4])
                    else:
                        Status.sList[pos].src = info[1].split(':')[0]
                        Status.sList[pos].srcPort = int(info[1].split(':')[1])
                        Status.sList[pos].dst = info[2].split(':')[0]
                        Status.sList[pos].dstPort = int(info[2].split(':')[1])
                    
                    Status.sList[pos].length = int(info[3])
                    Status.sList[pos].snd_nxt = int(info[4])
                    Status.sList[pos].snd_una = int(info[5])
                    Status.sList[pos].snd_cwnd = int(info[6])
                    Status.sList[pos].ssthresh = int(info[7])
                    Status.sList[pos].snd_wnd = int(info[8])
                    Status.sList[pos].srtt = srtt
                    Status.sList[pos].rcv_wnd = int(info[10])
                    Status.sList[pos].path_index = int(info[11])
                    Status.sList[pos].map_data_len = int(info[12])
                    Status.sList[pos].map_data_seq = int(info[13])
                    Status.sList[pos].map_subseq = int(info[14])
                    Status.sList[pos].snt_isn = int(info[15])
                    Status.sList[pos].rcv_isn = int(info[16])
                #####################################################
            except:
                count += 1
    print("try-except错误次数：{}".format(count))




def parseTcpprobeForTcpprobeStatusList(tcpprobeFile):
    count = 0
    with open(tcpprobeFile, 'r') as f:
        for line in f.readlines():
            info = line.strip().split(' ')
            try:
                #####################################################
                # 从文件中提取数据，赋值变量
                # StatusList对齐时间戳使用int(timestamp)
                # TcpprobeStatusList使用int(timestamp * 1e6)
                timestamp = float(info[0])
                srtt = int(float(info[9]) / 1000)
                #####################################################
                #####################################################
                # 解析数据写入TcpprobeStatusList
                tcpprobeStatus = Status.TcpprobeStatus()

                tcpprobeStatus.timestamp = int(timestamp * 1e6)

                if 'ffff' in info[1]: 
                    tcpprobeStatus.src = info[1].split('[')[1].split(']')[0].split(':')[3]
                    tcpprobeStatus.srcPort = int(info[1].split(':')[4])
                    tcpprobeStatus.dst = info[2].split('[')[1].split(']')[0].split(':')[3]
                    tcpprobeStatus.dstPort = int(info[2].split(':')[4])
                else:
                    tcpprobeStatus.src = info[1].split(':')[0]
                    tcpprobeStatus.srcPort = int(info[1].split(':')[1])
                    tcpprobeStatus.dst = info[2].split(':')[0]
                    tcpprobeStatus.dstPort = int(info[2].split(':')[1])
                
                tcpprobeStatus.length = int(info[3])
                tcpprobeStatus.snd_nxt = int(info[4])
                tcpprobeStatus.snd_una = int(info[5])
                tcpprobeStatus.snd_cwnd = int(info[6])
                tcpprobeStatus.ssthresh = int(info[7])
                tcpprobeStatus.snd_wnd = int(info[8])
                tcpprobeStatus.srtt = srtt
                tcpprobeStatus.rcv_wnd = int(info[10])
                tcpprobeStatus.path_index = int(info[11])
                tcpprobeStatus.map_data_len = int(info[12])
                tcpprobeStatus.map_data_seq = int(info[13])
                tcpprobeStatus.map_subseq = int(info[14])
                tcpprobeStatus.snt_isn = int(info[15])
                tcpprobeStatus.rcv_isn = int(info[16])

                Status.TcpprobeStatusList.append(tcpprobeStatus)
                #####################################################
            except:
                count += 1
    print("try-except错误次数：{}".format(count))
    


# 返回填补统计信息
def fillTcpprobe(sList, startTime, fillDir):
    # 按秒填充，后续处理会丢弃所有填充数据
    txTime = startTime + len(sList)
    fillTimes = []
    fillFlag = True
    for i in range(len(sList)-1, -1, -1):
        # srtt类型为int
        if sList[i].srtt == 0:
            rxTime = startTime + i
            if rxTime <= txTime:
                j = i
                while(j >= 0 and sList[j].srtt == 0):
                    j -= 1
                # txTime为缺失时段第一秒
                txTime = startTime + j + 1
            # srtt单位为毫秒
            sList[i].srtt = (rxTime - txTime + 1)*1000
            if fillFlag:
                fillTimes.append([txTime, rxTime, rxTime-txTime+1])
                fillFlag = False
        else:
            fillFlag = True

    holeList = pd.DataFrame(fillTimes, columns=['start', 'end', 'duration'])
    fileName = 'fillTcpprobeForEvent-{}-{}.csv'.format(len(holeList), holeList['duration'].sum())
    holeList.to_csv(os.path.join(fillDir,fileName))