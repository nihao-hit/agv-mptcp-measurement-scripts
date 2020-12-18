import subprocess
import numpy as np
import re
import math
import os
import time
import datetime
import pandas as pd
import functools

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
    # subflow
    subStats = []                           #26
    # subflow : agv -> server && server -> agv
    subFirstTs = []                         #27
    subLastTs = []                          #28

    subFirstDataTs = []                     #29
    subLastDataTs = []                      #30
    
    subFirstFastcloseTs = []                #31
    subLastFastcloseTs = []                 #32
    
    subFirstDatafinTs = []                  #33
    subLastDatafinTs = []                   #34
    
    subFinRstTs = []                        #35

    subPacket = []                          #36
    subDataPacket = []                      #37
    subPayloadByte = []                     #38

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
        # subflow
        self.subStats = []                           #26
        # subflow : agv -> server && server -> agv
        self.subFirstTs = []                         #27
        self.subLastTs = []                          #28

        self.subFirstDataTs = []                     #29
        self.subLastDataTs = []                      #30
        
        self.subFirstFastcloseTs = []                #31
        self.subLastFastcloseTs = []                 #32
        
        self.subFirstDatafinTs = []                  #33
        self.subLastDatafinTs = []                   #34
        
        self.subFinRstTs = []                        #35

        self.subPacket = []                          #36
        self.subDataPacket = []                      #37
        self.subPayloadByte = []                     #38
    
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
    pcapFileList = sorted(list(map(lambda fileName : os.path.join(pcapDir, fileName), os.listdir(pcapDir))))
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
    with open(staticsFile, 'r') as f:
        mptcpList = f.read()
        mptcpList = list(filter(lambda content: len(content) != 0, mptcpList.split('||')))
        for mptcp in mptcpList:
            try:
                mptcpStatus = MptcpStatus()
                
                # mptcp
                mptcpStatus.mptcpNum = int(re.findall(r'(?<=mptcpNum: )\d+(?=\n)', mptcp)[0])
                mptcpStatus.connStats = re.findall(r'(?<=Connection stats: ).*?(?= )', mptcp)[0]
                mptcpStatus.numSub = int(re.findall(r'(?<=num_subflows: )\d+(?= )', mptcp)[0])

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
                # subflow
                mptcpStatus.subStats = re.findall(r'(?<=\n)30\.113\.\d+\.\d+:\d+:30\.113\.\d+\.\d+:\d+(?= )', mptcp)
                # subflow : agv -> server && server -> agv
                mptcpStatus.subFirstTs = firstTs[2:]
                mptcpStatus.subLastTs = lastTs[2:]

                mptcpStatus.subFirstDataTs = firstDataTs[2:]
                mptcpStatus.subLastDataTs = lastDataTs[2:]
                
                mptcpStatus.subFirstFastcloseTs = firstFastcloseTs[2:]
                mptcpStatus.subLastFastcloseTs = lastFastcloseTs[2:]
                
                mptcpStatus.subFirstDatafinTs = firstDatafinTs[2:]
                mptcpStatus.subLastDatafinTs = lastDatafinTs[2:]
                
                mptcpStatus.subFinRstTs = finrstTs

                mptcpStatus.subPacket = packet[2:]
                mptcpStatus.subDataPacket = dataPacket[2:]
                mptcpStatus.subPayloadByte = payloadByte[2:]
                
                mptcpStatusList.append(mptcpStatus)
            except:
                count += 1
                print(mptcp)
    print("try-except错误次数：{}".format(count))
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将mptcpStatusList写入mptcpData.csv文件**********')
    with open(os.path.join(tmpDir, 'mptcpData.csv'), 'w') as f:
        for status in mptcpStatusList:
            tmpList = []
            # 在MptcpStatus.keys()中将dir(self)修改为self.__dict__以获得有序的keys．
            for key in status.keys():
                if type(status[key]) == list:
                    tmpList += status[key]
                else:
                    tmpList.append(status[key])
            f.write(','.join(map(str, tmpList)) + '\n')
    print('**********第二阶段结束**********')
    ###############################################################################




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
            
            print('解析statics.txt，生成mptcpData.csv')
            staticsFile = os.path.join(csvPath, 'mptcpData/statics.txt')
            parseStatics(staticsFile, csvPath)
    #####################################################
    print('**********Tcpdump文件解析阶段结束**********')
    ###############################################################################