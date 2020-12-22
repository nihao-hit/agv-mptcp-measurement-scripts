import numpy as np
import re
import gzip
import os
import time
import datetime
import pandas as pd

import Status
import calcTime

# 2020/12/22:15: 使用细分后的reportInfoLog提取应用层数据
def parseComm(reportInfoLogCsvFile):
    count = 0
    with open(reportInfoLogCsvFile, 'r') as f:
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



# 根据日志级别划分日志数据，生成info.csv, debug.csv, warn.csv；根据日志类型划分info.csv, debug.csv，生成infoLog/*, debugLog/*．
def classifyLog(commCsvFileList, appDir):
    #####################################################
    print('解析comm文件，写入statusList')
    statusList = []
    for commCsvFile in commCsvFileList:
        with gzip.open(commCsvFile, 'r') as f:
                for line in f.readlines():
                    try:
                        # 从文件中提取数据，赋值变量
                        line = str(line, encoding="utf-8")
                        statusList.append(line.split('\t'))
                    except:
                        pass
    #####################################################
    #####################################################
    print('按照日志级别划分info, debug, warn日志')
    df = pd.DataFrame(statusList)
    df.columns = ['date', 'logLevel', 'logger', 'loggerType', 'content']
    
    # 不能成功解析timestamp与logType的日志行可以直接舍弃
    # ValueError: time data 'java.util.concurrent.TimeoutException: SERVER_CONNECTION_CLOSED\n' does not match format '%Y-%m-%d %H:%M:%S.%f'
    def strToTimestamp(row):
        try:
            return int(time.mktime(datetime.datetime.strptime(row['date'], "%Y-%m-%d %H:%M:%S.%f").timetuple()))
        except:
            return np.nan
    df['timestamp'] = df.apply(strToTimestamp, axis=1)
    
    def getLogType(row):
        try:
            return row['content'].split('|')[0]
        except:
            return np.nan
    df['logType'] = df.apply(getLogType, axis=1)
    df = df.dropna().reset_index(drop=True)

    infoDf = df[df['logLevel'] == 'INFO']
    debugDf = df[df['logLevel'] == 'DEBUG']
    warnDf = df[df['logLevel'] == 'WARN']
    #####################################################
    #####################################################
    print('进一步解析info日志')
    infoDfDict = dict(list(infoDf.groupby('logType')))
    infoLogDir = os.path.join(appDir, 'infoLog')
    if not os.path.isdir(infoLogDir):
        os.makedirs(infoLogDir)
    for k, v in infoDfDict.items():
        v.to_csv(os.path.join(infoLogDir, '{}.csv'.format(k)))
    infoDf.to_csv(os.path.join(appDir, 'infoData.csv'))
    #####################################################
    #####################################################
    print('进一步解析debug日志')
    debugDfDict = dict(list(debugDf.groupby('logType')))
    debugLogDir = os.path.join(appDir, 'debugLog')
    if not os.path.isdir(debugLogDir):
        os.makedirs(debugLogDir)
    for k, v in debugDfDict.items():
        v.to_csv(os.path.join(debugLogDir, '{}.csv'.format(k)))
    debugDf.to_csv(os.path.join(appDir, 'debugData.csv'))
    #####################################################
    #####################################################
    print('进一步解析warn日志')
    # 不一定所有日志都有msgId这一项
    # warnDf['msgId'] = warnDf.apply(lambda row : int(re.findall('(?<=msgId=[)\d+(?=])', row['content'])), axis=1)
    warnDf.to_csv(os.path.join(appDir, 'warnData.csv'))
    #####################################################
    #####################################################
    print('非图表型统计数据构造')
    staticsFile = os.path.join(appDir, 'statics.csv')
    statics = dict()
    if os.path.isfile(staticsFile):
        statics = pd.read_csv(staticsFile).to_dict('list')

    # 数据总数
    statics['log数量'] = len(df)

    statics['infoLog数量'] = len(infoDf)
    # info细分总数
    for k, v in infoDfDict.items():
        statics['{}-infoLog数量'.format(k)] = len(v)

    statics['debugLog数量'] = len(debugDf)
    # debug细分总数
    for k, v in debugDfDict.items():
        statics['{}-debugLog数量'.format(k)] = len(v)
    
    statics['warn数量'] = len(warnDf)
    #####################################################
    #####################################################
    print('将非图表型统计数据写入文件')
    pd.DataFrame(statics, index=[0]).to_csv(os.path.join(appDir, 'statics.csv'))
    #####################################################



# 按path字段划分reqInfoLog，生成job.csv, record.csv, notification.csv
def classifyReqInfoLog(reqInfoLogCsvFile, tmpDir):
    #####################################################
    def getBucketId(row):
        try:
            return int(re.findall('(?<=bucketId=).*?(?=, )', row['content'])[0])
        except:
            return 0
    def getJobId(row):
        try:
            return int(re.findall('(?<=jobID=).*?(?=, )', row['content'])[0])
        except:
            return 0
    #####################################################
    #####################################################
    print('按path字段划分reqInfoLog，写入reqInfoLogDir')
    reqDf = pd.read_csv(reqInfoLogCsvFile, usecols=['timestamp', 'content'],
                                dtype={'timestamp' : int,
                                       'content' : str})
    reqDf['path'] = reqDf.apply(lambda row : re.findall(r'(?<=path=Path\(path=).*?(?=\),)', row['content'])[0], axis=1)
    reqInfoLogDir = os.path.join(os.path.split(reqInfoLogCsvFile)[0], 'reqInfoLog')
    if not os.path.isdir(reqInfoLogDir):
        os.makedirs(reqInfoLogDir)
    for label, group in reqDf.groupby('path'):
        group.to_csv(os.path.join(reqInfoLogDir, '{}.csv'.format(os.path.split(label)[1])))
    #####################################################
    #####################################################
    print('进一步解析path=/DUBackend/job/state/confirm，得到jobDf并写入文件')
    jobDf = dict(list(reqDf.groupby('path')))['/DUBackend/job/state/confirm']
    jobDf['status'] = jobDf.apply(lambda row : re.findall('(?<=feedback=JS_).*?(?=, )', row['content'])[0], axis=1)
    jobDf['jobId'] = jobDf.apply(lambda row : int(re.findall('(?<=jobid=).*?(?=, )', row['content'])[0]), axis=1)
    # bucketId可能为null
    jobDf['bucketId'] = jobDf.apply(getBucketId, axis=1)
    jobDf['jobType'] = jobDf.apply(lambda row : re.findall('(?<=jobType=).*?(?=, )', row['content'])[0], axis=1)
    jobDf['wayPointId'] = jobDf.apply(lambda row : re.findall(r'(?<=wayPointId=).*?(?=\)\])', row['content'])[0], axis=1)
    jobDf.drop(['content','path'], axis=1, inplace=True)
    jobDf.to_csv(os.path.join(tmpDir, 'job.csv'))
    #####################################################
    #####################################################
    print('进一步解析path=/DUBackend/das/duEvent/record，得到recordDf并写入文件')
    recordDf = dict(list(reqDf.groupby('path')))['/DUBackend/das/duEvent/record']
    recordDf['lastRobotState'] = recordDf.apply(lambda row : int(re.findall('(?<=lastRobotState=).*?(?=, )', row['content'])[0]), axis=1)
    recordDf['opstate'] = recordDf.apply(lambda row : int(re.findall('(?<=opstate=).*?(?=, )', row['content'])[0]), axis=1)
    recordDf['workingPattern'] = recordDf.apply(lambda row : re.findall('(?<=workingPattern=).*?(?=, )', row['content'])[0], axis=1)
    recordDf['eventID'] = recordDf.apply(lambda row : re.findall('(?<=eventID=).*?(?=, )', row['content'])[0], axis=1)
    recordDf['eventType'] = recordDf.apply(lambda row : re.findall('(?<=eventType=).*?(?=, )', row['content'])[0], axis=1)
    recordDf['waypointID'] = recordDf.apply(lambda row : int(re.findall('(?<=waypointID=).*?(?=, )', row['content'])[0]), axis=1)
    recordDf['x'] = recordDf.apply(lambda row : int(re.findall('(?<=x=).*?(?=, )', row['content'])[0]), axis=1)
    recordDf['y'] = recordDf.apply(lambda row : int(re.findall('(?<=y=).*?(?=, )', row['content'])[0]), axis=1)
    recordDf['heading'] = recordDf.apply(lambda row : int(re.findall('(?<=heading=).*?(?=, )', row['content'])[0]), axis=1)
    recordDf['speed'] = recordDf.apply(lambda row : float(re.findall('(?<=speed=).*?(?=, )', row['content'])[0]), axis=1)
    # bucketId可能为null
    recordDf['bucketID'] = recordDf.apply(getBucketId, axis=1)
    # jobId可能为null
    recordDf['jobId'] = recordDf.apply(getJobId, axis=1)
    recordDf['power'] = recordDf.apply(lambda row : float(re.findall('(?<=power=).*?(?=, )', row['content'])[0]), axis=1)
    recordDf.drop(['content','path'], axis=1, inplace=True)
    recordDf.to_csv(os.path.join(tmpDir, 'record.csv'))
    #####################################################
    #####################################################
    print('进一步解析path=/DUBackend/zkProxy/sendNotification，得到notifyDf并写入文件')
    notifyDf = dict(list(reqDf.groupby('path')))['/DUBackend/zkProxy/sendNotification']
    notifyDf['level'] = notifyDf.apply(lambda row : re.findall('(?<=level=).*?(?=, )', row['content'])[0], axis=1)
    notifyDf['biz'] = notifyDf.apply(lambda row : re.findall('(?<=biz=).*?(?=, )', row['content'])[0], axis=1)
    notifyDf['type'] = notifyDf.apply(lambda row : re.findall('(?<=type=).*?(?=, )', row['content'])[1], axis=1)
    notifyDf['code'] = notifyDf.apply(lambda row : re.findall('(?<=code=).*?(?=, )', row['content'])[0], axis=1)
    # notifyDf['extra'] = notifyDf.apply(lambda row : re.findall(r'(?<=extra=).*?(?=\)\])', row['content'])[0], axis=1)
    notifyDf.drop(['content','path'], axis=1, inplace=True)
    notifyDf.to_csv(os.path.join(tmpDir, 'notification.csv'))
    #####################################################




if __name__ == '__main__':
    ###############################################################################
    print('**********细粒度解析comm文件阶段**********')
    #####################################################
    for i in range(1, 42):
        fileName = '30.113.151.' + str(i)
        print(fileName)
        tmpPath = os.path.join(r'/home/cx/Desktop/sdb-dir/tmp', fileName)
        dataPath = os.path.join(tmpPath, 'data')
        if os.path.isdir(tmpPath):
            appDir = os.path.join(tmpPath, 'analysisApp')
            if not os.path.isdir(appDir):
                os.makedirs(appDir)

            print('根据日志级别划分日志数据，并进一步探究细分后日志．')
            commCsvFileList = sorted([os.path.join(dataPath, i) for i in os.listdir(dataPath)
                                                                if 'communication' in i])
            classifyLog(commCsvFileList, appDir)

            print('按path字段划分reqInfoLog，并进一步探究细分后日志')
            reqInfoLogCsvFile = os.path.join(appDir, 'infoLog/NEW_REQUEST.csv')
            classifyReqInfoLog(reqInfoLogCsvFile, tmpPath)
    #####################################################
    print('**********细粒度解析comm文件阶段结束**********')
    ###############################################################################