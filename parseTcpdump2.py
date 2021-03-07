#-*- coding:utf-8 -*-
#!/usr/bin/env python2
import os
# use the local version (subdirectory "scapy" in the current directory)
os.putenv("PYTHONPATH","%s:%s" % ('/home/cx/program/agv-mptcp-measurement-scripts', os.getenv("PYTHONPATH")))
import scapy.all as scapy

import pandas as pd
import csv
import re
import time

# 时间戳精度为us
class TcpdumpStatus:
    timestamp = 0

    src = ''                #48
    srcPort = 0             #49
    dst = ''                #50
    dstPort = 0             #51
    tcpDataLen = 0          #52
    seq = 0                 #53
    ack = 0                 #54
    segType = ''            #55
    dsn = 0                 #56
    dataAck = 0             #57
    subSeq = 0              #58
    mptcpDataLen = 0        #59
    tsval = 0               #60
    tsecr = 0               #61

    def __init__(self):
        self.timestamp = 0

        self.src = ''                #48
        self.srcPort = 0             #49
        self.dst = ''                #50
        self.dstPort = 0             #51
        self.tcpDataLen = 0          #52
        self.seq = 0                 #53
        self.ack = 0                 #54
        self.segType = ''            #55
        self.dsn = 0                 #56
        self.dataAck = 0             #57
        self.subSeq = 0              #58
        self.mptcpDataLen = 0        #59
        self.tsval = 0               #60
        self.tsecr = 0               #61
    
    def __setitem__(self, k, v):
        self.k = v

    def __getitem__(self, k):
        return getattr(self, k)

    def __str__(self):
        return str(self.__dict__)

    def keys(self):
        return [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]


# 对每台车提取数据都需要重置以下全局变量
#####################################################
# 时间戳精度为us，不能预分配大小
TcpdumpStatusList = []
#####################################################


# [<TCPOption_NOP  kind=NOP |>, 
# <TCPOption_NOP  kind=NOP |>, 
# <TCPOption_Timestamp  kind=Timestamp length=10 timestamp_value=2084115984 timestamp_echo=1191083467 |>, 
# <TCPOption_MP  kind=MpTCP mptcp=<MPTCP_DSS_Map64_AckMapCsum  length=20 subtype=DSS reserved=0L flags=AM data_ack=4198133845 dsn=1429758358 subflow_seqnum=3868048 datalevel_len=418 checksum=0x1d79 |> |>]
def parseTcpdumpForTcp(tcpdumpFile):
    count = 0
    tcpFlags = {2: 'SYN', 1: 'FIN', 4: 'RST'}
    try:
        ps = scapy.rdpcap(tcpdumpFile)
    # 2021/3/6: raise Scapy_Exception("Not a pcap capture file (bad magic)")
    except:
        print('{}: raise Scapy_Exception("Not a pcap capture file (bad magic)")'.format(tcpdumpFile))
    else:
        for p in ps:
            try:
                tcpdumpStatus = TcpdumpStatus()
                
                tcpdumpStatus.timestamp = int(p.time * 1e6)
                tcpdumpStatus.src = p.payload.src
                tcpdumpStatus.srcPort = p.payload.payload.sport
                tcpdumpStatus.dst = p.payload.dst
                tcpdumpStatus.dstPort = p.payload.payload.dport
                tcpdumpStatus.tcpDataLen = p.payload.len - (p.payload.ihl + p.payload.payload.dataofs) * 4
                tcpdumpStatus.seq = p.payload.payload.seq
                tcpdumpStatus.ack = p.payload.payload.ack
                for bit, flag in tcpFlags.items():
                    if p.payload.payload.flags & bit == 1:
                        tcpdumpStatus.segType = flag
                for option in str(p.payload.payload.options).split('>'):
                    try:# option可能为' |'
                        kind = re.findall('(?<=kind=).*?(?= )', option)[0]
                    except:
                        kind = None
                    if kind == 'MpTCP':
                        subtype = re.findall('(?<=subtype=).*?(?= )', option)[0]
                        if subtype in ['MP_CAPABLE', 'MP_JOIN']:
                            tcpdumpStatus.segType += '|{}'.format(subtype)
                        if subtype == 'DSS':
                            dssFlags = re.findall('(?<=flags=).*?(?= )', option)[0]
                            if 'A' in dssFlags:
                                tcpdumpStatus.dataAck = int(re.findall('(?<=data_ack=).*?(?= )', option)[0])
                            if 'M' in dssFlags:
                                tcpdumpStatus.dsn = int(re.findall('(?<=dsn=).*?(?= )', option)[0])
                                tcpdumpStatus.subSeq = int(re.findall('(?<=subflow_seqnum=).*?(?= )', option)[0])
                                tcpdumpStatus.mptcpDataLen = int(re.findall('(?<=datalevel_len=).*?(?= )', option)[0])
                    if kind == 'Timestamp':
                        tcpdumpStatus.tsval = int(re.findall('(?<=timestamp_value=).*?(?= )', option)[0])
                        tcpdumpStatus.tsecr = int(re.findall('(?<=timestamp_echo=).*?(?= )', option)[0])

                TcpdumpStatusList.append(tcpdumpStatus)
            except:
                count += 1
    print("try-except错误次数：{}".format(count))


def writeDataIntoTcpdumpStatusList(dataPath):
    dataFiles = os.listdir(dataPath)
    # 排序以保证按照时间顺序解析文件
    dataFiles.sort()
    for dataFile in dataFiles:
        dataFile = os.path.join(dataPath, dataFile)
        print(dataFile)
        if 'tcpdump' in dataFile:
            parseTcpdumpForTcp(dataFile)


def writeTcpdumpStatusIntoCsv(csvPath):
    #####################################################
    print('时间戳精度为us的TcpdumpStatusList写入tcpdumpData.csv')
    tcpdumpHeaders = [
               'timestamp', 'src','srcPort','dst','dstPort','tcpDataLen','seq','ack',
               'segType','dsn', 'dataAck', 'subSeq', 'mptcpDataLen',
               'tsval', 'tsecr'
              ]
    # python2 open() have not kwarg 'newline'
    with open(os.path.join(csvPath, 'tcpdumpData.csv'), 'w') as f:
        f_csv = csv.DictWriter(f, tcpdumpHeaders)
        f_csv.writeheader()
        for s in TcpdumpStatusList:
            f_csv.writerow(dict(s))
    #####################################################


if __name__ == '__main__':
    ###############################################################################
    print('**********第六阶段：解析文件，提取TcpdumpStatusList写入tcpdumpData.csv**********')
    #####################################################
    for i in range(1, 42):
        st = time.time()

        fileName = '30.113.151.' + str(i)
        path = os.path.join(r'/home/cx/Desktop/sdb-dir/data', fileName)
        tmpPath = os.path.join(r'/home/cx/Desktop/sdb-dir/tmp', fileName)
        dataPath = os.path.join(tmpPath, 'data')
        if os.path.isdir(path):
            if not os.path.isdir(dataPath):
                os.makedirs(dataPath)
            #####################################################
            print('重置全局变量TcpdumpStatusList')
            TcpdumpStatusList = []
            #####################################################
            #####################################################
            print('解析文件数据，写入TcpdumpStatusList')
            writeDataIntoTcpdumpStatusList(dataPath)
            #####################################################
            #####################################################
            print('将TcpdumpStatusList写入csv文件')
            csvPath = tmpPath
            writeTcpdumpStatusIntoCsv(csvPath)
            #####################################################
        et = time.time()
        print('为{}生成tcpdumpData.csv耗时{}s'.format(fileName, int(et - st)))
    #####################################################
    print('**********第六阶段结束**********')
    ###############################################################################