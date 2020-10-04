import Status
import calcTime

from parseConn import parseConn, fillConn
from parseScan import parseScan, fillScan

from parsePing127 import parsePing127, fillPing127ForEvent
from parsePing151 import parsePing151, fillPing151ForEvent

from parseComm import parseComm, fillComm

from parseTcpprobe import parseTcpprobe, fillTcpprobeForEvent

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

# from parseTcpdump import parseTcpdump


def rmExtractedFiles(path):
    shutil.rmtree(path)


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


def extractOneAgv(path, tmpPath):
    oneAgvDataFile = os.listdir(path)
    for fileOrDir in oneAgvDataFile:
        fileOrDir = os.path.join(path, fileOrDir)
        print(fileOrDir)
        extractOneTargz(fileOrDir, tmpPath)


def writeDataIntoStatusList(dataPath):
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
        if 'communication' in dataFile:
            parseComm(dataFile)
        if 'tcpprobe' in dataFile:
            parseTcpprobe(dataFile)


def writeStatusIntoCsv(csvPath):
    headers = [
               'agvCode', 'dspStatus', 'destPosX', 'destPosY', 'curPosX', 'curPosY', 'curTimestamp', 'direction', 'aggregation', 'speed', 'withBucket', 
               'W0APMac', 'W0channel', 'W0level', 'W1APMac', 'W1channel', 'W1level',
               'W0pingrtt', 'W1pingrtt',
               'scanW0APCount', 'scanW0APLevelMin', 'scanW0APMacMin', 'scanW0APLevelMax', 'scanW0APMacMax', 
               'scanW1APCount', 'scanW1APLevelMin', 'scanW1APMacMin', 'scanW1APLevelMax', 'scanW1APMacMax', 
               'src','srcPort','dst','dstPort','length','snd_nxt','snd_una','snd_cwnd','ssthresh','snd_wnd','srtt','rcv_wnd','path_index','map_data_len','map_data_seq','map_subseq','snt_isn','rcv_isn'
              ]
    with open(os.path.join(csvPath, 'data.csv'), 'w', newline='') as f:
        f_csv = csv.DictWriter(f, headers)
        f_csv.writeheader()
        for s in Status.sList:
            f_csv.writerow(dict(s))
        # f_csv.writerows(Status.sList[sliceStart : sliceEnd])

    # scan数据单独写入csv
    # ['timestamp', 'posX', 'posY', w0ApCount', 'w1ApCount', 'w0ApMac', 'w0Channel', 'w0Level', 'w1ApMac', 'w1Channel', 'w1Level']
    with open(os.path.join(csvPath, 'scanData.csv'), 'w') as f:
        for s in Status.scanStatusList:
            w0ApCount = len(s['w0ApMac'])
            w1ApCount = len(s['w1ApMac'])
            seq = [s.timestamp, s.posX, s.posY] + \
                [w0ApCount, w1ApCount] + \
                    s['w0ApMac'] + s['w0Channel'] + s['w0Level'] + \
                        s['w1ApMac'] + s['w1Channel'] + s['w1Level']
            f.write(','.join(map(str, seq)) + '\n')
    
    # tcpprobe数据单独写入csv
    tcpprobeHeaders = [
               'timestamp', 'src','srcPort','dst','dstPort','length','snd_nxt','snd_una','snd_cwnd','ssthresh','snd_wnd','srtt','rcv_wnd','path_index','map_data_len','map_data_seq','map_subseq','snt_isn','rcv_isn'
              ]
    with open(os.path.join(csvPath, 'tcpprobeData.csv'), 'w', newline='') as f:
        f_csv = csv.DictWriter(f, tcpprobeHeaders)
        f_csv.writeheader()
        for s in Status.TcpprobeStatusList:
            f_csv.writerow(dict(s))


if __name__ == '__main__':
    for i in range(1, 42):
        fileName = '30.113.151.' + str(i)
        path = os.path.join(r'/home/cx/Desktop/sdb-dir/data', fileName)
        tmpPath = os.path.join(r'/home/cx/Desktop/sdb-dir/tmp', fileName)
        dataPath = os.path.join(tmpPath, 'data')
        if os.path.isdir(path):
            if not os.path.isdir(dataPath):
                os.makedirs(dataPath)

            # 重置全局变量sList,scanStatusList,TcpprobeStatusList,connStartTime,startTimes,endTimes
            Status.sList = [Status.Status() for _ in range(86400*15)]
            Status.scanStatusList = [Status.ScanStatus() for _ in range(86400*15)]
            Status.TcpprobeStatusList = []
            calcTime.connStartTime = -1
            calcTime.startTimes = [-1 for i in range(6)]
            calcTime.endTimes = [-1 for i in range(6)]
            
            #########################################
            print('提取压缩包文件，放入tmpPath')
            extractOneAgv(path, tmpPath) 
            ########################################
            
            
            #########################################
            print('解析文件数据，写入StatusList, ScanStatusList, TcpprobeStatusList')
            writeDataIntoStatusList(dataPath)
            ###########################################


            ##########################################
            print('对齐最大开始时间戳与最小结束时间戳')
            startTime = max(list(filter(lambda x: x != -1, calcTime.startTimes)))
            endTime = min(list(filter(lambda x: x != -1, calcTime.endTimes)))
            sliceStart = startTime - calcTime.connStartTime
            sliceEnd = endTime - calcTime.connStartTime + 1
            Status.sList = Status.sList[sliceStart : sliceEnd]
            Status.scanStatusList = Status.scanStatusList[sliceStart : sliceEnd]
            # Status.TcpprobeStatusList = Status.TcpprobeStatusList[sliceStart : sliceEnd]
            print('startTime = {}, endTime = {}'.format(startTime, endTime))
            ################################################


            #########################################
            print('填补StatusList与ScanStatusList缺失数据')
            fillDir = os.path.join(tmpPath, 'fillDir')
            if not os.path.isdir(fillDir):
                os.mkdir(fillDir)
            fillComm(Status.sList, startTime, fillDir)
            fillConn(Status.sList, startTime, fillDir)
            fillScan(Status.scanStatusList, startTime)
            fillPing151ForEvent(Status.sList, startTime, fillDir)
            fillPing127ForEvent(Status.sList, startTime, fillDir)
            fillTcpprobeForEvent(Status.sList, startTime, fillDir)
            ###########################################


            ##########################################
            print('将StatusList与ScanStatusList写入csv文件')
            csvPath = tmpPath
            writeStatusIntoCsv(csvPath)
            ############################################


            # ##########################################
            # print('删除data文件夹及下属所有解压文件')
            # rmExtractedFiles(dataPath)