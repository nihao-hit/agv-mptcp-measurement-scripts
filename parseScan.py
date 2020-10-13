import Status
import calcTime

import numpy as np
import re

def parseScan(scanFile):
    count = 0
    with open(scanFile, 'r') as f:
        scanList = f.read()
        scanList = scanList.split('||')
        for scan in scanList:
            try:
                #####################################################
                # 从文件中提取数据，赋值变量
                status = {}
                status['dev'] = re.findall('(?<=dev\": \").*?(?=\")', scan)[0]
                status['stime'] = int(float((re.findall('(?<=stime\": ).*?(?=,)', scan)[0])))
                status['etime'] = int(float((re.findall('(?<=etime\": ).*?(?=,)', scan)[0])))
                status['apMac'] = re.findall('(?<=\n)[A-Fa-f0-9]{2}:[A-Fa-f0-9]{2}:[A-Fa-f0-9]{2}:[A-Fa-f0-9]{2}:[A-Fa-f0-9]{2}:[A-Fa-f0-9]{2}', scan)
                status['channel'] = list(map(float, re.findall('(?<=\" )\d\.\d+(?= \d)', scan)))
                # "Quicktron-AGV" 5.6 120 100/100 97/100
                # "cainiao-AGV" 5.3 60 43/70 -67
                if status['dev'] == 'wlan0':
                    status['level'] = list(map(int, re.findall(' -\d+(?=,)', scan)))
                else:
                    # 根据公式quality = (level + 110) / 70 * 100还原level为接收信号强度
                    status['level'] = list(map(lambda x: int(int(x) * 70 / 100 - 110), re.findall(' \d+(?=/\d+,)', scan)))
                #####################################################
                #####################################################
                # 计算connStartTime, startTime与endTime
                if calcTime.connStartTime == -1:
                    calcTime.connStartTime = status['stime']
                if calcTime.startTimes[calcTime.SCAN] == -1:
                    calcTime.startTimes[calcTime.SCAN] = status['stime']
                calcTime.endTimes[calcTime.SCAN] = status['etime']
                #####################################################
                #####################################################
                startPos = status['stime'] - calcTime.connStartTime
                endPos = status['etime'] - calcTime.connStartTime
                # 避免出现负数的pos污染最后时间戳的数据，直接丢弃这部分数据
                if endPos < 0:
                    continue
                if startPos < 0:
                    startPos = 0
                # 解析数据放入ScanStatusList中
                for pos in range(startPos, endPos+1):
                    Status.scanStatusList[pos].timestamp = calcTime.connStartTime + pos
                    if status['dev'] == 'wlan0':
                        Status.scanStatusList[pos].w0ApMac = status['apMac']
                        Status.scanStatusList[pos].w0Channel = status['channel']
                        Status.scanStatusList[pos].w0Level = status['level']
                    elif status['dev'] == 'wlan1':
                        Status.scanStatusList[pos].w1ApMac = status['apMac']
                        Status.scanStatusList[pos].w1Channel = status['channel']
                        Status.scanStatusList[pos].w1Level = status['level']
                    else:
                        pass
                # 解析数据放入StatusList中
                apCount = len(status['level'])
                if apCount > 0:
                    maxIdx = status['level'].index(max(status['level']))
                    minIdx = status['level'].index(min(status['level']))
                    for pos in range(startPos, endPos + 1):
                        if status['dev'] == 'wlan0':
                            Status.sList[pos].scanW0APCount = apCount
                            Status.sList[pos].scanW0APLevelMin = status['level'][minIdx]
                            Status.sList[pos].scanW0APMacMin = status['apMac'][minIdx]
                            Status.sList[pos].scanW0APLevelMax = status['level'][maxIdx]
                            Status.sList[pos].scanW0APMacMax = status['apMac'][maxIdx]
                        elif status['dev'] == 'wlan1':
                            Status.sList[pos].scanW1APCount = apCount
                            Status.sList[pos].scanW1APLevelMin = status['level'][minIdx]
                            Status.sList[pos].scanW1APMacMin = status['apMac'][minIdx]
                            Status.sList[pos].scanW1APLevelMax = status['level'][maxIdx]
                            Status.sList[pos].scanW1APMacMax = status['apMac'][maxIdx]
                        else:
                            pass
                #####################################################
                #####################################################
                # TODO: 这里的conn数据没有写入data.csv文件，目前看来影响不大，有时间再搞吧．
                # 使用scan文件的conn数据，减轻conn文件测量空洞的问题
                # 由于所有数据直接在ConnStatusList末尾插入，没有按照时间戳排序，
                # 因此从connData.csv文件读取后需要进行这一操作
                etime = int(float((re.findall('(?<=etime\": ).*?(?=,)', scan)[0])) * 1e3)
                apMac = re.findall('(?<=Access ).*?(?= )', scan)[0]
                if re.findall('Not-Associated', scan):
                    apMac = 'Not-Associated'
                    level = 0
                    channel = 0.0
                elif len(re.findall('level', scan)) == 1:
                    level = int(re.findall('(?<=level=).*?(?= )', scan)[0])
                    channel = float(re.findall('(?<=Frequency:).*?(?= )', scan)[0])
                else:
                    # 根据公式quality = (level + 110) / 70 * 100还原level为接收信号强度
                    tmp = int(re.findall('(?<=level=).*?(?=/\d+ )', scan)[0])
                    level = int(tmp * 70 / 100 - 110)
                    channel = float(re.findall('(?<=Frequency:).*?(?= )', scan)[0])
                
                connStatus = Status.ConnStatus()

                connStatus.timestamp = etime

                if status['dev'] == 'wlan0':
                    connStatus.W0APMac = apMac
                    connStatus.W0level = level
                    connStatus.W0channel = channel
                if status['dev'] == 'wlan1' and Status.sList[endPos].W1APMac == '':
                    connStatus.W1APMac = apMac
                    connStatus.W1level = level
                    connStatus.W1channel = channel
                
                Status.ConnStatusList.append(connStatus)
                #####################################################
            except:
                    count += 1
    print("try-except错误次数：{}".format(count))
            

def fillScan(scanStatusList, startTime):
    for i in range(len(scanStatusList)):
        if scanStatusList[i].timestamp == 0:
            scanStatusList[i].timestamp = startTime + i