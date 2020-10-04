from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
import numpy as np
import pandas as pd 
import time
import os
import sys

from Status import ScanStatus

# 通过端口号，path_index，初始序列号区分当前使用子流
def drawTcp(csvFile, tmpDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读入csv文件为dataframe')
    df = pd.read_csv(csvFile, usecols=['curTimestamp', 'src', 'srcPort', 'dst', 'dstPort', 
                                       'length', 
                                       'snd_nxt', 'snd_una', 
                                       'snd_cwnd', 'ssthresh',
                                       'snd_wnd', 'srtt', 'rcv_wnd',
                                       'path_index', 'map_data_len', 'map_data_seq', 'map_subseq',
                                       'snt_isn', 'rcv_isn'],
                            dtype={'curTimestamp':int, 'src':str, 'srcPort':int, 'dst':str, 'dstPort':int, 
                                   'length':int, 
                                   'snd_nxt':int, 'snd_una':int, 
                                   'snd_cwnd':int, 'ssthresh':int,
                                   'snd_wnd':int, 'srtt':int, 'rcv_wnd':int,
                                   'path_index':int, 'map_data_len':int, 'map_data_seq':int, 'map_subseq':int,
                                   'snt_isn':int, 'rcv_isn':int})
    #####################################################
    # #####################################################
    # print('将30.113.151.替换为151, 30.113.127.替换为127，方便统计时间序列上src的变化')
    # df.loc['151' in df['src']] = 151
    # df.loc['127' in df['src']] = 127
    # #####################################################
    #####################################################
    # print('提取src, curTimestamp，观察src在时间序列上的变化，并记录每个值的起始时间戳')
    # src = pd.Series(data=list(df['src']), index=df['curTimestamp'])
    # srcDiff = src.replace(0, np.nan).dropna().diff().replace(0, np.nan).dropna()
    # srcDiff = pd.concat([src[:1], srcDiff])
    # srcDiff = srcDiff.cumsum().astype(int)
    # srcDiff.columns = ['curTimestamp', 'path_index']

    print('提取srcPort, curTimestamp，观察srcPort在时间序列上的变化，并记录每个值的起始时间戳')
    srcPort = pd.Series(data=list(df['srcPort']), index=df['curTimestamp'])
    srcPortDiff = srcPort.replace(0, np.nan).dropna().diff().replace(0, np.nan).dropna()
    srcPortDiff = pd.concat([srcPort[:1], srcPortDiff])
    srcPortDiff = srcPortDiff.cumsum().astype(int)
    srcPortDiff.columns = ['curTimestamp', 'srcPort']

#     print('提取dstPort, curTimestamp，观察dstPort在时间序列上的变化，并记录每个值的起始时间戳')
#     dstPort = pd.Series(data=list(df['dstPort']), index=df['curTimestamp'])
#     dstPortDiff = dstPort.replace(0, np.nan).dropna().diff().replace(0, np.nan).dropna()
#     dstPortDiff = pd.concat([dstPort[:1], dstPortDiff])
#     dstPortDiff = dstPortDiff.cumsum().astype(int)
#     dstPortDiff.columns = ['curTimestamp', 'dstPort']
    #####################################################
    #####################################################
    print('提取path_index, curTimestamp，观察path_index在时间序列上的变化，并记录每个值的起始时间戳')
    path_index = pd.Series(data=list(df['path_index']), index=df['curTimestamp'])
    path_indexDiff = path_index.replace(0, np.nan).dropna().diff().replace(0, np.nan).dropna()
    path_indexDiff = pd.concat([path_index[:1], path_indexDiff])
    path_indexDiff = path_indexDiff.cumsum().astype(int)
    path_indexDiff.columns = ['curTimestamp', 'path_index']

#     print('提取map_data_len, curTimestamp，观察map_data_len在时间序列上的变化，并记录每个值的起始时间戳')
#     map_data_len = pd.Series(data=list(df['map_data_len']), index=df['curTimestamp'])
#     map_data_lenDiff = map_data_len.replace(0, np.nan).dropna().diff().replace(0, np.nan).dropna()
#     map_data_lenDiff = pd.concat([map_data_len[:1], map_data_lenDiff])
#     map_data_lenDiff = map_data_lenDiff.cumsum().astype(int)

#     print('提取map_data_seq, curTimestamp，观察map_data_seq在时间序列上的变化，并记录每个值的起始时间戳')
#     map_data_seq = pd.Series(data=list(df['map_data_seq']), index=df['curTimestamp'])
#     map_data_seqDiff = map_data_seq.replace(0, np.nan).dropna().diff().replace(0, np.nan).dropna()
#     map_data_seqDiff = pd.concat([map_data_seq[:1], map_data_seqDiff])
#     map_data_seqDiff = map_data_seqDiff.cumsum().astype(int)

#     print('提取map_subseq, curTimestamp，观察map_subseq在时间序列上的变化，并记录每个值的起始时间戳')
#     map_subseq = pd.Series(data=list(df['map_subseq']), index=df['curTimestamp'])
#     map_subseqDiff = map_subseq.replace(0, np.nan).dropna().diff().replace(0, np.nan).dropna()
#     map_subseqDiff = pd.concat([map_subseq[:1], map_subseqDiff])
#     map_subseqDiff = map_subseqDiff.cumsum().astype(int)
    #####################################################
    #####################################################
    print('提取snt_isn, curTimestamp，观察snt_isn在时间序列上的变化，并记录每个值的起始时间戳')
    snt_isn = pd.Series(data=list(df['snt_isn']), index=df['curTimestamp'])
    snt_isnDiff = snt_isn.replace(0, np.nan).dropna().diff().replace(0, np.nan).dropna()
    snt_isnDiff = pd.concat([snt_isn[:1], snt_isnDiff])
    snt_isnDiff = snt_isnDiff.cumsum().astype(int)
    snt_isnDiff.columns = ['curTimestamp', 'snt_isn']

    print('提取rcv_isn, curTimestamp，观察rcv_isn在时间序列上的变化，并记录每个值的起始时间戳')
    rcv_isn = pd.Series(data=list(df['rcv_isn']), index=df['curTimestamp'])
    rcv_isnDiff = rcv_isn.replace(0, np.nan).dropna().diff().replace(0, np.nan).dropna()
    rcv_isnDiff = pd.concat([rcv_isn[:1], rcv_isnDiff])
    rcv_isnDiff = rcv_isnDiff.cumsum().astype(int)
    rcv_isnDiff.columns = ['curTimestamp', 'rcv_isn']
    #####################################################
    #####################################################
    print('合并单列进行时间序列上的对比')
    mergeDiff = srcPortDiff.to_frame(name='srcPort').reset_index() \
        .merge(path_indexDiff.to_frame(name='path_index').reset_index(), on='curTimestamp', how='outer') \
        .merge(snt_isnDiff.to_frame(name='snt_isn').reset_index(), on='curTimestamp', how='outer') \
        .merge(rcv_isnDiff.to_frame(name='rcv_isn').reset_index(), on='curTimestamp', how='outer') \
        .replace(np.nan, 0).astype(int)
    if mergeDiff.iloc[-1]['curTimestamp'] != df.iloc[-1]['curTimestamp']:
        mergeDiff = mergeDiff.append(df.iloc[-1][['curTimestamp', 'srcPort', 'path_index', 'snt_isn', 'rcv_isn']]).reset_index(drop=True)
    #####################################################
    #####################################################
    print('构造tcp子流连续使用时长CDF数据')
    subflowDuration = pd.DataFrame([(mergeDiff.iloc[i]['curTimestamp'], mergeDiff.iloc[i + 1]['curTimestamp'] - mergeDiff.iloc[i]['curTimestamp']) for i in range(len(mergeDiff)-1)], columns=['curTimestamp', 'duration'])
    subflowDurationGroup = subflowDuration.merge(df[['curTimestamp', 'src']], on='curTimestamp', how='left').groupby('src')
    w0SubflowDuration = 0
    w1SubflowDuration = 0
    for name, group in subflowDurationGroup:
        if '151' in name:
            w0SubflowDuration = group
        else:
            w1SubflowDuration = group

    ratio = np.arange(0, 1.01, 0.01)
    subflowDurationRatio = subflowDuration['duration'].quantile(ratio)
    w0SubflowDurationRatio = w0SubflowDuration['duration'].quantile(ratio)
    w1SubflowDurationRatio = w1SubflowDuration['duration'].quantile(ratio)
    #####################################################
    #####################################################
    print('构造tcp子流连续使用时长柱状图数据')
    bins = [0, 1, 60, 60 * 10, 60 * 60, sys.maxsize]
    labels = ['<=1s', '1s-1min', '1min-10min', '10min-1h', '>1h']
    subflowDurationBarData = pd.cut(subflowDuration['duration'], bins=bins, labels=labels).value_counts().sort_index() / len(subflowDuration)
    w0SubflowDurationBarData = pd.cut(w0SubflowDuration['duration'], bins=bins, labels=labels).value_counts().sort_index() / len(w0SubflowDuration)
    w1SubflowDurationBarData = pd.cut(w1SubflowDuration['duration'], bins=bins, labels=labels).value_counts().sort_index() / len(w1SubflowDuration)
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
    print('将tcp子流连续使用时长CDF数据统计信息写入文件')
    subflowDuration.to_csv(os.path.join(tmpDir, 'subflowDuration.csv'))
    subflowDurationRatio.to_csv(os.path.join(tmpDir, 'subflowDurationRatio.csv'))

    w0SubflowDuration.to_csv(os.path.join(tmpDir, 'w0SubflowDuration.csv'))
    w0SubflowDurationRatio.to_csv(os.path.join(tmpDir, 'w0SubflowDurationRatio.csv'))

    w1SubflowDuration.to_csv(os.path.join(tmpDir, 'w1SubflowDuration.csv'))
    w1SubflowDurationRatio.to_csv(os.path.join(tmpDir, 'w1SubflowDurationRatio.csv'))
    #####################################################
    print('**********第二阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第三阶段：画WLAN0与WLAN1使用时长占比饼状图**********')
    #####################################################
    print('构造饼状图数据')
    pieData = df['src'].to_frame(name='src').dropna().groupby('src').size().to_frame('count').reset_index()
    #####################################################
    #####################################################
    print('画饼状图')
    plt.title('WLAN0与WLAN1使用时长占比饼状图')

    plt.pie(list(pieData['count']), labels=list(pieData['src']), autopct='%1.2f%%')
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
    print('**********第四阶段：画tcp子流连续使用时长CDF图**********')
    #####################################################
    print('画CDF图前的初始化：设置标题、坐标轴')
    plt.title('tcp子流连续使用时长CDF')

    # plt.xlim(left=0)
    plt.xlabel('时长')

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
    figName = os.path.join(tmpDir, 'tcp子流连续使用时长CDF.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第四阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第五阶段：画tcp子流连续使用时长分类柱状图**********')
    #####################################################
    print('画tcp子流连续使用时长分类柱状图')
    plt.title('tcp子流连续使用时长分类柱状图')

    width = 0.3
    x = np.arange(len(subflowDurationBarData)) - width

    plt.bar(x, list(subflowDurationBarData), width=width, label='WLAN0+WLAN1')
    plt.bar(x + width, list(w0SubflowDurationBarData), width=width, label='WLAN0', tick_label=labels)
    plt.bar(x + 2 * width, list(w1SubflowDurationBarData), width=width, label='WLAN0')
    #####################################################
    #####################################################
    figName = os.path.join(tmpDir, 'tcp子流连续使用时长分类柱状图.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第五阶段结束**********')
    ###############################################################################