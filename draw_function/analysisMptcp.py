# drawMptcpFeature: 使用提取的完整mptcp连接画mptcp连接长度小提琴图，流量分配饼状图
# drawMptcpInHandover : 提取漫游事件前后tcp状态做时序图
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

# 使用提取的完整mptcp连接画mptcp连接长度小提琴图，流量分配饼状图
def drawMptcpFeature(mptcpCsvFileList, subCsvFileList, mptcpDir):
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

    # 保留时长单位为s而不是us
    mptcpAll['duration'] = (mptcpAll['originMptcpLastTs'] - mptcpAll['originMptcpFirstTs']) / 1e6
    mptcpAll['dataDuration'] = (mptcpAll['originMptcpLastDataTs'] - mptcpAll['originMptcpFirstDataTs']) / 1e6

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
    subAll['duration'] = (subAll['originSubLastTs'] - subAll['originSubFirstTs']) / 1e6
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
    statics['mptcp-duration(s)'] = mptcpAll['duration'].mean()
    statics['sub-wlan0-duration(s)'] = subAll[subAll['type'] == 'sub-wlan0']['duration'].mean()
    statics['sub-wlan1-duration(s)'] = subAll[subAll['type'] == 'sub-wlan1']['duration'].mean()
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



# 提取漫游事件前后tcp状态做时序图
def drawMptcpInHandover(csvFile, tcpprobeCsvFile, tcpdumpCsvFile, w0HoCsvFile, w1HoCsvFile, tmpDir, count):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读取单台车的data.csv数据')
    df = pd.read_csv(csvFile, na_filter=False, usecols=['curTimestamp', 'W0pingrtt', 'W1pingrtt'],
                              dtype={'curTimestamp' : int, 
                                     'W0pingrtt' : int,
                                     'W1pingrtt' : int})
    #####################################################
    #####################################################
    print('读入tcpprobeData.csv文件为dataframe')
    tcpprobeDf = pd.read_csv(tcpprobeCsvFile, usecols=['timestamp', 'src', 'srcPort', 'dst', 'dstPort', 
                                       'length', 
                                       'snd_nxt', 'snd_una', 
                                       'snd_cwnd', 'ssthresh',
                                       'snd_wnd', 'srtt', 'rcv_wnd',
                                       'path_index', 'map_data_len', 'map_data_seq', 'map_subseq',
                                       'snt_isn', 'rcv_isn'],
                            dtype={'timestamp':int, 'src':str, 'srcPort':int, 'dst':str, 'dstPort':int, 
                                   'length':int, 
                                   'snd_nxt':int, 'snd_una':int, 
                                   'snd_cwnd':int, 'ssthresh':int,
                                   'snd_wnd':int, 'srtt':int, 'rcv_wnd':int,
                                   'path_index':int, 'map_data_len':int, 'map_data_seq':int, 'map_subseq':int,
                                   'snt_isn':int, 'rcv_isn':int})
    #####################################################
    #####################################################
    print('读入tcpdumpData.csv文件为dataframe')
    tcpdumpDf = pd.read_csv(tcpdumpCsvFile, usecols=['timestamp', 'src','srcPort','dst','dstPort','tcpDataLen','seq','ack',
                                                    'segType','dsn', 'dataAck', 'subSeq', 'mptcpDataLen',
                                                    'tsval', 'tsecr'],
                            dtype={'timestamp':int, 'src':str, 'srcPort':int, 'dst':str, 'dstPort':int, 'tcpDataLen':int, 'seq':int, 'ack':int,
                                   'segType':str, 'dsn':int, 'dataAck':int, 'subSeq':int, 'mptcpDataLen':int,
                                   'tsval':int, 'tsecr':int})
    #####################################################
    #####################################################
    print('读取单台车的WLAN0漫游时段汇总.csv文件')
    w0HoDf = pd.read_csv(w0HoCsvFile, na_filter=False, usecols=['start', 'end', 'duration', 'flag'],
                            dtype={'start' : int, 
                                    'end' : int,
                                    'duration' : int,
                                    'flag' : int})
    #####################################################
    #####################################################
    print('读取单台车的WLAN1漫游时段汇总.csv文件')
    w1HoDf = pd.read_csv(w1HoCsvFile, na_filter=False, usecols=['start', 'end', 'duration', 'flag'],
                            dtype={'start' : int, 
                                    'end' : int,
                                    'duration' : int,
                                    'flag' : int})
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：画漫游事件前后mptcp时序图**********')
    #####################################################
    print('按漫游时长各分类提取时段数据进行分析')
    bins = [0, 200, 1e3, 30e3, sys.maxsize]
    labels = ['<200ms', '200ms-1s', '1s-30s', '>=30s']
    w0HoDurationCategory = dict(list(w0HoDf.groupby(pd.cut(w0HoDf['duration'], 
        bins=bins, labels=labels, right=False).sort_index())))
    w1HoDurationCategory = dict(list(w1HoDf.groupby(pd.cut(w1HoDf['duration'], 
        bins=bins, labels=labels, right=False).sort_index())))
    #####################################################
    #####################################################
    print('按漫游时长各分类提取时段数据进行分析')
    w0HoList = list(w0HoDf.groupby(pd.cut(w0HoDf['duration'], [0, 1e3]).sort_index()))[0][1]
    w1HoList = list(w1HoDf.groupby(pd.cut(w1HoDf['duration'], [0, 1e3]).sort_index()))[0][1]
    #####################################################
    #####################################################
    for wlanStr, wlanHoList in {'wlan0': w0HoDurationCategory, 'wlan1': w1HoDurationCategory}.items():
        for durationStr, hoList in wlanHoList.items():
            fileDir = os.path.join(os.path.join(tmpDir, wlanStr), durationStr)
            if not os.path.isdir(fileDir):
                os.makedirs(fileDir)
            innerCount = count
            for _, ho in hoList.iterrows():
                if innerCount == 0:
                    break
                innerCount -= 1
                #####################################################
                # 提取分析时段为[漫游开始时刻-5s, 漫游结束时刻+5s]
                startTime = ho['start'] - int(5e6)
                endTime = ho['end'] + int(5e6)
                tcpprobeDf['bin'] = pd.cut(tcpprobeDf['timestamp'], [startTime, endTime])
                innerTpDf = list(tcpprobeDf.groupby('bin'))[0][1]

                tcpdumpDf['bin'] = pd.cut(tcpdumpDf['timestamp'], [startTime, endTime])
                innerTdDf = list(tcpdumpDf.groupby('bin'))[0][1]
                # 过滤服务器端口非7070的tcpdump数据
                innerTdDf = innerTdDf[(innerTdDf['srcPort'] == 7070) | (innerTdDf['dstPort'] == 7070)]
                if innerTdDf.empty or innerTpDf.empty:
                    continue
                # 划分wlan0与wlan1
                innerTpDf['wlan'] = innerTpDf.apply(
                    lambda row : 'wlan{}'.format(0 if '151' in row['src'] else 1), axis=1)
                innerTdDf['wlan'] = innerTdDf.apply(
                    lambda row: 'wlan0' if '151' in row['src'] or '151' in row['dst'] else 'wlan1', axis=1)
                # C1=red, C0=blue
                innerTdDf['color'] = innerTdDf.apply(lambda row: 'C0' if row['wlan'] == 'wlan0' else 'C1', axis=1)
                # 提取漫游事件
                w0InnerHoList = w0HoDf[((w0HoDf['start'] > startTime) & (w0HoDf['start'] < endTime)) |
                                    ((w0HoDf['end'] > startTime) & (w0HoDf['end'] < endTime))]
                w1InnerHoList = w1HoDf[((w1HoDf['start'] > startTime) & (w1HoDf['start'] < endTime)) |
                                    ((w1HoDf['end'] > startTime) & (w1HoDf['end'] < endTime))]
                #####################################################
                #####################################################
                # 画tcp time sequence graph
                plt.xlabel('timestamp (s)')
                xticks = np.linspace(startTime, endTime, 10, dtype=np.int64)
                xlabels = list(map(lambda x: str(int(x / 1e6))[-2:], xticks))
                plt.xticks(xticks, xlabels)
                plt.ylabel('seq/ack number')
                plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
                # 构造时序数据
                agvToServerDf = innerTdDf[(innerTdDf['dst'] == '30.113.129.7') 
                                        & (innerTdDf['dsn'] != 0)]
                serverToAgvDf = innerTdDf[(innerTdDf['src'] == '30.113.129.7')
                                        & (innerTdDf['dataAck'] != 0)]
                #####################################################
                #####################################################
                # 画dataAck横线
                try:
                    ackHxmin = serverToAgvDf['timestamp'].tolist()[:-1]
                    ackHxmax = serverToAgvDf['timestamp'].tolist()[1:]
                    ackHy = serverToAgvDf['dataAck'].tolist()[:-1]
                    ackHColors = serverToAgvDf['color'].tolist()[:-1]
                    ackH = list(zip(ackHy, ackHxmin, ackHxmax, ackHColors))

                    plt.hlines(*zip(*ackH), linestyles='dotted')
                except Exception as e:
                    print('画dataAck横线: {}'.format(e))
                #####################################################
                #####################################################
                # 画dataAck竖线
                try:
                    ackVymin = serverToAgvDf['dataAck'].tolist()[:-1]
                    ackVymax = serverToAgvDf['dataAck'].tolist()[1:]
                    ackVx = serverToAgvDf['timestamp'].tolist()[1:]
                    ackVColors = serverToAgvDf['color'].tolist()[1:]
                    ackV = list(zip(ackVx, ackVymin, ackVymax, ackVColors))
                    plt.vlines(*zip(*ackV), linestyles='dotted')

                except Exception as e:
                    print('画dataAck竖线: {}'.format(e))
                #####################################################
                #####################################################
                # 画dsn竖线
                try:
                    seqVymin = agvToServerDf['dsn'].tolist()
                    seqVymax = (agvToServerDf['dsn'] + agvToServerDf['mptcpDataLen']).tolist()
                    seqVx = agvToServerDf['timestamp'].tolist()
                    seqVColors = agvToServerDf['color'].tolist()
                    seqV = list(zip(seqVx, seqVymin, seqVymax, seqVColors))
                    plt.vlines(*zip(*seqV))
    
                except Exception as e:
                    print('画dsn竖线: {}'.format(e))
                #####################################################
                #####################################################
                # 画漫游竖线
                for _, row in w0InnerHoList.iterrows():
                    plt.axvspan(row['start'], row['end'], alpha=0.3, color='C0')
                for _, row in w1InnerHoList.iterrows():
                    plt.axvspan(row['start'], row['end'], alpha=0.3, color='C1')
                #####################################################
                #####################################################
                # 构造时延数据
                df['timestamp'] = (df['curTimestamp'] * 1e6).astype(int)
                df['bin'] = pd.cut(df['timestamp'], bins=[startTime, endTime], right=False)
                rttDf = list(df.groupby('bin'))[0][1]
                # # w0PingRtt
                # w0PingRttDf = rttDf[rttDf['W0pingrtt'] % 1000 != 0][['timestamp', 'W0pingrtt']]
                # w0PingRttDf = w0PingRttDf.rename(columns={'W0pingrtt': 'data'})
                # w0PingRttDf['data_type'] = 'w0PingRtt'
                # w0PingRttDf['wlan'] = 'wlan0'
                # # w1PingRtt
                # w1PingRttDf = rttDf[rttDf['W1pingrtt'] % 1000 != 0][['timestamp', 'W1pingrtt']]
                # w1PingRttDf = w1PingRttDf.rename(columns={'W1pingrtt': 'data'})
                # w1PingRttDf['data_type'] = 'w1PingRtt'
                # w1PingRttDf['wlan'] = 'wlan1'
                # srtt
                srttDf = innerTpDf[['timestamp', 'srtt', 'wlan']]
                srttDf = srttDf.rename(columns={'srtt': 'data'})
                srttDf['data_type'] = 'srtt'
                # rtt
                tsvalDf = agvToServerDf[['timestamp', 'tsval', 'wlan']]
                tsecrDf = serverToAgvDf[['timestamp', 'tsecr']]
                tsoptRttDf = tsvalDf.merge(tsecrDf, how='inner', left_on='tsval', 
                    right_on='tsecr', suffixes=('_start', '_end'))
                tsoptRttDf['rtt'] = ((tsoptRttDf['timestamp_end'] - 
                                    tsoptRttDf['timestamp_start']) / 1e3).astype(int)
                # # 记录状态以debug
                # tsoptRttDf.to_csv(os.path.join(fileDir, '{}:{}-{}.csv'.format(wlanStr, ho['start'], ho['end'])))
                tsoptRttDf = tsoptRttDf[['timestamp_end', 'rtt', 'wlan']] \
                    .rename(columns={'timestamp_end': 'timestamp', 'rtt': 'data'})
                tsoptRttDf['data_type'] = 'rtt'

                delayDf = pd.concat([srttDf, tsoptRttDf], ignore_index=True)
                # 画时延
                delayAx = plt.twinx()
                sns.lineplot(data=delayDf, x='timestamp', y='data', hue='wlan', 
                    style='data_type', ms=4, markers={'srtt': 'o', 'rtt': 's'},
                    ax=delayAx)
                delayAx.set_ylabel('delay (ms)')
                delayAx.get_yaxis().set_major_locator(MaxNLocator(integer=True))
                #####################################################
                #####################################################     
                # 设置标题
                plt.title("mptcp时序图")

                # 减小字体
                plt.rcParams.update({'font.size': 6})

                # 调整图像避免截断xlabel
                plt.tight_layout()

                plt.savefig(os.path.join(fileDir, '{}:{}-{}.png'.format(wlanStr, ho['start'], ho['end'])), dpi=200)
                plt.pause(1)
                plt.close()
                plt.pause(1)
                #####################################################     
    print('**********第二阶段结束**********')
    ###############################################################################




if __name__ == '__main__':
    # 显示中文
    import locale
    locale.setlocale(locale.LC_CTYPE, 'zh_CN.utf8')
    from pylab import *
    mpl.rcParams['font.sans-serif'] = ['SimHei']
    mpl.rcParams['axes.unicode_minus'] = False

    ###############################################################################
    print('**********MPTCP协议分析->第一阶段：单车数据统计**********')
    #####################################################
    for i in range(1, 42):
        st = time.time()

        fileName = '30.113.151.' + str(i)
        print(fileName)
        csvPath = os.path.join(r'/home/cx/Desktop/sdb-dir/tmp', fileName)
        mptcpCsvFile = os.path.join(csvPath, 'mptcpData.csv')
        subCsvFile = os.path.join(csvPath, 'subflowData.csv')
        csvFile = os.path.join(csvPath, 'data.csv')
        tcpprobeCsvFile = os.path.join(csvPath, 'tcpprobeData.csv')
        tcpdumpCsvFile = os.path.join(csvPath, 'tcpdumpData.csv')
        if os.path.isdir(csvPath):
            print('mptcp分析')
            mptcpDir = os.path.join(csvPath, 'analysisMptcp')
            print(mptcpDir)
            if not os.path.isdir(mptcpDir):
                os.makedirs(mptcpDir)
            print('使用提取的完整mptcp连接画mptcp连接长度小提琴图，流量分配饼状图')
            drawMptcpFeature([mptcpCsvFile], [subCsvFile], mptcpDir)

            print('提取漫游事件前后tcp状态做时序图')
            count = 5000
            w0HoCsvFile = os.path.join(csvPath, 'analysisHandover/WLAN0漫游时段汇总.csv')
            w1HoCsvFile = os.path.join(csvPath, 'analysisHandover/WLAN1漫游时段汇总.csv')
            drawMptcpInHandover(csvFile, tcpprobeCsvFile, tcpdumpCsvFile, w0HoCsvFile, w1HoCsvFile, mptcpDir, count)
    
        et = time.time()
        print('单车{}MPTCP协议分析耗时{}s'.format(fileName, int(et - st)))
    #####################################################
    print('**********MPTCP协议分析->第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********MPTCP协议分析->第二阶段：所有车数据统计**********')
    #####################################################
    st = time.time()
    
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
    
    drawMptcpFeature(mptcpCsvFileList, subCsvFileList, mptcpDir)

    et = time.time()
    print('所有车MPTCP协议分析耗时{}s'.format(int(et - st)))
    #####################################################
    print('**********MPTCP协议分析->第二阶段结束**********')
    ###############################################################################