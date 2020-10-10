import subprocess
import numpy as np
import re
import math
import os
import time
import datetime
import pandas as pd
import functools

def parseTcpdump(dataPath):
    #####################################################
    print('构造解析tcpdump数据的目录结构')
    mptcpDataDir = os.path.join(os.path.split(dataPath)[0], 'mptcpData')
    pcapDir = os.path.join(mptcpDataDir, 'pcap')
    staticsFile = os.path.join(mptcpDataDir, 'statics.txt')
    xplDir = os.path.join(mptcpDataDir, 'xpl')
    if not os.path.isdir(pcapDir):
        os.makedirs(pcapDir)
    if not os.path.isdir(xplDir):
        os.makedirs(xplDir)
    #####################################################
    #####################################################
    print('使用mptcpsplit工具从原始pcap文件中提取单条mptcp连接的pcap文件')
    rawPcapFileNameList = list(filter(lambda fileName : True if 'pcap' in fileName else False, os.listdir(dataPath))) 
    rawPpcapFileList = sorted(list(map(lambda fileName : os.path.join(dataPath, fileName), rawPcapFileNameList)))
    globaln = 1
    for pcapFile in rawPpcapFileList:
        output = subprocess.getoutput('mptcpsplit -l {}'.format(pcapFile))
        localn = len(output.split('\n')) - 1
        for i in range(localn):
            subprocess.call('mptcpsplit -n {} -o {} {}' \
                .format(i, os.path.join(pcapDir, 'mptcp{}.pcap'.format(globaln)), pcapFile), shell=True)
            globaln += 1
    #####################################################
    #####################################################
    print('使用mptcpcrunch工具统计单条mptcp连接的信息')
    print('使用mptcpplot工具生成time sequence graph文件')
    pcapFileList = sorted(list(map(lambda fileName : os.path.join(pcapDir, fileName), os.listdir(pcapDir))))
    for pcapFile in pcapFileList:
        mptcpNum = re.findall(r'\d+', os.path.split(pcapFile)[1])[0]
        subprocess.call('echo mptcpNum: {} >> {}'.format(mptcpNum, staticsFile), shell=True)
        subprocess.call('mptcpcrunch -c {} >> {}'.format(pcapFile, staticsFile), shell=True)
        subprocess.call('mptcpcrunch -s {} >> {}'.format(pcapFile, staticsFile), shell=True)
        subprocess.call('echo "||" >> {}'.format(staticsFile), shell=True)

        subXplDir = os.path.join(xplDir, os.path.splitext(os.path.split(pcapFile)[1])[0])
        if not os.path.isdir(subXplDir):
            os.makedirs(subXplDir)
        p = subprocess.Popen('cd {};mptcpplot -a -j {}'.format(subXplDir, pcapFile), shell=True)
        p.wait()
    #####################################################


def parseStatics(staticsFile, tmpDir):
    count = 0
    mptcpStatusList = []
    with open(staticsFile, 'r') as f:
        mptcpList = f.read()
        mptcpList = list(filter(lambda content: len(content) != 0, mptcpList.split('||')))
        for mptcp in mptcpList:
            try:
                mptcpNum = int(re.findall(r'(?<=mptcpNum: )\d+(?=\n)', mptcp)[0])
                first_timestamp = int(float(re.findall(r'(?<=first_timestamp: )\d+\.\d+(?= )', mptcp)[0]) * 1e3)
                last_timestamp = int(float(re.findall(r'(?<=last_timestamp: )\d+\.\d+(?= )', mptcp)[0]) * 1e3)
                mptcpStatusList.append([mptcpNum, first_timestamp, last_timestamp])
            except:
                count += 1
    mptcpDf = pd.DataFrame(mptcpStatusList, columns=['mptcpNum', 'first_timestamp', 'last_timestamp'])
    mptcpDf['duration'] = mptcpDf['last_timestamp'] - mptcpDf['first_timestamp']
    mptcpDf['startDate'] = mptcpDf.apply(lambda row : datetime.datetime.fromtimestamp(row['first_timestamp'] / 1000), axis=1)
    mptcpDf['endDate'] = mptcpDf.apply(lambda row : datetime.datetime.fromtimestamp(row['last_timestamp'] / 1000), axis=1)
    mptcpDf.to_csv(os.path.join(tmpDir, 'mptcpData.csv'))
    print("try-except错误次数：{}".format(count))