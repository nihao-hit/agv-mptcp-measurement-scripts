import subprocess
import numpy as np
import re
import math
import os
import time
import datetime
import pandas as pd
import functools
import csv
import scapy.all as scapy

import Status

class MptcpStatus:
    # mptcp
    mptcpNum = 0                            #1
    connStats = ''                          #2
    numSub = 0                              #3
    # mptcp : agv -> server             
    originMptcpFirstTs = 0                  #4
    originMptcpLastTs = 0                   #5

    originMptcpFirstDataTs = 0              #6
    originMptcpLastDataTs = 0               #7
    
    originMptcpFirstFastcloseTs = 0         #8
    originMptcpLastFastcloseTs = 0          #9
    
    originMptcpFirstDatafinTs = 0           #10
    originMptcpLastDatafinTs = 0            #11
    
    originMptcpPacket = 0                   #12
    originMptcpDataPacket = 0               #13
    originMptcpPayloadByte = 0              #14
    # mptcp : server -> agv
    remoteMptcpFirstTs = 0                  #15
    remoteMptcpLastTs = 0                   #16

    remoteMptcpFirstDataTs = 0              #17
    remoteMptcpLastDataTs = 0               #18
    
    remoteMptcpFirstFastcloseTs = 0         #19
    remoteMptcpLastFastcloseTs = 0          #20
    
    remoteMptcpFirstDatafinTs = 0           #21
    remoteMptcpLastDatafinTs = 0            #22
    
    remoteMptcpPacket = 0                   #23 
    remoteMptcpDataPacket = 0               #24
    remoteMptcpPayloadByte = 0              #25

    def __init__(self):
        # mptcp
        self.mptcpNum = 0                            #1
        self.connStats = ''                          #2
        self.numSub = 0                              #3
        # mptcp : agv -> server             
        self.originMptcpFirstTs = 0                  #4
        self.originMptcpLastTs = 0                   #5

        self.originMptcpFirstDataTs = 0              #6
        self.originMptcpLastDataTs = 0               #7
        
        self.originMptcpFirstFastcloseTs = 0         #8
        self.originMptcpLastFastcloseTs = 0          #9
        
        self.originMptcpFirstDatafinTs = 0           #10
        self.originMptcpLastDatafinTs = 0            #11
        
        self.originMptcpPacket = 0                   #12
        self.originMptcpDataPacket = 0               #13
        self.originMptcpPayloadByte = 0              #14
        # mptcp : server -> agv
        self.remoteMptcpFirstTs = 0                  #15
        self.remoteMptcpLastTs = 0                   #16

        self.remoteMptcpFirstDataTs = 0              #17
        self.remoteMptcpLastDataTs = 0               #18
        
        self.remoteMptcpFirstFastcloseTs = 0         #19
        self.remoteMptcpLastFastcloseTs = 0          #20
        
        self.remoteMptcpFirstDatafinTs = 0           #21
        self.remoteMptcpLastDatafinTs = 0            #22
        
        self.remoteMptcpPacket = 0                   #23
        self.remoteMptcpDataPacket = 0               #24
        self.remoteMptcpPayloadByte = 0              #25
    
    def __setitem__(self, k, v):
        self.k = v

    def __getitem__(self, k):
        return getattr(self, k)

    def __str__(self):
        return str(self.__dict__)

    def keys(self):
        return [attr for attr in self.__dict__ if not callable(getattr(self, attr)) and not attr.startswith("__")]




class SubflowStatus:
    # mptcp
    mptcpNum = 0                            #1
    # subflow
    subStats = ''                           #2
    # subflow : agv -> server             
    originSubFirstTs = 0                    #3
    originSubLastTs = 0                     #4

    originSubFirstDataTs = 0                #5
    originSubLastDataTs = 0                 #6
    
    originSubFirstFastcloseTs = 0           #7
    originSubLastFastcloseTs = 0            #8
    
    originSubFirstDatafinTs = 0             #9
    originSubLastDatafinTs = 0              #10

    originSubFinrstTs = 0                   #11
    
    originSubPacket = 0                     #12
    originSubDataPacket = 0                 #13
    originSubPayloadByte = 0                #14
    # subflow : server -> agv
    remoteSubFirstTs = 0                    #15
    remoteSubLastTs = 0                     #16

    remoteSubFirstDataTs = 0                #17
    remoteSubLastDataTs = 0                 #18
    
    remoteSubFirstFastcloseTs = 0           #19
    remoteSubLastFastcloseTs = 0            #20
    
    remoteSubFirstDatafinTs = 0             #21
    remoteSubLastDatafinTs = 0              #22

    remoteSubFinrstTs = 0                   #23
    
    remoteSubPacket = 0                     #24 
    remoteSubDataPacket = 0                 #25
    remoteSubPayloadByte = 0                #26

    def __init__(self):
        # mptcp
        self.mptcpNum = 0                            #1
        # subflow
        self.subStats = ''                           #2
        # subflow : agv -> server             
        self.originSubFirstTs = 0                    #3
        self.originSubLastTs = 0                     #4

        self.originSubFirstDataTs = 0                #5
        self.originSubLastDataTs = 0                 #6
        
        self.originSubFirstFastcloseTs = 0           #7
        self.originSubLastFastcloseTs = 0            #8
        
        self.originSubFirstDatafinTs = 0             #9
        self.originSubLastDatafinTs = 0              #10

        self.originSubFinrstTs = 0                   #11
        
        self.originSubPacket = 0                     #12
        self.originSubDataPacket = 0                 #13
        self.originSubPayloadByte = 0                #14
        # subflow : server -> agv
        self.remoteSubFirstTs = 0                    #15
        self.remoteSubLastTs = 0                     #16

        self.remoteSubFirstDataTs = 0                #17
        self.remoteSubLastDataTs = 0                 #18
        
        self.remoteSubFirstFastcloseTs = 0           #19
        self.remoteSubLastFastcloseTs = 0            #20
        
        self.remoteSubFirstDatafinTs = 0             #21
        self.remoteSubLastDatafinTs = 0              #22

        self.remoteSubFinrstTs = 0                   #23
        
        self.remoteSubPacket = 0                     #24 
        self.remoteSubDataPacket = 0                 #25
        self.remoteSubPayloadByte = 0                #26
    
    def __setitem__(self, k, v):
        self.k = v

    def __getitem__(self, k):
        return getattr(self, k)

    def __str__(self):
        return str(self.__dict__)

    def keys(self):
        return [attr for attr in self.__dict__ if not callable(getattr(self, attr)) and not attr.startswith("__")]




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
    pcapFileNameList = sorted(os.listdir(pcapDir), key=lambda fileName : int(re.findall(r'\d+', fileName)[0]))
    pcapFileList = list(map(lambda fileName : os.path.join(pcapDir, fileName), pcapFileNameList))
    # 为了解决多次调用parseTcpdump对statics.txt文件的追加内容bug，在这里重置文件
    subprocess.call('echo > {}'.format(staticsFile), shell=True)
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
    ###############################################################################
    print('**********第一阶段：解析statics.txt文件，写入mptcpStatusList**********')
    count = 0
    mptcpStatusList = []
    subflowStatusList = []
    with open(staticsFile, 'r') as f:
        mptcpList = f.read()
        mptcpList = list(filter(lambda content: len(content) != 0, mptcpList.split('||')))
        for mptcp in mptcpList:
            try:
                #####################################################
                # 提取每条mptcp连接的元数据写入变量
                subStats = re.findall(r'(?<=\n)30\.113\.\d+\.\d+:\d+:30\.113\.\d+\.\d+:\d+(?= )', mptcp)
                firstTs = list(map(lambda x : 0 if x == '-' else int(float(x) * 1e3), 
                                   re.findall(r'(?<=first_timestamp: ).*?(?= )', mptcp)
                                  )
                              )
                lastTs =  list(map(lambda x : 0 if x == '-' else int(float(x) * 1e3), 
                                   re.findall(r'(?<=last_timestamp: ).*?(?= )', mptcp)
                                  )
                              )
                firstDataTs = list(map(lambda x : 0 if x == '-' else int(float(x) * 1e3), 
                                       re.findall(r'(?<=first_data_timestamp: ).*?(?= )', mptcp)
                                      )
                                  )
                lastDataTs =  list(map(lambda x : 0 if x == '-' else int(float(x) * 1e3), 
                                       re.findall(r'(?<=last_data_timestamp: ).*?(?= )', mptcp)
                                      )
                                  )
                firstFastcloseTs = list(map(lambda x : 0 if x == '-' else int(float(x) * 1e3), 
                                            re.findall(r'(?<=first_fastclose_timestamp: ).*?(?= )', mptcp)
                                           )
                                       )
                lastFastcloseTs =  list(map(lambda x : 0 if x == '-' else int(float(x) * 1e3), 
                                            re.findall(r'(?<=last_fastclose_timestamp: ).*?(?= )', mptcp)
                                           )
                                       )
                firstDatafinTs =   list(map(lambda x : 0 if x == '-' else int(float(x) * 1e3), 
                                            re.findall(r'(?<=first_datafin_timestamp: ).*?(?= )', mptcp)
                                           )
                                       )
                lastDatafinTs =    list(map(lambda x : 0 if x == '-' else int(float(x) * 1e3), 
                                            re.findall(r'(?<=last_datafin_timestamp: ).*?(?= )', mptcp)
                                           )
                                       )
                finrstTs =    list(map(lambda x : 0 if x == '-' else int(float(x) * 1e3), 
                                       re.findall(r'(?<=first_fin_rst_timestamp: ).*?(?= )', mptcp)
                                      )
                                  )
                packet = list(map(lambda x : 0 if x == '-' else int(x), 
                                  re.findall(r'(?<= packet_count: ).*?(?= )', mptcp)
                                 )
                             )
                dataPacket = list(map(lambda x : 0 if x == '-' else int(x), 
                                      re.findall(r'(?<=data_packet_count: ).*?(?= )', mptcp)
                                     )
                                 )
                payloadByte = list(map(lambda x : 0 if x == '-' else int(x), 
                                       re.findall(r'(?<=payload_byte_count: ).*?(?=\n)', mptcp)
                                      )
                                  )
                #####################################################
                #####################################################
                # 创建并赋值mptcpStatus，接着写入mptcpStatusList
                # 创建mptcpStatus
                mptcpStatus = MptcpStatus()
                # mptcp
                mptcpStatus.mptcpNum = int(re.findall(r'(?<=mptcpNum: )\d+(?=\n)', mptcp)[0])
                mptcpStatus.connStats = re.findall(r'(?<=Connection stats: ).*?(?= )', mptcp)[0]
                mptcpStatus.numSub = int(re.findall(r'(?<=num_subflows: )\d+(?= )', mptcp)[0])
                # mptcp : agv -> server
                mptcpStatus.originMptcpFirstTs = firstTs[0]
                mptcpStatus.originMptcpLastTs = lastTs[0]

                mptcpStatus.originMptcpFirstDataTs = firstDataTs[0]
                mptcpStatus.originMptcpLastDataTs = lastDataTs[0]
                
                mptcpStatus.originMptcpFirstFastcloseTs = firstFastcloseTs[0]
                mptcpStatus.originMptcpLastFastcloseTs = lastFastcloseTs[0]
                
                mptcpStatus.originMptcpFirstDatafinTs = firstDatafinTs[0]
                mptcpStatus.originMptcpLastDatafinTs = lastDatafinTs[0]
                
                mptcpStatus.originMptcpPacket = packet[0]
                mptcpStatus.originMptcpDataPacket = dataPacket[0]
                mptcpStatus.originMptcpPayloadByte = payloadByte[0]
                # mptcp : server -> agv
                mptcpStatus.remoteMptcpFirstTs = firstTs[1]
                mptcpStatus.remoteMptcpLastTs = lastTs[1]

                mptcpStatus.remoteMptcpFirstDataTs = firstDataTs[1]
                mptcpStatus.remoteMptcpLastDataTs = lastDataTs[1]
                
                mptcpStatus.remoteMptcpFirstFastcloseTs = firstFastcloseTs[1]
                mptcpStatus.remoteMptcpLastFastcloseTs = lastFastcloseTs[1]
                
                mptcpStatus.remoteMptcpFirstDatafinTs = firstDatafinTs[1]
                mptcpStatus.remoteMptcpLastDatafinTs = lastDatafinTs[1]
                
                mptcpStatus.remoteMptcpPacket = packet[1]
                mptcpStatus.remoteMptcpDataPacket = dataPacket[1]
                mptcpStatus.remoteMptcpPayloadByte = payloadByte[1]
                # 写入mptcpStatusList
                mptcpStatusList.append(mptcpStatus)
                #####################################################
                #####################################################
                # 创建并赋值subStatus，接着写入subflowStatusList
                for i in range(mptcpStatus.numSub):
                    # 创建subStatus
                    subStatus = SubflowStatus()
                    # subflow
                    subStatus.mptcpNum = mptcpStatus.mptcpNum
                    subStatus.subStats = subStats[i*2]
                    # subflow : agv -> server             
                    subStatus.originSubFirstTs = firstTs[i*2 + 2]
                    subStatus.originSubLastTs = lastTs[i*2 + 2]

                    subStatus.originSubFirstDataTs = firstDataTs[i*2 + 2]
                    subStatus.originSubLastDataTs = lastDataTs[i*2 + 2]
                    
                    subStatus.originSubFirstFastcloseTs = firstFastcloseTs[i*2 + 2]
                    subStatus.originSubLastFastcloseTs = lastFastcloseTs[i*2 + 2]
                    
                    subStatus.originSubFirstDatafinTs = firstDatafinTs[i*2 + 2]
                    subStatus.originSubLastDatafinTs = lastDatafinTs[i*2 + 2]

                    subStatus.originSubFinrstTs = finrstTs[i*2]
                    
                    subStatus.originSubPacket = packet[i*2 + 2]
                    subStatus.originSubDataPacket = dataPacket[i*2 + 2]
                    subStatus.originSubPayloadByte = payloadByte[i*2 + 2]
                    # subflow : server -> agv
                    subStatus.remoteSubFirstTs = firstTs[i*2 + 2 + 1]
                    subStatus.remoteSubLastTs = lastTs[i*2 + 2 + 1]

                    subStatus.remoteSubFirstDataTs = firstDataTs[i*2 + 2 + 1]
                    subStatus.remoteSubLastDataTs = lastDataTs[i*2 + 2 + 1]
                    
                    subStatus.remoteSubFirstFastcloseTs = firstFastcloseTs[i*2 + 2 + 1]
                    subStatus.remoteSubLastFastcloseTs = lastFastcloseTs[i*2 + 2 + 1]
                    
                    subStatus.remoteSubFirstDatafinTs = firstDatafinTs[i*2 + 2 + 1]
                    subStatus.remoteSubLastDatafinTs = lastDatafinTs[i*2 + 2 + 1]
                    
                    subStatus.remoteSubFinrstTs = finrstTs[i*2 + 1]

                    subStatus.remoteSubPacket = packet[i*2 + 2 + 1]
                    subStatus.remoteSubDataPacket = dataPacket[i*2 + 2 + 1]
                    subStatus.remoteSubPayloadByte = payloadByte[i*2 + 2 + 1]
                    # 写入subflowStatusList
                    subflowStatusList.append(subStatus)
                #####################################################
            except:
                count += 1
                print(mptcp)
    print("try-except错误次数：{}".format(count))
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将mptcpStatusList写入mptcpData.csv文件**********')
    mptcpHeaders = ['mptcpNum', 'connStats', 'numSub', 

                    'originMptcpFirstTs', 'originMptcpLastTs', 
                    'originMptcpFirstDataTs', 'originMptcpLastDataTs', 
                    'originMptcpFirstFastcloseTs', 'originMptcpLastFastcloseTs', 
                    'originMptcpFirstDatafinTs', 'originMptcpLastDatafinTs', 
                    'originMptcpPacket', 'originMptcpDataPacket', 'originMptcpPayloadByte', 
                    
                    'remoteMptcpFirstTs', 'remoteMptcpLastTs', 
                    'remoteMptcpFirstDataTs', 'remoteMptcpLastDataTs', 
                    'remoteMptcpFirstFastcloseTs', 'remoteMptcpLastFastcloseTs', 
                    'remoteMptcpFirstDatafinTs', 'remoteMptcpLastDatafinTs', 
                    'remoteMptcpPacket', 'remoteMptcpDataPacket', 'remoteMptcpPayloadByte']
    with open(os.path.join(tmpDir, 'mptcpData.csv'), 'w', newline='') as f:
        f_csv = csv.DictWriter(f, mptcpHeaders)
        f_csv.writeheader()
        for s in mptcpStatusList:
            f_csv.writerow(dict(s))
    print('**********第二阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第三阶段：将subflowStatusList写入subflowData.csv文件**********')
    subflowHeaders= ['mptcpNum', 'subStats',

                    'originSubFirstTs', 'originSubLastTs', 
                    'originSubFirstDataTs', 'originSubLastDataTs', 
                    'originSubFirstFastcloseTs', 'originSubLastFastcloseTs', 
                    'originSubFirstDatafinTs', 'originSubLastDatafinTs', 
                    'originSubFinrstTs',
                    'originSubPacket', 'originSubDataPacket', 'originSubPayloadByte', 
                    
                    'remoteSubFirstTs', 'remoteSubLastTs', 
                    'remoteSubFirstDataTs', 'remoteSubLastDataTs', 
                    'remoteSubFirstFastcloseTs', 'remoteSubLastFastcloseTs', 
                    'remoteSubFirstDatafinTs', 'remoteSubLastDatafinTs', 
                    'remoteSubFinrstTs',
                    'remoteSubPacket', 'remoteSubDataPacket', 'remoteSubPayloadByte']
    with open(os.path.join(tmpDir, 'subflowData.csv'), 'w', newline='') as f:
        f_csv = csv.DictWriter(f, subflowHeaders)
        f_csv.writeheader()
        for s in subflowStatusList:
            f_csv.writerow(dict(s))
    print('**********第三阶段结束**********')
    ###############################################################################




def parseTcpdumpForTcp(tcpdumpFile):
    count = 0
    for p in scapy.rdpcap(tcpdumpFile):
        try:
            tcpdumpStatus = Status.TcpdumpStatus()
            
            tcpdumpStatus.timestamp = int(p.time * 1e3)

            tcpdumpStatus.src = p.payload.src
            tcpdumpStatus.srcPort = p.payload.payload.sport
            tcpdumpStatus.dst = p.payload.dst
            tcpdumpStatus.dstPort = p.payload.payload.dport
            tcpdumpStatus.ipLen = p.payload.len
            tcpdumpStatus.seq = p.payload.payload.seq
            tcpdumpStatus.ack = p.payload.payload.ack
            tcpdumpStatus.tcpFlags = p.payload.payload.flags
            tcpdumpStatus.options = p.payload.payload.options

            Status.TcpdumpStatusList.append(tcpdumpStatus)
        except:
            count += 1
    print("try-except错误次数：{}".format(count))




if __name__ == '__main__':
    ###############################################################################
    print('**********Tcpdump文件解析**********')
    #####################################################
    for i in range(1, 42):
        fileName = '30.113.151.' + str(i)
        print(fileName)
        csvPath = os.path.join(r'/home/cx/Desktop/sdb-dir/tmp', fileName)
        if os.path.isdir(csvPath):
            print('解析Tcpdump文件，生成statics.txt')
            dataPath = os.path.join(csvPath, 'data')
            parseTcpdump(dataPath)
            
            print('解析statics.txt，生成mptcpData.csv与subflowData.csv')
            staticsFile = os.path.join(csvPath, 'mptcpData/statics.txt')
            parseStatics(staticsFile, csvPath)
    #####################################################
    print('**********Tcpdump文件解析阶段结束**********')
    ###############################################################################