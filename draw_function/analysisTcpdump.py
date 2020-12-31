from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
import numpy as np
import pandas as pd 
import time
import datetime
import os
import sys

def drawMptcp(mptcpCsvFileList, subCsvFileList, mptcpDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读入mptcpData.csv文件为mptcpDf，subflowData.csv文件为subDf')
    mptcpDfList = []
    for mptcpCsvFile in mptcpCsvFileList:
        mptcpDf = pd.read_csv(mptcpCsvFile, dtype={'connStats':str})
        mptcpDfList.append(mptcpDf)
    mptcpAll = pd.concat(mptcpDfList, ignore_index=True)

    subDfList = []
    for subCsvFile in subCsvFileList:
        subDf = pd.read_csv(subCsvFile, dtype={'subStats':str})
        subDfList.append(subDf)
    subAll = pd.concat(subDfList, ignore_index=True)
    #####################################################
    #####################################################
    print('只保留data-mptcp，丢弃ka-mptcp，生成统计列')
    mptcpAll = mptcpAll[mptcpAll.connStats.str.contains('7070')]

    # 保留时长单位为s而不是ms
    mptcpAll['duration'] = (mptcpAll['originMptcpLastTs'] - mptcpAll['originMptcpFirstTs']) / 1e3
    mptcpAll['dataDuration'] = (mptcpAll['originMptcpLastDataTs'] - mptcpAll['originMptcpFirstDataTs']) / 1e3

    mptcpAll['originRate'] = mptcpAll['originMptcpPayloadByte'] / mptcpAll['dataDuration']
    mptcpAll['originPacketRate'] = mptcpAll['originMptcpDataPacket'] / mptcpAll['dataDuration']
    mptcpAll['originPacketSize'] = mptcpAll['originMptcpPayloadByte'] / mptcpAll['originMptcpDataPacket']

    mptcpAll['remoteRate'] = mptcpAll['remoteMptcpPayloadByte'] / mptcpAll['dataDuration']
    mptcpAll['remotePacketRate'] = mptcpAll['remoteMptcpDataPacket'] / mptcpAll['dataDuration']
    mptcpAll['remotePacketSize'] = mptcpAll['remoteMptcpPayloadByte'] / mptcpAll['remoteMptcpDataPacket']
    #####################################################
    #####################################################
    print('只保留data-sub，丢弃ka-sub，生成统计列')
    subAll = subAll[subAll.subStats.str.contains('7070')]
    subAll['duration'] = (subAll['originSubLastTs'] - subAll['originSubFirstTs']) / 1e3
    subAll['type'] = subAll.apply(lambda row : 'sub-wlan0' if '151' in row['subStats'] else 'sub-wlan1', axis=1)
    #####################################################
    #####################################################
    print('非图表型统计数据构造')
    staticsFile = os.path.join(mptcpDir, 'statics.csv')
    statics = dict()
    if os.path.isfile(staticsFile):
        statics = pd.read_csv(staticsFile).to_dict('list')

    # 数据总数
    statics['mptcp总数'] = len(mptcpAll)
    statics['sub-wlan0总数'] = len(subAll[subAll['type'] == 'sub-wlan0'])
    statics['sub-wlan1总数'] = len(subAll[subAll['type'] == 'sub-wlan1'])
    # 流量
    statics['上行速率 (B/s)'] = mptcpAll.loc[(mptcpAll['originMptcpPayloadByte'] != 0) & 
                                            (mptcpAll['dataDuration'] != 0), 'originRate'].mean()
    statics['下行速率 (B/s)'] = mptcpAll.loc[(mptcpAll['remoteMptcpPayloadByte'] != 0) & 
                                            (mptcpAll['dataDuration'] != 0), 'remoteRate'].mean()
    # 发包
    statics['上行包速率 (个/s)'] = mptcpAll.loc[(mptcpAll['originMptcpDataPacket'] != 0) & 
                                              (mptcpAll['dataDuration'] != 0), 'originPacketRate'].mean()
    statics['下行包速率 (个/s)'] = mptcpAll.loc[(mptcpAll['remoteMptcpDataPacket'] != 0) & 
                                              (mptcpAll['dataDuration'] != 0), 'remotePacketRate'].mean()
    # 包大小
    statics['上行包大小 (B/个)'] = mptcpAll.loc[(mptcpAll['originMptcpPayloadByte'] != 0), 'originPacketSize'].mean()
    statics['下行包大小 (B/个)'] = mptcpAll.loc[(mptcpAll['remoteMptcpPayloadByte'] != 0), 'remotePacketSize'].mean()
    # 连接长度
    statics['mptcp-duration'] = mptcpAll['duration'].mean()
    statics['sub-wlan0-duration'] = subAll[subAll['type'] == 'sub-wlan0']['duration'].mean()
    statics['sub-wlan1-duration'] = subAll[subAll['type'] == 'sub-wlan1']['duration'].mean()
    # subflow存在比例
    statics['sub-wlan0-duration-ratio'] = subAll[subAll['type'] == 'sub-wlan0']['duration'].sum() / mptcpAll['duration'].sum()
    statics['sub-wlan1-duration-ratio'] = subAll[subAll['type'] == 'sub-wlan1']['duration'].sum() / mptcpAll['duration'].sum()
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：关键数据写入文件**********')
    #####################################################
    print('将非图表型统计数据写入文件')
    pd.DataFrame(statics, index=[0]).to_csv(os.path.join(mptcpDir, 'statics.csv'))
    #####################################################
    print('**********第二阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第三阶段：画mptcp分析图**********')
    #####################################################
    print('画mptcp分析图')
    fig, ((mptcpAx, subW0Ax, subW1Ax),
          (originPsAx, remotePsAx, subUseAx)) = plt.subplots(2, 3)
    
    sns.violinplot(data=mptcpAll, y='duration', ax=mptcpAx)
    mptcpAx.set_xlabel('mptcp')
    mptcpAx.set_ylabel('duration (s)')

    sns.violinplot(data=subAll[subAll['type'] == 'sub-wlan0'], y='duration', ax=subW0Ax)
    subW0Ax.set_xlabel('subflow-wlan0')
    subW0Ax.set_ylabel('duration (s)')

    sns.violinplot(data=subAll[subAll['type'] == 'sub-wlan1'], y='duration', ax=subW1Ax)
    subW1Ax.set_xlabel('subflow-wlan1')
    subW1Ax.set_ylabel('duration (s)')

    sns.violinplot(data=mptcpAll, y='originPacketSize', ax=originPsAx)
    originPsAx.set_xlabel('uplink')
    originPsAx.set_ylabel('packetSize (Byte)')

    sns.violinplot(data=mptcpAll, y='remotePacketSize', ax=remotePsAx)
    remotePsAx.set_xlabel('downlink')
    remotePsAx.set_ylabel('packetSize (Byte)')
    
    subW0Use = subAll[subAll['type'] == 'sub-wlan0']['originSubPacket'].sum() / mptcpAll['originMptcpPacket'].sum()
    subUseAx.pie(x=[subW0Use, 1 - subW0Use], labels=['subflow-wlan0', 'subflow-wlan1'], autopct='%1.f%%')
    #####################################################
    #####################################################
    # 设置标题
    fig.suptitle("mptcp分析图")

    # 调整图像避免截断xlabel
    fig.tight_layout()
    
    figName = os.path.join(mptcpDir, 'mptcp分析图.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第三阶段结束**********')
    ###############################################################################




if __name__ == '__main__':
    # 显示中文
    import locale
    locale.setlocale(locale.LC_CTYPE, 'zh_CN.utf8')
    from pylab import *
    mpl.rcParams['font.sans-serif'] = ['SimHei']
    mpl.rcParams['axes.unicode_minus'] = False

    ###############################################################################
    print('**********MPTCP协议分析->第一阶段：所有车数据统计**********')
    #####################################################
    print('构造文件夹')
    topTmpPath = r'/home/cx/Desktop/sdb-dir/tmp'
    topDataPath = r'/home/cx/Desktop/sdb-dir/'
    
    mptcpCsvFileList = [os.path.join(os.path.join(topTmpPath, path), 'mptcpData.csv') 
                        for path in os.listdir(topTmpPath)
                        if os.path.isfile(os.path.join(os.path.join(topTmpPath, path), 'mptcpData.csv'))]
    subCsvFileList = [os.path.join(os.path.split(f)[0], 'subflowData.csv') for f in mptcpCsvFileList]
    #####################################################
    #####################################################
    print('mptcp所有车数据分析')
    mptcpDir = os.path.join(topDataPath, 'analysisMptcp')
    print(mptcpDir)
    if not os.path.isdir(mptcpDir):
        os.makedirs(mptcpDir)
    
    drawMptcp(mptcpCsvFileList, subCsvFileList, mptcpDir)
    #####################################################
    print('**********MPTCP协议分析->第一阶段结束**********')
    ###############################################################################