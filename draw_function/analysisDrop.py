# drawDrop : 画单台车或所有车的掉线热力图
# drawDropLinechart : 画单台车的掉线折线图(两个关键字参数：１是时间划分粒度，２是时段截取)
# exploreHoAndDrop : 探究网络漫游与网络掉线的关系
# exploreMptcpDropAndAgvSuspend : 探究mptcp掉线与agv停车的关系
from matplotlib import pyplot as plt 
import seaborn as sns
import numpy as np
import pandas as pd 
import time
import datetime
import os

# 画单台车或所有车的掉线热力图
def drawDrop(csvFileList, dropDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读入所有data.csv文件，构造minPingRtt列')
    dfList = []
    for csvFile in csvFileList:
        df = pd.read_csv(csvFile, na_filter=False, usecols=['curTimestamp', 
                                       'W0pingrtt', 'W1pingrtt', 'srtt',
                                       'curPosX', 'curPosY'],
                              dtype={'curTimestamp' : int, 
                                     'W0pingrtt' : int, 
                                     'W1pingrtt' : int,
                                     'srtt' : int,
                                     'curPosX' : int,
                                     'curPosY' : int})
        dfList.append(df)
    dfAll = pd.concat(dfList, ignore_index=True)
    dfAll['minPingRtt'] = dfAll.apply(lambda x: min(x['W0pingrtt'], x['W1pingrtt']), axis=1)
    #####################################################
    #####################################################
    print('分别提取W0pingrtt, W1pingrtt, minPingRtt, srtt列对应值等于30000，即超时30s时刻数据，作为掉线数据')
    print('为了方便人眼观察，为UNIX时间戳列添加日期时间列')
    # 2020/12/19:15: 当*DropDf为空时，apply()会抛出错误，fixed.
    w0DropDf = dfAll[(dfAll['W0pingrtt'] == 30000) & ((dfAll['curPosX'] != 0) | (dfAll['curPosY'] != 0))].reset_index(drop=True)
    if len(w0DropDf) != 0:
        w0DropDf['date'] = w0DropDf.apply(lambda row : datetime.datetime.fromtimestamp(row['curTimestamp']), axis=1)

    w1DropDf = dfAll[(dfAll['W1pingrtt'] == 30000) & ((dfAll['curPosX'] != 0) | (dfAll['curPosY'] != 0))].reset_index(drop=True)
    if len(w1DropDf) != 0:
        w1DropDf['date'] = w1DropDf.apply(lambda row : datetime.datetime.fromtimestamp(row['curTimestamp']), axis=1)

    minDropDf = dfAll[(dfAll['minPingRtt'] == 30000) & ((dfAll['curPosX'] != 0) | (dfAll['curPosY'] != 0))].reset_index(drop=True)
    if len(minDropDf) != 0:
        minDropDf['date'] = minDropDf.apply(lambda row : datetime.datetime.fromtimestamp(row['curTimestamp']), axis=1)

    srttDropDf = dfAll[(dfAll['srtt'] == 30000) & ((dfAll['curPosX'] != 0) | (dfAll['curPosY'] != 0))].reset_index(drop=True)
    if len(srttDropDf) != 0:
        srttDropDf['date'] = srttDropDf.apply(lambda row : datetime.datetime.fromtimestamp(row['curTimestamp']), axis=1)
    #####################################################
    #####################################################
    print('分别构造掉线热力图数据')
    # １．提取坐标；２．过滤(0, 0)；３．重置索引
    # ４．按坐标分组；５．统计各坐标分组长度；６．生成新列count；７．重置索引；
    # ８．转换dataframe为二元数组坐标轴；９．将nan置为0；
    # ９．将index也就是posY转换为int；
    # １０．将columns也就是posX转换为int;
    # １１．使用连续的posY, posX替换index, columns，并返回二元数组．
    
    # 2020/12/19:15: 当*DropMap为空时，reindex()会导致dtype变为float64，因此结尾再强转一次类型．
    w0DropMap = w0DropDf[['curPosX', 'curPosY']][(w0DropDf['curPosX'] != 0) | (w0DropDf['curPosY'] != 0)].reset_index(drop=True) \
        .groupby(['curPosX', 'curPosY']).size().to_frame('count').reset_index() \
        .pivot(index='curPosY', columns='curPosX', values='count').fillna(0).astype(int)
    w0DropMap.index = w0DropMap.index.astype(int)
    w0DropMap.columns = w0DropMap.columns.astype(int)
    w0DropMap = w0DropMap.reindex(index=range(139), columns=range(265), fill_value=0).values.astype(int)

    w1DropMap = w1DropDf[['curPosX', 'curPosY']][(w1DropDf['curPosX'] != 0) | (w1DropDf['curPosY'] != 0)].reset_index(drop=True) \
        .groupby(['curPosX', 'curPosY']).size().to_frame('count').reset_index() \
        .pivot(index='curPosY', columns='curPosX', values='count').fillna(0).astype(int)
    w1DropMap.index = w1DropMap.index.astype(int)
    w1DropMap.columns = w1DropMap.columns.astype(int)
    w1DropMap = w1DropMap.reindex(index=range(139), columns=range(265), fill_value=0).values.astype(int)

    minDropMap = minDropDf[['curPosX', 'curPosY']][(minDropDf['curPosX'] != 0) | (minDropDf['curPosY'] != 0)].reset_index(drop=True) \
        .groupby(['curPosX', 'curPosY']).size().to_frame('count').reset_index() \
        .pivot(index='curPosY', columns='curPosX', values='count').fillna(0).astype(int)
    minDropMap.index = minDropMap.index.astype(int)
    minDropMap.columns = minDropMap.columns.astype(int)
    minDropMap = minDropMap.reindex(index=range(139), columns=range(265), fill_value=0).values.astype(int)

    srttDropMap = srttDropDf[['curPosX', 'curPosY']][(srttDropDf['curPosX'] != 0) | (srttDropDf['curPosY'] != 0)].reset_index(drop=True) \
        .groupby(['curPosX', 'curPosY']).size().to_frame('count').reset_index() \
        .pivot(index='curPosY', columns='curPosX', values='count').fillna(0).astype(int)
    srttDropMap.index = srttDropMap.index.astype(int)
    srttDropMap.columns = srttDropMap.columns.astype(int)
    srttDropMap = srttDropMap.reindex(index=range(139), columns=range(265), fill_value=0).values.astype(int)
    #####################################################
    #####################################################
    print('非图表型统计数据构造')
    staticsFile = os.path.join(dropDir, 'statics.csv')
    statics = dict()
    if os.path.isfile(staticsFile):
        statics = pd.read_csv(staticsFile).to_dict('list')

    # 数据总数，时间跨度，时间粒度
    statics['wlan0单网络掉线次数'] = len(w0DropDf)
    statics['wlan1单网络掉线次数'] = len(w1DropDf)
    statics['双网络理论掉线次数'] = len(minDropDf)
    statics['双网络+mptcp实际掉线次数'] = len(srttDropDf)

    statics['start'] = dfAll['curTimestamp'].min()
    statics['end'] = dfAll['curTimestamp'].max()
    statics['duration'] = statics['end'] - statics['start']
    statics['时间戳粒度'] = '秒'
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将关键统计数据写入文件**********')
    #####################################################
    print('将wlan0单网络、wlan1单网络、双网络理论掉线、双网络+mptcp实际掉线时刻数据与掉线热力图数据写入文件')
    w0DropDf.to_csv(os.path.join(dropDir, 'wlan0单网络掉线时刻.csv'))
    # list转dataframe自动写入则携带行列信息，通过index=False与header=False参数设置不写入行列信息．
    pd.DataFrame(w0DropMap).to_csv(os.path.join(dropDir, 'wlan0单网络掉线热力图.csv'), index=False, header=False)
    
    w1DropDf.to_csv(os.path.join(dropDir, 'wlan1单网络掉线时刻.csv'))
    # list转dataframe自动写入则携带行列信息，通过index=False与header=False参数设置不写入行列信息．
    pd.DataFrame(w1DropMap).to_csv(os.path.join(dropDir, 'wlan1单网络掉线热力图.csv'), index=False, header=False)

    minDropDf.to_csv(os.path.join(dropDir, '双网络理论掉线时刻.csv'))
    # list转dataframe自动写入则携带行列信息，通过index=False与header=False参数设置不写入行列信息．
    pd.DataFrame(minDropMap).to_csv(os.path.join(dropDir, '双网络理论掉线热力图.csv'), index=False, header=False)

    srttDropDf.to_csv(os.path.join(dropDir, '双网络+mptcp实际掉线时刻.csv'))
    # list转dataframe自动写入则携带行列信息，通过index=False与header=False参数设置不写入行列信息．
    pd.DataFrame(srttDropMap).to_csv(os.path.join(dropDir, '双网络+mptcp实际掉线热力图.csv'), index=False, header=False)
    #####################################################
    #####################################################
    print('将非图表型统计数据写入文件')
    pd.DataFrame(statics, index=[0]).to_csv(os.path.join(dropDir, 'statics.csv'))
    #####################################################
    print('**********第二阶段结束**********')
    ###############################################################################


    #####################################################
    print('抵消第一个图长宽比不起作用的bug，画两次')
    print("画wlan0单网络掉线热力图")
    plt.title('wlan0单网络掉线热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)
    # 暂时不清楚平均掉线上限
    ax = sns.heatmap(w0DropMap, cmap="Blues", vmin=0, 
                     cbar_kws={'label' : '掉线次数'})
    plt.xlabel('坐标X轴')
    plt.ylabel('坐标Y轴')
    # 逆置Y轴
    ax.invert_yaxis()
    plt.savefig(os.path.join(dropDir, 'wlan0单网络掉线热力图.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################


    ###############################################################################
    print('**********第三阶段：画掉线热力图**********')
    #####################################################
    print("画wlan0单网络掉线热力图")
    plt.title('wlan0单网络掉线热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)
    # 2020/12/7:11: 若刻度小于等于5，步长设为1；否则步长设为5.
    cbarMaxTick = max(list(map(max, w0DropMap)))
    cbarTicks = range(0, cbarMaxTick + 1) if cbarMaxTick <= 5 else range(0, cbarMaxTick + 1, 5)
    ax = sns.heatmap(w0DropMap, cmap="Blues", vmin=0, 
                     cbar_kws={'ticks': cbarTicks, 'label' : '掉线次数'})
    plt.xlabel('坐标X轴')
    plt.ylabel('坐标Y轴')
    # 逆置Y轴
    ax.invert_yaxis()
    plt.savefig(os.path.join(dropDir, 'wlan0单网络掉线热力图.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    #####################################################
    print("画wlan1单网络掉线热力图")
    plt.title('wlan1单网络掉线热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)
    # 2020/12/7:11: 若刻度小于等于5，步长设为1；否则步长设为5.
    cbarMaxTick = max(list(map(max, w1DropMap)))
    cbarTicks = range(0, cbarMaxTick + 1) if cbarMaxTick <= 5 else range(0, cbarMaxTick + 1, 5)
    ax = sns.heatmap(w1DropMap, cmap="Blues", vmin=0, 
                     cbar_kws={'ticks': cbarTicks, 'label' : '掉线次数'})
    plt.xlabel('坐标X轴')
    plt.ylabel('坐标Y轴')
    # 逆置Y轴
    ax.invert_yaxis()
    plt.savefig(os.path.join(dropDir, 'wlan1单网络掉线热力图.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    #####################################################
    print("画双网络理论掉线热力图")
    plt.title('双网络理论掉线热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)
    # 2020/12/7:11: 若刻度小于等于5，步长设为1；否则步长设为5.
    cbarMaxTick = max(list(map(max, minDropMap)))
    cbarTicks = range(0, cbarMaxTick + 1) if cbarMaxTick <= 5 else range(0, cbarMaxTick + 1, 5)
    ax = sns.heatmap(minDropMap, cmap="Blues", vmin=0, 
                     cbar_kws={'ticks': cbarTicks, 'label' : '掉线次数'})
    plt.xlabel('坐标X轴')
    plt.ylabel('坐标Y轴')
    # 逆置Y轴
    ax.invert_yaxis()
    plt.savefig(os.path.join(dropDir, '双网络理论掉线热力图.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    #####################################################
    print("画双网络+mptcp实际掉线热力图")
    plt.title('双网络+mptcp实际掉线热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)
    # 2020/12/7:11: 若刻度小于等于5，步长设为1；否则步长设为5.
    cbarMaxTick = max(list(map(max, srttDropMap)))
    cbarTicks = range(0, cbarMaxTick + 1) if cbarMaxTick <= 5 else range(0, cbarMaxTick + 1, 5)
    ax = sns.heatmap(srttDropMap, cmap="Blues", vmin=0, 
                     cbar_kws={'ticks': cbarTicks, 'label' : '掉线次数'})
    plt.xlabel('坐标X轴')
    plt.ylabel('坐标Y轴')
    # 逆置Y轴
    ax.invert_yaxis()
    plt.savefig(os.path.join(dropDir, '双网络+mptcp实际掉线热力图.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第三阶段结束**********')
    ###############################################################################



# 画单台车的掉线折线图(两个关键字参数：１是时间划分粒度，２是时段截取)
def drawDropLinechart(dropStaticsFile, w0DropFile, w1DropFile, minDropFile, srttDropFile, dropDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读入static.csv, drop.csv')
    staticsDf = pd.read_csv(dropStaticsFile, usecols=['start', 'end'], dtype={'start':int, 'end':int})
    w0DropDf = pd.read_csv(w0DropFile, usecols=['curTimestamp'], dtype={'curTimestamp':int})
    w1DropDf = pd.read_csv(w1DropFile, usecols=['curTimestamp'], dtype={'curTimestamp':int})
    minDropDf = pd.read_csv(minDropFile, usecols=['curTimestamp'], dtype={'curTimestamp':int})
    srttDropDf = pd.read_csv(srttDropFile, usecols=['curTimestamp'], dtype={'curTimestamp':int})
    #####################################################
    #####################################################
    print('构造以小时为粒度的掉线次数折线图数据')
    sHour, eHour = int(staticsDf['start'].min() / 3600), int(staticsDf['end'].min() / 3600)
    
    w0DropDf['hour'] = w0DropDf.apply(lambda row : int(row['curTimestamp'] / 3600), axis=1)
    w0DropHour = w0DropDf.groupby('hour').size().to_frame('count') \
        .reindex(index=range(sHour, eHour), fill_value=0)

    w1DropDf['hour'] = w1DropDf.apply(lambda row : int(row['curTimestamp'] / 3600), axis=1)
    w1DropHour = w1DropDf.groupby('hour').size().to_frame('count') \
        .reindex(index=range(sHour, eHour), fill_value=0)

    minDropDf['hour'] = minDropDf.apply(lambda row : int(row['curTimestamp'] / 3600), axis=1)
    minDropHour = minDropDf.groupby('hour').size().to_frame('count') \
        .reindex(index=range(sHour, eHour), fill_value=0)

    srttDropDf['hour'] = srttDropDf.apply(lambda row : int(row['curTimestamp'] / 3600), axis=1)
    srttDropHour = srttDropDf.groupby('hour').size().to_frame('count') \
        .reindex(index=range(sHour, eHour), fill_value=0)
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将关键统计数据写入文件**********')
    #####################################################
    print('将掉线折线图数据写入文件')
    w0DropHour.merge(w1DropHour, on='hour') \
              .merge(minDropHour, on='hour') \
              .merge(srttDropHour, on='hour') \
              .to_csv(os.path.join(dropDir, '掉线折线图统计数据.csv'))
    #####################################################
    print('**********第二阶段结束**********')
    ###############################################################################


    #####################################################
    print('画两次抵消第一次设置长宽比不生效的bug')
    print('构造折线图x轴日期刻度')
    xticks = [i for i in range(sHour, eHour+1, 24)]
    xlabels = [time.strftime('%d日%H时', time.localtime(i * 3600)) for i in xticks]
    #####################################################
    #####################################################
    print('画图前的初始化：设置标题、坐标轴')
    plt.title('掉线折线图')

    plt.xlim([sHour, eHour])
    plt.xticks(xticks, xlabels)

    print('设置图片长宽比，结合dpi确定图片大小')
    plt.rcParams['figure.figsize'] = (12.8, 4.8)    
    #####################################################
    #####################################################
    print("画wlan0掉线折线图")
    lineW0, = plt.plot(list(w0DropHour.index), list(w0DropHour['count']), c='red')
    #####################################################
    #####################################################
    print("设置标注")
    plt.legend([lineW0],
            ['wlan0单网络'],
            loc='lower right')
    #####################################################
    #####################################################
    figName = os.path.join(dropDir, '掉线折线图.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################


    ###############################################################################
    print('**********第三阶段：画掉线折线图**********')
    #####################################################
    print('构造折线图x轴日期刻度')
    xticks = [i for i in range(sHour, eHour+1, 24)]
    xlabels = [time.strftime('%d日%H时', time.localtime(i * 3600)) for i in xticks]
    #####################################################
    #####################################################
    print('画图前的初始化：设置标题、坐标轴')
    plt.title('掉线折线图')

    plt.xlim([sHour, eHour])
    plt.xticks(xticks, xlabels)

    plt.ylabel('掉线次数')

    print('设置图片长宽比，结合dpi确定图片大小')
    plt.rcParams['figure.figsize'] = (12.8, 4.8)    
    #####################################################
    #####################################################
    print("画wlan0掉线折线图")
    lineW0, = plt.plot(list(w0DropHour.index), list(w0DropHour['count']), c='blue')
    #####################################################
    #####################################################
    print("画wlan1掉线折线图")
    lineW1, = plt.plot(list(w1DropHour.index), list(w1DropHour['count']), c='green')
    #####################################################
    #####################################################
    print("画双网络理论掉线折线图")
    lineMin, = plt.plot(list(minDropHour.index), list(minDropHour['count']), c='yellow')
    #####################################################
    #####################################################
    print("画双网络+mptcp实际掉线折线图")
    lineSrtt, = plt.plot(list(srttDropHour.index), list(srttDropHour['count']), c='red')
    #####################################################
    #####################################################
    print("设置标注")
    plt.legend([lineW0, lineW1, lineMin, lineSrtt],
            ['wlan0单网络', 
             'wlan1单网络', 
             '双网络理论', 
             '双网络+mptcp实际'],
            loc='upper right')
    #####################################################
    #####################################################
    figName = os.path.join(dropDir, '掉线折线图.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第三阶段结束**********')
    ###############################################################################



# 探究网络漫游与网络掉线的关系
def exploreHoAndDrop(w0HoCsvFile, w1HoCsvFile, w0DropCsvFile, w1DropCsvFile, dropDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读入漫游时段汇总.csv')
    w0HoDf = pd.read_csv(w0HoCsvFile, usecols=['start', 'end', 'duration', 'rtt1', 'rtt2'], 
                                    dtype={'start':int, 'end':int, 'duration':int, 'rtt1':int, 'rtt2':int})
    w1HoDf = pd.read_csv(w1HoCsvFile, usecols=['start', 'end', 'duration', 'rtt1', 'rtt2'], 
                                    dtype={'start':int, 'end':int, 'duration':int, 'rtt1':int, 'rtt2':int})
    #####################################################
    #####################################################
    print('读入单网络掉线时刻.csv')
    w0DropDf = pd.read_csv(w0DropCsvFile, usecols=['curTimestamp'], 
                                    dtype={'curTimestamp':int})
    w1DropDf = pd.read_csv(w1DropCsvFile, usecols=['curTimestamp'], 
                                    dtype={'curTimestamp':int})
    #####################################################
    #####################################################
    print('探究漫游与无线网络业务掉线的关系')
    # 这里实现的不太好，通过apply实现了两层循环：外层以掉线事件迭代，内层以漫游事件迭代，比较掉线事件时间戳与漫游影响时延时段
    def isHo(dropDfRow, hoDf):
        for _, hoDfRow in hoDf.iterrows():
            if dropDfRow['curTimestamp'] * 1e3 > hoDfRow['rttBreakTimestamp'] \
                    and dropDfRow['curTimestamp'] * 1e3 < hoDfRow['rttRecoverTimestamp']:
                return hoDfRow['start']
        return np.nan

    w0HoDf['rttBreakTimestamp'] = w0HoDf.apply(lambda row : row['start'] - row['rtt1'], axis=1)
    w0HoDf['rttRecoverTimestamp'] = w0HoDf.apply(lambda row : row['end'] + row['rtt2'], axis=1)
    w0DropDf['isHo'] = w0DropDf.apply(isHo, args=(w0HoDf,), axis=1)
    w0HoAndDropDf = w0DropDf.dropna()

    w1HoDf['rttBreakTimestamp'] = w1HoDf.apply(lambda row : row['start'] - row['rtt1'], axis=1)
    w1HoDf['rttRecoverTimestamp'] = w1HoDf.apply(lambda row : row['end'] + row['rtt2'], axis=1)
    w1DropDf['isHo'] = w1DropDf.apply(isHo, args=(w1HoDf,), axis=1)
    w1HoAndDropDf = w1DropDf.dropna()
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将关键统计数据写入文件**********')
    #####################################################
    print('将漫游与无线网络业务掉线的关系数据写入文件')
    w0HoAndDropDf.to_csv(os.path.join(dropDir, 'w0HoAndDrop.csv'))
    w1HoAndDropDf.to_csv(os.path.join(dropDir, 'w1HoAndDrop.csv'))
    #####################################################
    print('**********第二阶段结束**********')
    ###############################################################################



# 探究mptcp掉线与agv停车的关系
def exploreMptcpDropAndAgvSuspend(csvFile, notifyCsvFile, dropDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读入notification日志信息与全部数据')
    notifyDf = pd.read_csv(notifyCsvFile)
    df = pd.read_csv(csvFile, usecols=['curTimestamp', 'srtt'])
    #####################################################
    #####################################################
    print('探究mptcp掉线与agv停车的关系')
    notifyDf['srtt'] = notifyDf.apply(lambda row : df[(df['curTimestamp'] >= row['timestamp'] - 5) & 
                                                  (df['curTimestamp'] <= row['timestamp'] + 5)].srtt.max(), axis=1)
    # 截取并丢弃notification日志时间轴超出df的部分停车数据
    notifyDf = notifyDf.dropna()
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将关键统计数据写入文件**********')
    #####################################################
    print('将mptcp掉线与agv停车的关系数据写入文件')
    notifyDf.to_csv(os.path.join(dropDir, 'agvStopAndMptcpDrop.csv'))
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
    print('**********掉线分析->第一阶段：单车数据统计**********')
    #####################################################
    for i in range(1, 42):
        fileName = '30.113.151.' + str(i)
        print(fileName)
        csvPath = os.path.join(r'/home/cx/Desktop/sdb-dir/tmp', fileName)
        csvFile = os.path.join(csvPath, 'data.csv')
        if os.path.isdir(csvPath):
            print("掉线分析")
            dropDir = os.path.join(csvPath, 'analysisDrop')
            if not os.path.isdir(dropDir):
                os.makedirs(dropDir)

            print('单车数据的掉线热力图')
            drawDrop([csvFile], dropDir)

            print('单车数据的掉线次数折线图')
            dropStaticsFile = os.path.join(dropDir, 'statics.csv')
            w0DropFile = os.path.join(dropDir, 'wlan0单网络掉线时刻.csv')
            w1DropFile = os.path.join(dropDir, 'wlan1单网络掉线时刻.csv')
            minDropFile = os.path.join(dropDir, '双网络理论掉线时刻.csv')
            srttDropFile = os.path.join(dropDir, '双网络+mptcp实际掉线时刻.csv')
            
            drawDropLinechart(dropStaticsFile, w0DropFile, w1DropFile, minDropFile, srttDropFile, dropDir)

            print('探究漫游与掉线的关系')
            w0HoCsvFile = os.path.join(csvPath, 'analysisHandover/WLAN0漫游时段汇总.csv')
            w1HoCsvFile = os.path.join(csvPath, 'analysisHandover/WLAN1漫游时段汇总.csv')

            exploreHoAndDrop(w0HoCsvFile, w1HoCsvFile, w0DropFile, w1DropFile, dropDir)

            print('探究mptcp掉线与agv停车的关系')
            notifyCsvFile = os.path.join(csvPath, 'notification.csv')
            exploreMptcpDropAndAgvSuspend(csvFile, notifyCsvFile, dropDir)
    #####################################################
    print('**********掉线分析->第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********掉线分析->第二阶段：所有车数据统计**********')
    #####################################################
    print('构造文件夹')
    topTmpPath = r'/home/cx/Desktop/sdb-dir/tmp'
    topDataPath = r'/home/cx/Desktop/sdb-dir/'
    # csvFile与scanCsvFile按顺序一一对应
    csvFileList = [os.path.join(os.path.join(topTmpPath, path), 'data.csv') 
                   for path in os.listdir(topTmpPath)
                   if os.path.isfile(os.path.join(os.path.join(topTmpPath, path), 'data.csv'))]
    #####################################################
    #####################################################
    print("掉线分析")
    dropDir = os.path.join(topDataPath, 'analysisDrop')
    if not os.path.isdir(dropDir):
        os.makedirs(dropDir)

    print('所有车数据的掉线热力图')
    drawDrop(csvFileList, dropDir)
    #####################################################
    print('**********掉线分析->第二阶段结束**********')
    ###############################################################################