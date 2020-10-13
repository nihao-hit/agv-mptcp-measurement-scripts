# drawSubflowUseTime : 通过端口号，path_index，初始序列号区分当前使用子流
# drawMptcp : 提取一段子流的snd_nxt, snd_una, snd_cwnd, ssthresh, snd_wnd, rcv_wnd, srtt进行分析
from matplotlib import pyplot as plt
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
def drawMptcp(csvFile, mergeDiffCsvFile, tmpDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读入tcpprobeData.csv文件为dataframe')
    df = pd.read_csv(csvFile, usecols=['timestamp', 'src', 'srcPort', 'dst', 'dstPort', 
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
    print('读入mergeDiff.csv文件为dataframe')
    mergeDiff = pd.read_csv(mergeDiffCsvFile, usecols=['timestamp', 'srcPort', 'path_index', 'snt_isn', 'rcv_isn'],
                            dtype={'timestamp':int, 'srcPort':int,
                                   'path_index':int,
                                   'snt_isn':int, 'rcv_isn':int})
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：细粒度统计数据构造**********')
    #####################################################
    print('提取10s-20s时长子流')
    # 实际上没有在这里过滤并提取10s-20s时长子流，而是在后面画图的时候再过滤并提取
    subflowBins = pd.cut(df['timestamp'], bins=list(mergeDiff['timestamp']), right=False).sort_index()
    # subflowBins = [interval for interval in subflowBins
    #                         if type(interval) != float and interval.length >= 10000000]
    #####################################################
    #####################################################
    print('构造10s-20s时长子流状态数据')
    subflow = list(df.groupby(subflowBins))
    #####################################################
    print('**********第二阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第三阶段：画细粒度tcp子流snd_nxt, snd_una散点图**********')
    #####################################################
    print('画细粒度tcp子流snd_nxt, snd_una散点图')
    for i in range(len(subflow)):
        if type(subflow[i][0]) != float and \
            subflow[i][0].length >= 10000000 and \
                subflow[i][0].length <= 20000000:
            #####################################################
            interval = subflow[i][0]
            print('子流时段({},{})'.format(interval.left, interval.right))
            #####################################################
            #####################################################
            print('构造子流状态统计文件夹')
            fileDir = os.path.join(tmpDir, 'subflow{}-{}'.format(interval.left, interval.right))
            if not os.path.isdir(fileDir):
                os.makedirs(fileDir)
            #####################################################
            #####################################################
            print('将子流状态写入文件')
            subflow[i][1].to_csv(os.path.join(fileDir, 'subflow.csv'))
            #####################################################
            #####################################################
            plt.title('tcp子流snd_nxt, snd_una散点图')
            plt.xlim([interval.left, interval.right])
            plt.ylim([min(subflow[i][1]['snd_nxt'].min(), subflow[i][1]['snd_una'].min()), 
                      max(subflow[i][1]['snd_nxt'].max(), subflow[i][1]['snd_una'].max())])

            # plt.xticks(xticks, xlabels, rotation=45)
            # plt.yticks(yticks, ylabels)

            plt.xlabel('time(us)')
            plt.ylabel('序列号')

            # # 设置坐标轴，不显示x轴刻度值，只显示标签值
            # plt.tick_params(labelbottom=False)

            # 设置图片长宽比，结合dpi确定图片大小
            # 将12.0改为len(xticks)/2
            # plt.rcParams['figure.figsize'] = (len(xticks)/2, 4.0)

            plt.scatter(list(subflow[i][1]['timestamp']), list(subflow[i][1]['snd_nxt']), c='red', s=0.2, label='snd_nxt')
            plt.scatter(list(subflow[i][1]['timestamp']), list(subflow[i][1]['snd_una']), c='blue', s=0.2, label='snd_una')
            plt.legend()

            figName = os.path.join(fileDir, 'tcp子流snd_nxt, snd_una散点图.png')
            print('保存到：', figName)
            plt.savefig(figName, dpi=200)
            plt.pause(1)
            plt.close()
            plt.pause(1)
            #####################################################
            #####################################################
            plt.title('tcp子流snd_cwnd散点图')
            plt.xlim([interval.left, interval.right])
            plt.ylim([subflow[i][1]['snd_cwnd'].min(), 
                      subflow[i][1]['snd_cwnd'].max()])

            # plt.xticks(xticks, xlabels, rotation=45)
            # plt.yticks(yticks, ylabels)

            plt.xlabel('time(us)')
            plt.ylabel('窗口大小()')

            # # 设置坐标轴，不显示x轴刻度值，只显示标签值
            # plt.tick_params(labelbottom=False)

            # 设置图片长宽比，结合dpi确定图片大小
            # 将12.0改为len(xticks)/2
            # plt.rcParams['figure.figsize'] = (len(xticks)/2, 4.0)

            plt.scatter(list(subflow[i][1]['timestamp']), list(subflow[i][1]['snd_cwnd']), c='red', s=0.2, label='snd_cwnd')
            plt.legend()

            figName = os.path.join(fileDir, 'tcp子流snd_cwnd散点图.png')
            print('保存到：', figName)
            plt.savefig(figName, dpi=200)
            plt.pause(1)
            plt.close()
            plt.pause(1)
            #####################################################
            #####################################################
            plt.title('tcp子流ssthresh散点图')
            plt.xlim([interval.left, interval.right])
            plt.ylim([subflow[i][1]['ssthresh'].min(), 
                      subflow[i][1]['ssthresh'].max()])

            # plt.xticks(xticks, xlabels, rotation=45)
            # plt.yticks(yticks, ylabels)

            plt.xlabel('time(us)')
            plt.ylabel('窗口大小()')

            # # 设置坐标轴，不显示x轴刻度值，只显示标签值
            # plt.tick_params(labelbottom=False)

            # 设置图片长宽比，结合dpi确定图片大小
            # 将12.0改为len(xticks)/2
            # plt.rcParams['figure.figsize'] = (len(xticks)/2, 4.0)

            plt.scatter(list(subflow[i][1]['timestamp']), list(subflow[i][1]['ssthresh']), c='blue', s=0.2, label='ssthresh')
            plt.legend()

            figName = os.path.join(fileDir, 'tcp子流ssthresh散点图.png')
            print('保存到：', figName)
            plt.savefig(figName, dpi=200)
            plt.pause(1)
            plt.close()
            plt.pause(1)
            #####################################################
            #####################################################
            plt.title('tcp子流snd_wnd, rcv_wnd散点图')
            plt.xlim([interval.left, interval.right])
            plt.ylim([min(subflow[i][1]['snd_wnd'].min(), subflow[i][1]['rcv_wnd'].min()), 
                      max(subflow[i][1]['snd_wnd'].max(), subflow[i][1]['rcv_wnd'].max())])

            # plt.xticks(xticks, xlabels, rotation=45)
            # plt.yticks(yticks, ylabels)

            plt.xlabel('time(us)')
            plt.ylabel('窗口大小()')

            # # 设置坐标轴，不显示x轴刻度值，只显示标签值
            # plt.tick_params(labelbottom=False)

            # 设置图片长宽比，结合dpi确定图片大小
            # 将12.0改为len(xticks)/2
            # plt.rcParams['figure.figsize'] = (len(xticks)/2, 4.0)

            plt.scatter(list(subflow[i][1]['timestamp']), list(subflow[i][1]['snd_wnd']), c='red', s=0.2, label='snd_wnd')
            plt.scatter(list(subflow[i][1]['timestamp']), list(subflow[i][1]['rcv_wnd']), c='blue', s=0.2, label='rcv_wnd')
            plt.legend()

            figName = os.path.join(fileDir, 'tcp子流snd_wnd, rcv_wnd散点图.png')
            print('保存到：', figName)
            plt.savefig(figName, dpi=200)
            plt.pause(1)
            plt.close()
            plt.pause(1)
            #####################################################
            #####################################################
            plt.title('tcp子流srtt散点图')
            plt.xlim([interval.left, interval.right])
            plt.ylim([subflow[i][1]['srtt'].min(), 
                      subflow[i][1]['srtt'].max()])

            # plt.xticks(xticks, xlabels, rotation=45)
            # plt.yticks(yticks, ylabels)

            plt.xlabel('time(us)')
            plt.ylabel('时延(ms)')

            # # 设置坐标轴，不显示x轴刻度值，只显示标签值
            # plt.tick_params(labelbottom=False)

            # 设置图片长宽比，结合dpi确定图片大小
            # 将12.0改为len(xticks)/2
            # plt.rcParams['figure.figsize'] = (len(xticks)/2, 4.0)

            plt.scatter(list(subflow[i][1]['timestamp']), list(subflow[i][1]['srtt']), c='red', s=0.2, label='srtt')
            plt.legend()

            figName = os.path.join(fileDir, 'tcp子流srtt散点图.png')
            print('保存到：', figName)
            plt.savefig(figName, dpi=200)
            plt.pause(1)
            plt.close()
            plt.pause(1)
            #####################################################
    print('**********第三阶段结束**********')
    ###############################################################################