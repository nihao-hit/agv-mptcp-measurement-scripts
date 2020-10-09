import numpy as np
import re
import gzip
import os
import time
import pandas as pd

import Status
import calcTime

def parseComm(commFile):
    count = 0
    with gzip.open(commFile, 'r') as f:
        for line in f.readlines():
            try:
                #####################################################
                # 从文件中提取数据，赋值变量
                line = str(line, encoding="utf-8")
                curTimestamp = int(float(re.findall('(?<=curTimestamp=).*?(?=,)', line)[0]) / 1000)
                #####################################################
                #####################################################
                # 计算connStartTime, startTime与endTime
                if calcTime.connStartTime == -1:
                    calcTime.connStartTime = curTimestamp
                if calcTime.startTimes[calcTime.COMM] == -1:
                    calcTime.startTimes[calcTime.COMM] = curTimestamp
                calcTime.endTimes[calcTime.COMM] = curTimestamp
                #####################################################
                #####################################################
                pos = curTimestamp - calcTime.connStartTime
                # 避免出现负数的pos污染最后时间戳的数据，直接丢弃这部分数据
                if pos < 0:
                    continue
                Status.sList[pos].agvCode = re.findall('(?<=agvId=AGV-).*?(?=,)', line)[0]
                Status.sList[pos].dspStatus = re.findall('(?<=dspStatus=).*?(?=,)', line)[0]
                Status.sList[pos].destPosX = int(float(re.findall('(?<=destPosX=).*?(?=,)', line)[0]) / 1000)
                Status.sList[pos].destPosY = int(float(re.findall('(?<=destPosY=).*?(?=,)', line)[0]) / 1000)
                Status.sList[pos].curPosX = int(float(re.findall('(?<=curPosX=).*?(?=,)', line)[0]) / 1000)
                Status.sList[pos].curPosY = int(float(re.findall('(?<=curPosY=).*?(?=,)', line)[0]) / 1000)
                Status.sList[pos].curTimestamp = curTimestamp
                Status.sList[pos].direction = float(re.findall('(?<=direction=).*?(?=,)', line)[0])
                Status.sList[pos].speed = float(re.findall('(?<=speed=).*?(?=,)', line)[0])
                Status.sList[pos].withBucket = int(re.findall('(?<=withBucket=).*?(?=,)', line)[0])
                Status.sList[pos].jobSn = int(re.findall('(?<=jobSn=).*?(?=,)', line)[0])
                
                # 在解析comm文件时赋值
                Status.scanStatusList[pos].curPosX = int(float(re.findall('(?<=curPosX=).*?(?=,)', line)[0]) / 1000)
                Status.scanStatusList[pos].curPosY = int(float(re.findall('(?<=curPosY=).*?(?=,)', line)[0]) / 1000)
                
                # direction = float(re.findall('(?<=direction=).*?(?=,)', line)[0])
                # if direction < 0.8:
                #     Status.sList[pos].direction = 'up'
                #     Status.sList[pos].aggregation = (Status.sList[pos].curPosX << 10) + (Status.sList[pos].curPosY << 2)
                # elif direction < 2.3:
                #     Status.sList[pos].direction = 'left'
                #     Status.sList[pos].aggregation = (Status.sList[pos].curPosX << 10) + (Status.sList[pos].curPosY << 2) + 1
                # elif direction < 3.9:
                #     Status.sList[pos].direction = 'down'
                #     Status.sList[pos].aggregation = (Status.sList[pos].curPosX << 10) + (Status.sList[pos].curPosY << 2) + 2
                # elif direction < 5.4:
                #     Status.sList[pos].direction = 'right'
                #     Status.sList[pos].aggregation = (Status.sList[pos].curPosX << 10) + (Status.sList[pos].curPosY << 2) + 3
                # else:
                #     Status.sList[pos].direction = 'up'
                #     Status.sList[pos].aggregation = (Status.sList[pos].curPosX << 10) + (Status.sList[pos].curPosY << 2)
                #####################################################
            except:
                    count += 1
    print("try-except错误次数：{}".format(count))




def parseCommForCommStatusList(commFile):
    count = 0
    with gzip.open(commFile, 'r') as f:
        for line in f.readlines():
            try:
                #####################################################
                # 从文件中提取数据，赋值变量
                line = str(line, encoding="utf-8")
                #####################################################
                #####################################################
                commStatus = Status.CommStatus()

                commStatus.agvCode = re.findall('(?<=agvId=AGV-).*?(?=,)', line)[0]
                commStatus.dspStatus = re.findall('(?<=dspStatus=).*?(?=,)', line)[0]
                commStatus.destPosX = int(float(re.findall('(?<=destPosX=).*?(?=,)', line)[0]) / 1000)
                commStatus.destPosY = int(float(re.findall('(?<=destPosY=).*?(?=,)', line)[0]) / 1000)
                commStatus.curPosX = int(float(re.findall('(?<=curPosX=).*?(?=,)', line)[0]) / 1000)
                commStatus.curPosY = int(float(re.findall('(?<=curPosY=).*?(?=,)', line)[0]) / 1000)
                commStatus.curTimestamp = int(re.findall('(?<=curTimestamp=).*?(?=,)', line)[0])
                commStatus.direction = float(re.findall('(?<=direction=).*?(?=,)', line)[0])
                commStatus.speed = float(re.findall('(?<=speed=).*?(?=,)', line)[0])
                commStatus.withBucket = int(re.findall('(?<=withBucket=).*?(?=,)', line)[0])
                commStatus.jobSn = int(re.findall('(?<=jobSn=).*?(?=,)', line)[0])

                Status.CommStatusList.append(commStatus)
                #####################################################
            except:
                    count += 1
    print("try-except错误次数：{}".format(count))




def fillComm(sList, startTime, fillDir):
    # 暂时只填补时间戳
    txTime = startTime + len(sList)
    fillTimes = []
    fillFlag = True
    for i in range(len(sList)):
        if sList[i].curTimestamp == 0:
            sList[i].curTimestamp = startTime + i
            if fillFlag == True:
                fillFlag = False

                txTime = startTime + i
        else:
            if fillFlag == False:
                fillFlag = True

                rxTime = startTime + i - 1
                fillTimes.append([txTime, rxTime, rxTime-txTime+1])
    
    holeList = pd.DataFrame(fillTimes, columns=['start', 'end', 'duration'])
    fileName = 'fillComm-{}-{}.csv'.format(len(holeList), holeList['duration'].sum())
    holeList.to_csv(os.path.join(fillDir, fileName))