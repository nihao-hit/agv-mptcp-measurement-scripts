import Status
import calcTime

from parseComm import parseComm, fillComm, classifyLog, classifyReqInfoLog
from parseConn import parseConn, fillConn, parseConnForConnStatusList
from parseScan import parseScan, fillScan
from parsePing127 import parsePing127, fillPing127
from parsePing151 import parsePing151, fillPing151
from parseTcpdump import parseTcpdump, parseStatics
from parseTcpprobe import parseTcpprobe, parseTcpprobeForTcpprobeStatusList, fillTcpprobe

import shutil
import re
import os
import json
import csv
import pandas as pd
import tarfile
import gzip
import numpy as np
import time
import copy
import numpy as np

def rmExtractedFiles(path):
    shutil.rmtree(path)


def extractOneAgv(path, tmpPath):
    def extractOneTargz(file, tmpPath):
        try:
            # 解压.tar.gz文件到tmpPath，.tar.gz打包内容为['data', 'data/file1', 'data/file2']
            # 在linux下需要去除'data'项
            if '.tar.gz' in file:
                tar = tarfile.open(file, "r:gz")
                fileNames = tar.getnames()
                for fileName in fileNames:
                    if fileName == 'data':
                        pass
                    tar.extract(fileName, tmpPath)
                tar.close()
            # .gz文件不需要解压，直接复制到tmpPath
            if 'communication' in file:
                        shutil.copy(file, os.path.join(tmpPath, 'data'))
        except Exception as e:
            print('extractOneTargz: error {}'.format(e))
    
    oneAgvDataFile = os.listdir(path)
    for fileOrDir in oneAgvDataFile:
        fileOrDir = os.path.join(path, fileOrDir)
        print(fileOrDir)
        extractOneTargz(fileOrDir, tmpPath)

# 2020/12/22:18: 使用reportInfoLogCsvFile替换未分类日志文件
# 由于StatusList, ScanStatusList都需要对齐s级时间戳，因此在一起处理
# 由于需要scan文件中的conn数据进行补充，因此ConnStatusList也需要在一起处理
def writeDataIntoStatusList(reportInfoLogCsvFile, dataPath):
    parseComm(reportInfoLogCsvFile)
    
    dataFiles = os.listdir(dataPath)
    # 排序以保证按照时间顺序解析文件，startTimes与connStartTime正确
    dataFiles.sort()
    for dataFile in dataFiles:
        dataFile = os.path.join(dataPath, dataFile)
        # tmp = ['communication.log.2019-08-05-1', 'conn.1564932739', 'ping127.1564932739', 'ping151.1564932739', 'scan.1564932739']
        # for tmpStr in tmp:
        #     if tmpStr in dataFile:
        print(dataFile)
        if 'conn' in dataFile:
            parseConn(dataFile)
        if 'scan' in dataFile:
            parseScan(dataFile)
        if 'ping127' in dataFile:
            parsePing127(dataFile)
        if 'ping151' in dataFile:
            parsePing151(dataFile)
        if 'tcpprobe' in dataFile:
            parseTcpprobe(dataFile)


def writeDataIntoConnStatusList(dataPath):
    dataFiles = os.listdir(dataPath)
    # 排序以保证按照时间顺序解析文件，startTimes与connStartTime正确
    dataFiles.sort()
    for dataFile in dataFiles:
        dataFile = os.path.join(dataPath, dataFile)
        # tmp = ['communication.log.2019-08-05-1', 'conn.1564932739', 'ping127.1564932739', 'ping151.1564932739', 'scan.1564932739']
        # for tmpStr in tmp:
        #     if tmpStr in dataFile:
        print(dataFile)
        if 'conn' in dataFile:
            parseConnForConnStatusList(dataFile)


def writeDataIntoTcpprobeStatusList(dataPath):
    dataFiles = os.listdir(dataPath)
    # 排序以保证按照时间顺序解析文件，startTimes与connStartTime正确
    dataFiles.sort()
    for dataFile in dataFiles:
        dataFile = os.path.join(dataPath, dataFile)
        # tmp = ['communication.log.2019-08-05-1', 'conn.1564932739', 'ping127.1564932739', 'ping151.1564932739', 'scan.1564932739']
        # for tmpStr in tmp:
        #     if tmpStr in dataFile:
        print(dataFile)
        if 'tcpprobe' in dataFile:
            parseTcpprobeForTcpprobeStatusList(dataFile)


def writeStatusIntoCsv(csvPath):
    #####################################################
    print('s级时间戳对齐后的sList写入data.csv文件')
    # 2020/11/26:11: 为写入data.csv的headers添加scanW0APChannelMin, scanW0APChannelMax, scanW1APChannelMin, scanW1APChannelMax字段
    headers = [
               'agvCode', 'dspStatus', 'destPosX', 'destPosY', 'curPosX', 'curPosY', 'curTimestamp', 'direction', 'speed', 'withBucket', 'jobSn',
               'W0APMac', 'W0channel', 'W0level', 'W1APMac', 'W1channel', 'W1level',
               'W0pingrtt', 'W1pingrtt',
               'scanW0APCount', 'scanW0APLevelMin', 'scanW0APChannelMin', 'scanW0APMacMin', 'scanW0APLevelMax', 'scanW0APChannelMax', 'scanW0APMacMax', 
               'scanW1APCount', 'scanW1APLevelMin', 'scanW1APChannelMin', 'scanW1APMacMin', 'scanW1APLevelMax', 'scanW1APChannelMax', 'scanW1APMacMax', 
               'src','srcPort','dst','dstPort','length','snd_nxt','snd_una','snd_cwnd','ssthresh','snd_wnd','srtt','rcv_wnd','path_index','map_data_len','map_data_seq','map_subseq','snt_isn','rcv_isn'
              ]
    with open(os.path.join(csvPath, 'data.csv'), 'w', newline='') as f:
        f_csv = csv.DictWriter(f, headers)
        f_csv.writeheader()
        for s in Status.sList:
            f_csv.writerow(dict(s))
        # f_csv.writerows(Status.sList[sliceStart : sliceEnd])
    #####################################################


def writeScanStatusIntoCsv(csvPath):
    #####################################################
    print('s级时间戳对齐后的scanStatusList写入scanData.csv文件')
    # ['timestamp', 'posX', 'posY', w0ApCount', 'w1ApCount', 'w0ApMac', 'w0Channel', 'w0Level', 'w1ApMac', 'w1Channel', 'w1Level']
    with open(os.path.join(csvPath, 'scanData.csv'), 'w') as f:
        for s in Status.scanStatusList:
            w0ApCount = len(s['w0ApMac'])
            w1ApCount = len(s['w1ApMac'])
            seq = [s.timestamp, s.curPosX, s.curPosY] + \
                [w0ApCount, w1ApCount] + \
                    s['w0ApMac'] + s['w0Channel'] + s['w0Level'] + \
                        s['w1ApMac'] + s['w1Channel'] + s['w1Level']
            f.write(','.join(map(str, seq)) + '\n')
    #####################################################


def writeConnStatusIntoCsv(csvPath):
    #####################################################
    print('时间戳精度为us的ConnStatusList写入connData.csv')
    connHeaders = [
               'timestamp', 'W0APMac','W0channel','W0level','W1APMac','W1channel','W1level'
              ]
    with open(os.path.join(csvPath, 'connData.csv'), 'w', newline='') as f:
        f_csv = csv.DictWriter(f, connHeaders)
        f_csv.writeheader()
        for s in Status.ConnStatusList:
            f_csv.writerow(dict(s))
    #####################################################


def writeTcpprobeStatusIntoCsv(csvPath):
    #####################################################
    print('时间戳精度为us的TcpprobeStatusList写入tcpprobeData.csv')
    tcpprobeHeaders = [
               'timestamp', 'src','srcPort','dst','dstPort','length','snd_nxt','snd_una','snd_cwnd','ssthresh','snd_wnd','srtt','rcv_wnd','path_index','map_data_len','map_data_seq','map_subseq','snt_isn','rcv_isn'
              ]
    with open(os.path.join(csvPath, 'tcpprobeData.csv'), 'w', newline='') as f:
        f_csv = csv.DictWriter(f, tcpprobeHeaders)
        f_csv.writeheader()
        for s in Status.TcpprobeStatusList:
            f_csv.writerow(dict(s))
    #####################################################


if __name__ == '__main__':
    # ###############################################################################
    # print('**********第一阶段：解压文件**********')
    # for i in range(1, 42):
    #     fileName = '30.113.151.' + str(i)
    #     path = os.path.join(r'/home/cx/Desktop/sdb-dir/data', fileName)
    #     tmpPath = os.path.join(r'/home/cx/Desktop/sdb-dir/tmp', fileName)
    #     dataPath = os.path.join(tmpPath, 'data')
    #     if os.path.isdir(path):
    #         if not os.path.isdir(dataPath):
    #             os.makedirs(dataPath)
    #         #####################################################
    #         print('提取压缩包文件，放入tmpPath')
    #         extractOneAgv(path, tmpPath) 
    #         #####################################################
    # print('**********第一阶段结束**********')
    # ###############################################################################

    # # 由于StatusList, ScanStatusList都需要对齐s级时间戳，因此在一起处理
    # ###############################################################################
    # print('**********第二阶段：解析文件，提取StatusList, ScanStatusList写入data.csv, scanData.csv**********')
    # #####################################################
    # for i in range(1, 42):
    #     st = time.time()

    #     fileName = '30.113.151.' + str(i)
    #     path = os.path.join(r'/home/cx/Desktop/sdb-dir/data', fileName)
    #     tmpPath = os.path.join(r'/home/cx/Desktop/sdb-dir/tmp', fileName)
    #     dataPath = os.path.join(tmpPath, 'data')
    #     if os.path.isdir(path):
    #         if not os.path.isdir(dataPath):
    #             os.makedirs(dataPath)
    #         #####################################################
    #         #####################################################
    #         print('划分日志数据')
    #         appDir = os.path.join(tmpPath, 'analysisApp')
    #         if not os.path.isdir(appDir):
    #             os.makedirs(appDir)
    #         commCsvFileList = sorted([os.path.join(dataPath, i) for i in os.listdir(dataPath)
    #                                                             if 'communication' in i])
    #         classifyLog(commCsvFileList, appDir)

    #         reqInfoLogCsvFile = os.path.join(appDir, 'infoLog/NEW_REQUEST.csv')
    #         classifyReqInfoLog(reqInfoLogCsvFile, tmpPath)
    #         #####################################################
    #         #####################################################
    #         print('重置全局变量sList, scanStatusList')
    #         print('connStartTime, startTimes, endTimes')
    #         Status.sList = [Status.Status() for _ in range(86400*15)]
    #         Status.scanStatusList = [Status.ScanStatus() for _ in range(86400*15)]

    #         calcTime.connStartTime = -1
    #         calcTime.startTimes = [-1 for i in range(6)]
    #         calcTime.endTimes = [-1 for i in range(6)]
    #         #####################################################
    #         #####################################################
    #         print('解析文件数据，写入StatusList, ScanStatusList')
    #         reportInfoLogCsvFile = os.path.join(tmpPath, 'analysisApp/infoLog/NEW_REPORT.csv')
    #         writeDataIntoStatusList(reportInfoLogCsvFile, dataPath)
    #         #####################################################
    #         #####################################################
    #         print('对齐最大开始时间戳与最小结束时间戳')
    #         startTime = max(list(filter(lambda x: x != -1, calcTime.startTimes)))
    #         endTime = min(list(filter(lambda x: x != -1, calcTime.endTimes)))
    #         sliceStart = startTime - calcTime.connStartTime
    #         sliceEnd = endTime - calcTime.connStartTime + 1
    #         Status.sList = Status.sList[sliceStart : sliceEnd]
    #         Status.scanStatusList = Status.scanStatusList[sliceStart : sliceEnd]
    #         print('startTime = {}, endTime = {}'.format(startTime, endTime))
    #         #####################################################
    #         #####################################################
    #         print('填补StatusList缺失数据')
    #         fillDir = os.path.join(tmpPath, 'fillDir')
    #         if not os.path.isdir(fillDir):
    #             os.mkdir(fillDir)
    #         fillComm(Status.sList, startTime, fillDir)
    #         fillConn(Status.sList, startTime, fillDir)
    #         fillScan(Status.scanStatusList, startTime)
    #         fillPing151(Status.sList, startTime, fillDir)
    #         fillPing127(Status.sList, startTime, fillDir)
    #         fillTcpprobe(Status.sList, startTime, fillDir)
    #         #####################################################
    #         #####################################################
    #         print('将StatusList与ScanStatusList写入csv文件')
    #         csvPath = tmpPath
    #         writeStatusIntoCsv(csvPath)
    #         writeScanStatusIntoCsv(csvPath)
    #         #####################################################
    #     et = time.time()
    #     print('为{}生成data.csv, scanData.csv耗时{}s'.format(fileName, int(et - st)))
    # print('**********第二阶段结束**********')
    # ###############################################################################


    # # 2020/11/26:11: connData.csv不再需要scan测量文件数据补充，改为单独提取．
    # ###############################################################################
    # print('**********第三阶段：解析文件，提取ConnStatusList写入connData.csv**********')
    # #####################################################
    # for i in range(1, 42):
    #     st = time.time()

    #     fileName = '30.113.151.' + str(i)
    #     path = os.path.join(r'/home/cx/Desktop/sdb-dir/data', fileName)
    #     tmpPath = os.path.join(r'/home/cx/Desktop/sdb-dir/tmp', fileName)
    #     dataPath = os.path.join(tmpPath, 'data')
    #     if os.path.isdir(path):
    #         if not os.path.isdir(dataPath):
    #             os.makedirs(dataPath)
    #         #####################################################
    #         print('重置全局变量ConnStatusList')
    #         Status.ConnStatusList = []
    #         #####################################################
    #         #####################################################
    #         print('解析文件数据，写入ConnStatusList')
    #         writeDataIntoConnStatusList(dataPath)
    #         #####################################################
    #         #####################################################
    #         print('将ConnStatusList写入csv文件')
    #         csvPath = tmpPath
    #         writeConnStatusIntoCsv(csvPath)
    #         #####################################################
    #     et = time.time()
    #     print('为{}生成connData.csv耗时{}s'.format(fileName, int(et - st)))
    # print('**********第三阶段结束**********')
    # ###############################################################################


    # ###############################################################################
    # print('**********第四阶段：解析文件，提取TcpprobeStatusList写入tcpprobeData.csv**********')
    # #####################################################
    # for i in range(1, 42):
    #     st = time.time()

    #     fileName = '30.113.151.' + str(i)
    #     path = os.path.join(r'/home/cx/Desktop/sdb-dir/data', fileName)
    #     tmpPath = os.path.join(r'/home/cx/Desktop/sdb-dir/tmp', fileName)
    #     dataPath = os.path.join(tmpPath, 'data')
    #     if os.path.isdir(path):
    #         if not os.path.isdir(dataPath):
    #             os.makedirs(dataPath)
    #         #####################################################
    #         print('重置全局变量TcpprobeStatusList')
    #         Status.TcpprobeStatusList = []
    #         #####################################################
    #         #####################################################
    #         print('解析文件数据，写入TcpprobeStatusList')
    #         writeDataIntoTcpprobeStatusList(dataPath)
    #         #####################################################
    #         #####################################################
    #         print('将TcpprobeStatusList写入csv文件')
    #         csvPath = tmpPath
    #         writeTcpprobeStatusIntoCsv(csvPath)
    #         #####################################################
    #     et = time.time()
    #     print('为{}生成tcpprobeData.csv耗时{}s'.format(fileName, int(et - st)))
    # print('**********第四阶段结束**********')
    # ###############################################################################


    # ###############################################################################
    # print('**********第五阶段：解析tcpdump文件，提取MptcpStatusList, SubflowStatusList写入mptcpData.csv, subflowData.csv**********')
    # #####################################################
    # print('解析tcpdump文件')
    # for i in range(1, 42):
    #     st = time.time()

    #     fileName = '30.113.151.' + str(i)
    #     tmpPath = os.path.join(r'/home/cx/Desktop/sdb-dir/tmp', fileName)
    #     if os.path.isdir(tmpPath):
    #         dataPath = os.path.join(tmpPath, 'data')
    #         parseTcpdump(dataPath)
    #         staticsFile = os.path.join(tmpPath, 'mptcpData/statics.txt')
    #         parseStatics(staticsFile, tmpPath)
    #     et = time.time()
    #     print('为{}生成mptcpData.csv, subflowData.csv耗时{}s'.format(fileName, int(et - st)))
    # #####################################################
    # print('**********第五阶段结束**********')
    # ###############################################################################


    # ###############################################################################
    # print('**********第七阶段：删除data文件夹下的解压文件，减轻磁盘压力**********')
    # #####################################################
    # print('删除data文件夹及下属所有解压文件')
    # for i in range(1, 42):
    #     fileName = '30.113.151.' + str(i)
    #     path = os.path.join(r'/home/cx/Desktop/sdb-dir/data', fileName)
    #     tmpPath = os.path.join(r'/home/cx/Desktop/sdb-dir/tmp', fileName)
    #     dataPath = os.path.join(tmpPath, 'data')
    #     rmExtractedFiles(dataPath)
    # #####################################################
    # print('**********第七阶段结束**********')
    # ###############################################################################