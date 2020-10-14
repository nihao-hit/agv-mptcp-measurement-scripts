# drawSubflowUseTime : 通过端口号，path_index，初始序列号区分当前使用子流
#                      WLAN0与WLAN1使用时长占比饼状图, TCP子流连续使用时长CDF图, TCP子流连续使用时长分类柱状图
# drawMptcp : 提取一段子流的snd_nxt, snd_una, snd_cwnd, ssthresh, snd_wnd, rcv_wnd, srtt进行分析
#             可通过subflowLenTuple参数选择子流长度
# drawMptcpInHandover : 提取漫游事件对应的TCP子流
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

from Status import ScanStatus

# 通过端口号，path_index，初始序列号区分当前使用子流
# WLAN0与WLAN1使用时长占比饼状图, TCP子流连续使用时长CDF图, TCP子流连续使用时长分类柱状图
def drawSubflowUseTime(tcpprobeCsvFile, tmpDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读入tcpprobeData.csv文件为dataframe')
    df = pd.read_csv(tcpprobeCsvFile, usecols=['timestamp', 'src', 'srcPort', 'dst', 'dstPort', 
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
    print('提取srcPort, timestamp，观察srcPort在时间序列上的变化，并记录每个值的起始时间戳')
    srcPort = pd.Series(data=list(df['srcPort']), index=df['timestamp'])
    srcPortDiff = srcPort.replace(0, np.nan).dropna().diff().replace(0, np.nan).dropna()
    srcPortDiff = pd.concat([srcPort[:1], srcPortDiff])
    srcPortDiff = srcPortDiff.cumsum().astype(int)
    srcPortDiff.columns = ['timestamp', 'srcPort']
    #####################################################
    #####################################################
    print('提取path_index, timestamp，观察path_index在时间序列上的变化，并记录每个值的起始时间戳')
    path_index = pd.Series(data=list(df['path_index']), index=df['timestamp'])
    path_indexDiff = path_index.replace(0, np.nan).dropna().diff().replace(0, np.nan).dropna()
    path_indexDiff = pd.concat([path_index[:1], path_indexDiff])
    path_indexDiff = path_indexDiff.cumsum().astype(int)
    path_indexDiff.columns = ['timestamp', 'path_index']
    #####################################################
    #####################################################
    print('提取snt_isn, timestamp，观察snt_isn在时间序列上的变化，并记录每个值的起始时间戳')
    snt_isn = pd.Series(data=list(df['snt_isn']), index=df['timestamp'])
    snt_isnDiff = snt_isn.replace(0, np.nan).dropna().diff().replace(0, np.nan).dropna()
    snt_isnDiff = pd.concat([snt_isn[:1], snt_isnDiff])
    snt_isnDiff = snt_isnDiff.cumsum().astype(int)
    snt_isnDiff.columns = ['timestamp', 'snt_isn']

    print('提取rcv_isn, timestamp，观察rcv_isn在时间序列上的变化，并记录每个值的起始时间戳')
    rcv_isn = pd.Series(data=list(df['rcv_isn']), index=df['timestamp'])
    rcv_isnDiff = rcv_isn.replace(0, np.nan).dropna().diff().replace(0, np.nan).dropna()
    rcv_isnDiff = pd.concat([rcv_isn[:1], rcv_isnDiff])
    rcv_isnDiff = rcv_isnDiff.cumsum().astype(int)
    rcv_isnDiff.columns = ['timestamp', 'rcv_isn']
    #####################################################
    #####################################################
    print('合并单列进行时间序列上的对比')
    mergeDiff = srcPortDiff.to_frame(name='srcPort').reset_index() \
        .merge(path_indexDiff.to_frame(name='path_index').reset_index(), on='timestamp', how='outer') \
        .merge(snt_isnDiff.to_frame(name='snt_isn').reset_index(), on='timestamp', how='outer') \
        .merge(rcv_isnDiff.to_frame(name='rcv_isn').reset_index(), on='timestamp', how='outer') \
        .replace(np.nan, 0).astype(int) \
        .drop_duplicates(subset=['timestamp'], keep='first')
    if mergeDiff.iloc[-1]['timestamp'] != df.iloc[-1]['timestamp']:
        mergeDiff = mergeDiff.append(df.iloc[-1][['timestamp', 'srcPort', 'path_index', 'snt_isn', 'rcv_isn']]).reset_index(drop=True)
    #####################################################
    #####################################################
    print('提取TCP子流连续使用时段')
    subflowDuration = pd.DataFrame([(mergeDiff.iloc[i]['timestamp'], 
                                     mergeDiff.iloc[i + 1]['timestamp'],
                                     mergeDiff.iloc[i + 1]['timestamp'] - mergeDiff.iloc[i]['timestamp']
                                     ) for i in range(len(mergeDiff)-1)], columns=['timestamp', 'nextTimestamp', 'duration'])
    #                                 ) for i in range(len(mergeDiff)-1)], columns=['timestamp', 'nextTimestamp'])
    
    # print('由于tcpprobeData.csv时间轴不连续，因此统计duration稍微复杂一点：')
    # print('不能直接使用nextTimestamp - timestamp．')
    # print('而应该将数据按TCP子流连续使用时段分组，再将时间戳精度降低到秒，去重后计算总秒数．')
    # print('由于降低了时间戳精度，不到１秒也会按１秒算，因此这个总秒数会偏大一些．')
    # print('对１号车，有４ｗ多次TCP子流切换，大约增加４ｗ多秒．')
    # df['bin'] = pd.cut(df['timestamp'], bins=list(mergeDiff['timestamp']), right=False)
    # subflowDuration['duration'] = list(map(lambda subflowDf : (subflowDf['timestamp'] / 1000).astype(int).drop_duplicates().count(), dict(list(df.groupby('bin'))).values()))
    
    print('为了方便人眼观察，为UNIX时间戳列添加日期时间列')
    subflowDuration['startDate'] = subflowDuration.apply(lambda row : datetime.datetime.fromtimestamp(row['timestamp'] / 1000), axis=1)
    subflowDuration['nextStartDate'] = subflowDuration.apply(lambda row : datetime.datetime.fromtimestamp(row['nextTimestamp'] / 1000), axis=1)

    subflowDurationGroup = subflowDuration.merge(df[['timestamp', 'src']], on='timestamp', how='left').groupby('src')
    w0SubflowDuration = 0
    w1SubflowDuration = 0
    for name, group in subflowDurationGroup:
        if '151' in name:
            w0SubflowDuration = group
        else:
            w1SubflowDuration = group

    ratio = np.arange(0, 1.01, 0.01)
    #####################################################
    #####################################################
    print('构造tcp子流连续使用时长CDF数据')
    subflowDurationRatio = subflowDuration['duration'].quantile(ratio)
    w0SubflowDurationRatio = w0SubflowDuration['duration'].quantile(ratio)
    w1SubflowDurationRatio = w1SubflowDuration['duration'].quantile(ratio)
    #####################################################
    #####################################################
    print('构造tcp子流连续使用时长柱状图数据')
    bins = [0, 1000, 60 * 1000, 60 * 10 * 1000, 60 * 60 * 1000, sys.maxsize]
    labels = ['<=1s', '1s-1min', '1min-10min', '10min-1h', '>1h']
    subflowDurationBarData = pd.cut(subflowDuration['duration'], bins=bins, labels=labels).value_counts().sort_index() / len(subflowDuration)
    w0SubflowDurationBarData = pd.cut(w0SubflowDuration['duration'], bins=bins, labels=labels).value_counts().sort_index() / len(w0SubflowDuration)
    w1SubflowDurationBarData = pd.cut(w1SubflowDuration['duration'], bins=bins, labels=labels).value_counts().sort_index() / len(w1SubflowDuration)
    #####################################################
    #####################################################
    print('非图表型统计数据构造')
    statics = dict()
    for name, group in subflowDurationGroup:
        statics[name] = group['duration'].describe().astype(int)
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将关键统计数据写入文件**********')
    #####################################################
    print('将srcPort, path_index, snt_isn, rcv_isn在时间序列上的变化统计信息写入文件')
    mergeDiff.to_csv(os.path.join(tmpDir, 'mergeDiff.csv'))
    #####################################################
    #####################################################
    print('将tcp子流连续使用时段信息写入文件')
    subflowDuration.to_csv(os.path.join(tmpDir, 'subflowDuration.csv'))

    w0SubflowDuration.to_csv(os.path.join(tmpDir, 'w0SubflowDuration.csv'))

    w1SubflowDuration.to_csv(os.path.join(tmpDir, 'w1SubflowDuration.csv'))
    #####################################################
    #####################################################
    print('将tcp子流连续使用时长CDF数据统计信息写入文件')
    subflowDurationRatio.to_csv(os.path.join(tmpDir, 'subflowDurationRatio.csv'))

    w0SubflowDurationRatio.to_csv(os.path.join(tmpDir, 'w0SubflowDurationRatio.csv'))

    w1SubflowDurationRatio.to_csv(os.path.join(tmpDir, 'w1SubflowDurationRatio.csv'))
    #####################################################
    #####################################################
    print('将非图表型统计数据写入文件')
    pd.DataFrame(statics).to_csv(os.path.join(tmpDir, 'statics.csv'))
    #####################################################
    print('**********第二阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第三阶段：画WLAN0与WLAN1使用时长占比饼状图**********')
    #####################################################
    print('构造饼状图数据')
    pieData = dict()
    pieData['WLAN0'] = w0SubflowDuration['duration'].sum() / subflowDuration['duration'].sum()
    pieData['WLAN1'] = w1SubflowDuration['duration'].sum() / subflowDuration['duration'].sum()
    #####################################################
    #####################################################
    print('设置图片长宽比，结合dpi确定图片大小')
    plt.rcParams['figure.figsize'] = (6.4, 4.8)
    print('画饼状图')
    plt.title('WLAN0与WLAN1使用时长占比饼状图')

    plt.pie(pieData.values(), labels=pieData.keys(), autopct='%1.f%%')
    #####################################################
    #####################################################
    figName = os.path.join(tmpDir, 'WLAN0与WLAN1使用时长占比饼状图.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第三阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第四阶段：画TCP子流连续使用时长CDF图**********')
    #####################################################
    print('设置图片长宽比，结合dpi确定图片大小')
    plt.rcParams['figure.figsize'] = (6.4, 4.8)

    print('画CDF图前的初始化：设置标题、坐标轴')
    plt.title('TCP子流连续使用时长CDF')

    plt.xlim([0, 10000])
    plt.xlabel('时长(ms)')

    plt.ylim([0, 1])
    plt.yticks(np.arange(0, 1.1, 0.1))
    #####################################################
    #####################################################
    print("画tcp子流连续使用时长CDF图")
    cdfSubflowDuration, = plt.plot(list(subflowDurationRatio), list(subflowDurationRatio.index), c='red')
    #####################################################
    #####################################################
    print("画WLAN0连续使用时长CDF图")
    cdfW0SubflowDuration, = plt.plot(list(w0SubflowDurationRatio), list(w0SubflowDurationRatio.index), c='blue')
    #####################################################
    #####################################################
    print("画WLAN1连续使用时长CDF图")
    cdfW1SubflowDuration, = plt.plot(list(w1SubflowDurationRatio), list(w1SubflowDurationRatio.index), c='green')
    #####################################################
    #####################################################
    print("设置标注")
    plt.legend([cdfSubflowDuration, cdfW0SubflowDuration, cdfW1SubflowDuration],
            ['WLAN0+WLAN1', 'WLAN0', 'WLAN1'],
            loc='lower right')
    #####################################################
    #####################################################
    figName = os.path.join(tmpDir, 'TCP子流连续使用时长CDF.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第四阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第五阶段：画TCP子流连续使用时长分类柱状图**********')
    #####################################################
    print('设置图片长宽比，结合dpi确定图片大小')
    plt.rcParams['figure.figsize'] = (6.4, 4.8)
    print('画TCP子流连续使用时长分类柱状图')
    plt.title('TCP子流连续使用时长分类柱状图')

    width = 0.3
    x = np.arange(len(subflowDurationBarData)) - width

    plt.bar(x, list(subflowDurationBarData), width=width, label='WLAN0+WLAN1')
    plt.bar(x + width, list(w0SubflowDurationBarData), width=width, label='WLAN0', tick_label=labels)
    plt.bar(x + 2 * width, list(w1SubflowDurationBarData), width=width, label='WLAN1')
    plt.legend()
    #####################################################
    #####################################################
    figName = os.path.join(tmpDir, 'TCP子流连续使用时长分类柱状图.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第五阶段结束**********')
    ###############################################################################



# 提取一段子流的snd_nxt, snd_una, snd_cwnd, ssthresh, snd_wnd, rcv_wnd, srtt进行分析
# 可通过subflowLenTuple参数选择子流长度
def drawMptcpInSubflow(csvFile, tcpprobeCsvFile, w0SubflowDurationCsvFile, w0HoCsvFile, tmpDir, subflowLenTuple):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读取单台车的data.csv数据')
    df = pd.read_csv(csvFile, na_filter=False, usecols=['curTimestamp', 'W0pingrtt'],
                              dtype={'curTimestamp' : int, 'W0pingrtt' : int})
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
    print('读入w0SubflowDuration.csv文件为dataframe')
    w0SubflowDuration = pd.read_csv(w0SubflowDurationCsvFile, usecols=['timestamp', 'nextTimestamp', 'duration'],
                            dtype={'timestamp':int,
                                   'nextTimestamp':int,
                                   'duration':int})
    #####################################################
    #####################################################
    print('读取单台车的WLAN0漫游时段汇总.csv文件')
    w0HoDf = pd.read_csv(w0HoCsvFile, na_filter=False, usecols=['start', 'end', 'duration', 'flag'],
                            dtype={'start' : int, 
                                    'end' : int,
                                    'duration' : int,
                                    'flag' : int})
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：画细粒度TCP子流snd_nxt, snd_una, snd_cwnd, ssthresh, snd_wnd, rcv_wnd, srtt散点图**********')
    #####################################################
    print('构造subflow-duration文件夹')
    fileDir = os.path.join(tmpDir, 'subflow-duration')
    if not os.path.isdir(fileDir):
        os.makedirs(fileDir)
    print('设置图片长宽比，结合dpi确定图片大小')
    plt.rcParams['figure.figsize'] = (6.4, 4.8)
    #####################################################
    #####################################################
    print('提取WLAN0的10s-20s时长连续使用TCP子流，WLAN1的暂时不予分析')
    # TODO: 这里只分析了受WLAN0漫游影响的WLAN0的TCP子流，是否需要研究不同网络的漫游事件与TCP子流的交叉影响
    w0SubflowDurationFiltered = w0SubflowDuration[(w0SubflowDuration['duration'] >= subflowLenTuple[0]) & (w0SubflowDuration['duration'] <= subflowLenTuple[1])]
    for _, duration in w0SubflowDurationFiltered.iterrows():
        startTime = duration['timestamp']
        endTime = duration['nextTimestamp']
        tcpprobeDf['bin'] = pd.cut(tcpprobeDf['timestamp'], bins=[startTime, endTime], right=False)
        subflow = list(tcpprobeDf.groupby('bin'))[0][1]
        #####################################################
        print('构造snd_nxt, snd_una, snd_cwnd, ssthresh, snd_wnd, rcv_wnd, srtt散点图各自的子文件夹')
        snd_nxtAndsnd_unaDir = os.path.join(fileDir, 'snd_nxt-snd_una')
        if not os.path.isdir(snd_nxtAndsnd_unaDir):
            os.makedirs(snd_nxtAndsnd_unaDir)
        snd_cwndDir = os.path.join(fileDir, 'snd_cwnd')
        if not os.path.isdir(snd_cwndDir):
            os.makedirs(snd_cwndDir)
        ssthreshDir = os.path.join(fileDir, 'ssthresh')
        if not os.path.isdir(ssthreshDir):
            os.makedirs(ssthreshDir)
        snd_wndAndrcv_wndDir = os.path.join(fileDir, 'snd_wnd-rcv_wnd')
        if not os.path.isdir(snd_wndAndrcv_wndDir):
            os.makedirs(snd_wndAndrcv_wndDir)
        srttDir = os.path.join(fileDir, 'srtt')
        if not os.path.isdir(srttDir):
            os.makedirs(srttDir)
        csvDir = os.path.join(fileDir, 'csv')
        if not os.path.isdir(csvDir):
            os.makedirs(csvDir)
        #####################################################
        #####################################################
        print('将子流状态写入文件')
        subflow.to_csv(os.path.join(csvDir, '{}-{}.csv'.format(startTime, endTime)))
        #####################################################
        #####################################################
        # 提取所有在此时段的漫游事件
        innerHoList = w0HoDf[(w0HoDf['start'] >= startTime) & (w0HoDf['start'] <= endTime)]
        
        # 提取在此时段的ping时延数据，并过滤
        df['bin'] = pd.cut(df['curTimestamp'], bins=[int(startTime / 1000), int(endTime / 1000)], right=False)
        rttDf = list(df.groupby('bin'))[0][1]
        rttDf = rttDf[rttDf['W0pingrtt'] % 1000 != 0]
        #####################################################
        #####################################################
        plt.title('TCP子流snd_nxt, snd_una散点图')
        plt.xlim([startTime, endTime])
        # plt.ylim([min(subflow['snd_nxt'].min(), subflow['snd_una'].min()), 
        #           max(subflow['snd_nxt'].max(), subflow['snd_una'].max())])

        plt.xlabel('time(ms)')
        plt.ylabel('seq')

        plt.scatter(list(subflow['timestamp']), list(subflow['snd_nxt']), c='red', s=1, alpha=0.7, label='snd_nxt')
        plt.scatter(list(subflow['timestamp']), list(subflow['snd_una']), c='blue', s=1, alpha=0.7, label='snd_una')
        # 画漫游事件竖线
        for _, innerHo in innerHoList.iterrows():
            label = 'ap1->ap2'
            c = 'green'
            if innerHo['flag'] == 0:
                label = 'ap1->not-associated->ap2'
                c = 'red'
            if innerHo['flag'] == 1:
                label = 'ap1->not-associated->ap1'
                c = 'blue'
            width = int(innerHo['duration'] / 1000) if innerHo['duration'] >= 1000 else 1
            plt.axvline(innerHo['start'], lw=width, color=c, label=label, alpha=0.7)
        plt.legend()

        figName = os.path.join(snd_nxtAndsnd_unaDir, '{}-{}.png'.format(startTime, endTime))
        print('保存到：', figName)
        plt.savefig(figName, dpi=200)
        plt.pause(1)
        plt.close()
        plt.pause(1)
        #####################################################
        #####################################################
        plt.title('TCP子流snd_cwnd散点图')
        #　过滤离群值
        snd_cwnd = subflow[(subflow['snd_cwnd'] <= subflow['snd_cwnd'].quantile(0.9)) & (subflow['snd_cwnd'] >= subflow['snd_cwnd'].quantile(0.1))]
        plt.xlim([startTime, endTime])
        plt.ylim([snd_cwnd['snd_cwnd'].min() - 1, 
                  snd_cwnd['snd_cwnd'].max() + 1])

        plt.xlabel('time(ms)')
        plt.yticks(range(snd_cwnd['snd_cwnd'].min() - 1,  snd_cwnd['snd_cwnd'].max() + 2))

        plt.scatter(list(snd_cwnd['timestamp']), list(snd_cwnd['snd_cwnd']), c='red', s=1, alpha=0.7, label='snd_cwnd')
        # 画漫游事件竖线
        for _, innerHo in innerHoList.iterrows():
            label = 'ap1->ap2'
            c = 'green'
            if innerHo['flag'] == 0:
                label = 'ap1->not-associated->ap2'
                c = 'red'
            if innerHo['flag'] == 1:
                label = 'ap1->not-associated->ap1'
                c = 'blue'
            width = int(innerHo['duration'] / 1000) if innerHo['duration'] >= 1000 else 1
            plt.axvline(innerHo['start'], lw=width, color=c, label=label, alpha=0.7)
        plt.legend()

        figName = os.path.join(snd_cwndDir, '{}-{}.png'.format(startTime, endTime))
        print('保存到：', figName)
        plt.savefig(figName, dpi=200)
        plt.pause(1)
        plt.close()
        plt.pause(1)
        #####################################################
        #####################################################
        plt.title('TCP子流ssthresh散点图')
        # 过滤离群值
        ssthresh = subflow[(subflow['ssthresh'] <= subflow['ssthresh'].quantile(0.9)) & (subflow['ssthresh'] >= subflow['ssthresh'].quantile(0.1))]
        plt.xlim([startTime, endTime])
        plt.ylim([ssthresh['ssthresh'].min() - 1, 
                  ssthresh['ssthresh'].max() + 1])

        plt.xlabel('time(ms)')
        plt.yticks(range(ssthresh['ssthresh'].min() - 1,  ssthresh['ssthresh'].max() + 2))
        
        plt.scatter(list(ssthresh['timestamp']), list(ssthresh['ssthresh']), c='red', s=1, alpha=0.7, label='ssthresh')
        # 画漫游事件竖线
        for _, innerHo in innerHoList.iterrows():
            label = 'ap1->ap2'
            c = 'green'
            if innerHo['flag'] == 0:
                label = 'ap1->not-associated->ap2'
                c = 'red'
            if innerHo['flag'] == 1:
                label = 'ap1->not-associated->ap1'
                c = 'blue'
            width = int(innerHo['duration'] / 1000) if innerHo['duration'] >= 1000 else 1
            plt.axvline(innerHo['start'], lw=width, color=c, label=label, alpha=0.7)
        plt.legend()

        figName = os.path.join(ssthreshDir, '{}-{}.png'.format(startTime, endTime))
        print('保存到：', figName)
        plt.savefig(figName, dpi=200)
        plt.pause(1)
        plt.close()
        plt.pause(1)
        #####################################################
        #####################################################
        plt.title('TCP子流snd_wnd, rcv_wnd散点图')
        plt.xlim([startTime, endTime])
        # plt.ylim([min(subflow['snd_wnd'].min(), subflow['rcv_wnd'].min()), 
        #           max(subflow['snd_wnd'].max(), subflow['rcv_wnd'].max())])

        plt.xlabel('time(ms)')

        plt.scatter(list(subflow['timestamp']), list(subflow['snd_wnd']), c='red', s=1, alpha=0.7, label='snd_wnd')
        plt.scatter(list(subflow['timestamp']), list(subflow['rcv_wnd']), c='blue', s=1, alpha=0.7, label='rcv_wnd')
        # 画漫游事件竖线
        for _, innerHo in innerHoList.iterrows():
            label = 'ap1->ap2'
            c = 'green'
            if innerHo['flag'] == 0:
                label = 'ap1->not-associated->ap2'
                c = 'red'
            if innerHo['flag'] == 1:
                label = 'ap1->not-associated->ap1'
                c = 'blue'
            width = int(innerHo['duration'] / 1000) if innerHo['duration'] >= 1000 else 1
            plt.axvline(innerHo['start'], lw=width, color=c, label=label, alpha=0.7)
        plt.legend()

        figName = os.path.join(snd_wndAndrcv_wndDir, '{}-{}.png'.format(startTime, endTime))
        print('保存到：', figName)
        plt.savefig(figName, dpi=200)
        plt.pause(1)
        plt.close()
        plt.pause(1)
        #####################################################
        #####################################################
        plt.title('TCP子流srtt折线图')
        plt.xlim([startTime, endTime])
        # plt.ylim([min(subflow['srtt'].min(), rttDf['W0pingrtt'].min()),
        #           max(subflow['srtt'].max(), rttDf['W0pingrtt'].max())])

        plt.xlabel('time(ms)')
        plt.ylabel('时延(ms)')

        plt.plot(list(subflow['timestamp']), list(subflow['srtt']), 
                 c='red', marker='+', ms=4, alpha=0.7, label='srtt')
        # 画ping时延数据
        plt.plot(list(rttDf['curTimestamp'] * 1000), list(rttDf['W0pingrtt']), 
                 c='blue', marker='x', ms=4, alpha=0.7, label='ping-rtt')
        # 画漫游事件竖线
        for _, innerHo in innerHoList.iterrows():
            label = 'ap1->ap2'
            c = 'green'
            if innerHo['flag'] == 0:
                label = 'ap1->not-associated->ap2'
                c = 'red'
            if innerHo['flag'] == 1:
                label = 'ap1->not-associated->ap1'
                c = 'blue'
            width = int(innerHo['duration'] / 1000) if innerHo['duration'] >= 1000 else 1
            plt.axvline(innerHo['start'], lw=width, color=c, label=label, alpha=0.7)
        plt.legend()

        figName = os.path.join(srttDir, '{}-{}.png'.format(startTime, endTime))
        print('保存到：', figName)
        plt.savefig(figName, dpi=200)
        plt.pause(1)
        plt.close()
        plt.pause(1)
        #####################################################
    print('**********第二阶段结束**********')
    ###############################################################################



# 提取漫游事件对应的TCP子流的snd_nxt, snd_una, snd_cwnd, ssthresh, snd_wnd, rcv_wnd, srtt进行分析
def drawMptcpInHandover(csvFile, tcpprobeCsvFile, w0HoCsvFile, tmpDir, subflowLen):
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
    print('读取单台车的WLAN0漫游时段汇总.csv文件')
    w0HoDf = pd.read_csv(w0HoCsvFile, na_filter=False, usecols=['start', 'end', 'duration', 'flag'],
                            dtype={'start' : int, 
                                    'end' : int,
                                    'duration' : int,
                                    'flag' : int})
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：画细粒度TCP子流snd_nxt, snd_una, snd_cwnd, ssthresh, snd_wnd, rcv_wnd, srtt散点图**********')
    #####################################################
    print('设置图片长宽比，结合dpi确定图片大小')
    plt.rcParams['figure.figsize'] = (6.4, 4.8)
    #####################################################
    #####################################################
    print('按漫游时长各分类提取时段数据进行分析')
    bins = [0, 200, 1000, 5000, sys.maxsize]
    labels = ['<=200ms', '200ms-1s', '1s-5s', '>5s']
    w0HoDurationCategory = dict(list(w0HoDf.groupby(pd.cut(w0HoDf['duration'], bins=bins, labels=labels).sort_index())))
    #####################################################
    #####################################################
    for durationLabel, hoList in w0HoDurationCategory.items():
        fileDir = os.path.join(tmpDir, durationLabel)
        if not os.path.isdir(fileDir):
            os.makedirs(fileDir)
        for _, ho in hoList.iterrows():
            #####################################################
            # 提取分析时段为[漫游开始时刻-10s, 漫游结束时刻+10s]
            startTime = ho['start'] - subflowLen / 2
            endTime = ho['end'] + subflowLen / 2
            tcpprobeDf['bin'] = pd.cut(tcpprobeDf['timestamp'], [startTime, endTime])
            subflow = list(tcpprobeDf.groupby('bin'))[0][1]
            #####################################################
            #####################################################
            # 对分析时段内的TCP状态按照子流分组(src, srcPort)
            subflowGroup = dict(list(subflow.groupby(['src', 'srcPort'], sort=False)))
            # 为每个子流分配两种颜色
            colors = ['red', 'orange', 'green', 'blue', 'purple', 'black']
            colorsMap = dict()
            idx = 0
            for k in subflowGroup.keys():
                if k not in colorsMap:
                    colorsMap[k] = idx
                    idx = (idx + 2) % len(colors)
            # 对某些列进行标准化
            for k, v in subflowGroup.items():
                subflowGroup[k]['snd_nxt'] = v['snd_nxt'] - v.iloc[0]['snd_una']
                subflowGroup[k]['snd_una'] = v['snd_una'] - v.iloc[0]['snd_una']
            #####################################################
            #####################################################
            # 提取所有在此时段的漫游事件
            innerHoList = w0HoDf[(w0HoDf['start'] >= startTime) & (w0HoDf['start'] <= endTime)]
            
            # 提取在此时段的ping时延数据，并过滤
            df['bin'] = pd.cut(df['curTimestamp'], bins=[int(startTime / 1000), int(endTime / 1000)], right=False)
            rttDf = list(df.groupby('bin'))[0][1]
            w0PingRttDf = rttDf[rttDf['W0pingrtt'] % 1000 != 0]
            w1PingRttDf = rttDf[rttDf['W1pingrtt'] % 1000 != 0]
            #####################################################
            #####################################################
            print('构造snd_nxt, snd_una, snd_cwnd, ssthresh, snd_wnd, rcv_wnd, srtt散点图各自的子文件夹')
            snd_nxtAndsnd_unaDir = os.path.join(fileDir, 'snd_nxt-snd_una')
            if not os.path.isdir(snd_nxtAndsnd_unaDir):
                os.makedirs(snd_nxtAndsnd_unaDir)
            snd_cwndDir = os.path.join(fileDir, 'snd_cwnd')
            if not os.path.isdir(snd_cwndDir):
                os.makedirs(snd_cwndDir)
            ssthreshDir = os.path.join(fileDir, 'ssthresh')
            if not os.path.isdir(ssthreshDir):
                os.makedirs(ssthreshDir)
            snd_wndAndrcv_wndDir = os.path.join(fileDir, 'snd_wnd-rcv_wnd')
            if not os.path.isdir(snd_wndAndrcv_wndDir):
                os.makedirs(snd_wndAndrcv_wndDir)
            srttDir = os.path.join(fileDir, 'srtt')
            if not os.path.isdir(srttDir):
                os.makedirs(srttDir)
            csvDir = os.path.join(fileDir, 'csv')
            if not os.path.isdir(csvDir):
                os.makedirs(csvDir)
            #####################################################
            #####################################################
            print('将子流状态写入文件')
            subflow.to_csv(os.path.join(csvDir, '{}-{}.csv'.format(startTime, endTime)))
            #####################################################
            #####################################################
            plt.title('TCP子流snd_nxt, snd_una散点图')

            plt.xlim([startTime, endTime])

            plt.xlabel('Time(ms)')
            plt.ylabel('Seq(normalized)')

            subflowNum = 1
            for k, v in subflowGroup.items():
                label = 'WLAN{}, Subflow{}, '.format(0 if '151' in k[0] else 1, subflowNum)
                subflowNum += 1
                plt.scatter(list(v['timestamp']), list(v['snd_nxt']), 
                            c=colors[colorsMap[k]], s=1, alpha=0.7, marker='v',
                            label=label + 'snd_nxt')
                plt.scatter(list(v['timestamp']), list(v['snd_una']), 
                            c=colors[colorsMap[k] + 1], s=1, alpha=0.7, marker='^',
                            label=label + 'snd_una')
            # 画漫游事件竖线
            for _, innerHo in innerHoList.iterrows():
                label = 'ap1->ap2'
                c = 'green'
                if innerHo['flag'] == 0:
                    label = 'ap1->not-associated->ap2'
                    c = 'red'
                if innerHo['flag'] == 1:
                    label = 'ap1->not-associated->ap1'
                    c = 'blue'
                width = int(innerHo['duration'] / 1000) if innerHo['duration'] >= 1000 else 1
                plt.axvline(innerHo['start'], lw=width, color=c, label=label, alpha=0.7)
            plt.legend()

            # 强制yticks为整数值
            plt.figure().gca().yaxis.set_major_locator(MaxNLocator(integer=True))
            figName = os.path.join(snd_nxtAndsnd_unaDir, '{}-{}.png'.format(startTime, endTime))
            print('保存到：', figName)
            plt.savefig(figName, dpi=200)
            plt.pause(1)
            plt.close()
            plt.pause(1)
            #####################################################
            #####################################################
            plt.title('TCP子流snd_cwnd散点图')
            
            plt.xlim([startTime, endTime])

            plt.xlabel('Time(ms)')
            
            subflowNum = 1
            for k, v in subflowGroup.items():
                label = 'WLAN{}, Subflow{}, '.format(0 if '151' in k[0] else 1, subflowNum)
                subflowNum += 1
                plt.scatter(list(v['timestamp']), list(v['snd_cwnd']), 
                            c=colors[colorsMap[k]], s=1, alpha=0.7,
                            label=label + 'snd_cwnd')
            # 画漫游事件竖线
            for _, innerHo in innerHoList.iterrows():
                label = 'ap1->ap2'
                c = 'green'
                if innerHo['flag'] == 0:
                    label = 'ap1->not-associated->ap2'
                    c = 'red'
                if innerHo['flag'] == 1:
                    label = 'ap1->not-associated->ap1'
                    c = 'blue'
                width = int(innerHo['duration'] / 1000) if innerHo['duration'] >= 1000 else 1
                plt.axvline(innerHo['start'], lw=width, color=c, label=label, alpha=0.7)
            plt.legend()

            # 强制yticks为整数值
            plt.figure().gca().yaxis.set_major_locator(MaxNLocator(integer=True))
            figName = os.path.join(snd_cwndDir, '{}-{}.png'.format(startTime, endTime))
            print('保存到：', figName)
            plt.savefig(figName, dpi=200)
            plt.pause(1)
            plt.close()
            plt.pause(1)
            #####################################################
            #####################################################
            plt.title('TCP子流ssthresh散点图')
            
            plt.xlim([startTime, endTime])

            plt.xlabel('Time(ms)')
        
            subflowNum = 1
            for k, v in subflowGroup.items():
                label = 'WLAN{}, Subflow{}, '.format(0 if '151' in k[0] else 1, subflowNum)
                subflowNum += 1
                plt.scatter(list(v['timestamp']), list(v['ssthresh']), 
                            c=colors[colorsMap[k]], s=1, alpha=0.7,
                            label=label + 'ssthresh')
            # 画漫游事件竖线
            for _, innerHo in innerHoList.iterrows():
                label = 'ap1->ap2'
                c = 'green'
                if innerHo['flag'] == 0:
                    label = 'ap1->not-associated->ap2'
                    c = 'red'
                if innerHo['flag'] == 1:
                    label = 'ap1->not-associated->ap1'
                    c = 'blue'
                width = int(innerHo['duration'] / 1000) if innerHo['duration'] >= 1000 else 1
                plt.axvline(innerHo['start'], lw=width, color=c, label=label, alpha=0.7)
            plt.legend()

            # 强制yticks为整数值
            plt.figure().gca().yaxis.set_major_locator(MaxNLocator(integer=True))
            figName = os.path.join(ssthreshDir, '{}-{}.png'.format(startTime, endTime))
            print('保存到：', figName)
            plt.savefig(figName, dpi=200)
            plt.pause(1)
            plt.close()
            plt.pause(1)
            #####################################################
            #####################################################
            plt.title('TCP子流snd_wnd, rcv_wnd散点图')
            
            plt.xlim([startTime, endTime])

            plt.xlabel('Time(ms)')

            subflowNum = 1
            for k, v in subflowGroup.items():
                label = 'WLAN{}, Subflow{}, '.format(0 if '151' in k[0] else 1, subflowNum)
                subflowNum += 1
                plt.scatter(list(v['timestamp']), list(v['snd_wnd']), 
                            c=colors[colorsMap[k]], s=1, alpha=0.7, marker='>',
                            label=label + 'snd_wnd')
                plt.scatter(list(v['timestamp']), list(v['rcv_wnd']), 
                            c=colors[colorsMap[k] + 1], s=1, alpha=0.7, marker='<',
                            label=label + 'rcv_wnd')
            # 画漫游事件竖线
            for _, innerHo in innerHoList.iterrows():
                label = 'ap1->ap2'
                c = 'green'
                if innerHo['flag'] == 0:
                    label = 'ap1->not-associated->ap2'
                    c = 'red'
                if innerHo['flag'] == 1:
                    label = 'ap1->not-associated->ap1'
                    c = 'blue'
                width = int(innerHo['duration'] / 1000) if innerHo['duration'] >= 1000 else 1
                plt.axvline(innerHo['start'], lw=width, color=c, label=label, alpha=0.7)
            plt.legend()

            # 强制yticks为整数值
            plt.figure().gca().yaxis.set_major_locator(MaxNLocator(integer=True))
            figName = os.path.join(snd_wndAndrcv_wndDir, '{}-{}.png'.format(startTime, endTime))
            print('保存到：', figName)
            plt.savefig(figName, dpi=200)
            plt.pause(1)
            plt.close()
            plt.pause(1)
            #####################################################
            #####################################################
            plt.title('TCP子流srtt折线图')

            plt.xlim([startTime, endTime])

            plt.xlabel('Time(ms)')
            plt.ylabel('时延(ms)')

            subflowNum = 1
            for k, v in subflowGroup.items():
                label = 'WLAN{}, Subflow{}, '.format(0 if '151' in k[0] else 1, subflowNum)
                subflowNum += 1
                plt.plot(list(v['timestamp']), list(v['srtt']), 
                         c=colors[colorsMap[k]], alpha=0.7, marker='+', ms=4,
                         label=label + 'srtt')
            # 画ping时延数据
            plt.plot(list(w0PingRttDf['curTimestamp'] * 1000), list(w0PingRttDf['W0pingrtt']), 
                    c='purple', marker='x', ms=4, alpha=0.7, label='wlan0-ping-rtt')
            plt.plot(list(w1PingRttDf['curTimestamp'] * 1000), list(w1PingRttDf['W1pingrtt']), 
                    c='black', marker='x', ms=4, alpha=0.7, label='wlan1-ping-rtt')
            # 画漫游事件竖线
            for _, innerHo in innerHoList.iterrows():
                label = 'ap1->ap2'
                c = 'green'
                if innerHo['flag'] == 0:
                    label = 'ap1->not-associated->ap2'
                    c = 'red'
                if innerHo['flag'] == 1:
                    label = 'ap1->not-associated->ap1'
                    c = 'blue'
                width = int(innerHo['duration'] / 1000) if innerHo['duration'] >= 1000 else 1
                plt.axvline(innerHo['start'], lw=width, color=c, label=label, alpha=0.7)
            plt.legend()

            # 强制yticks为整数值
            plt.figure().gca().yaxis.set_major_locator(MaxNLocator(integer=True))
            figName = os.path.join(srttDir, '{}-{}.png'.format(startTime, endTime))
            print('保存到：', figName)
            plt.savefig(figName, dpi=200)
            plt.pause(1)
            plt.close()
            plt.pause(1)
            #####################################################
    print('**********第二阶段结束**********')
    ###############################################################################