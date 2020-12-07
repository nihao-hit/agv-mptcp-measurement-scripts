# drawDrop : 画单台车或所有车的掉线热力图
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
    w0DropDf = dfAll[(dfAll['W0pingrtt'] == 30000)]
    w0DropDf['date'] = w0DropDf.apply(lambda row : datetime.datetime.fromtimestamp(row['curTimestamp']), axis=1)

    w1DropDf = dfAll[(dfAll['W1pingrtt'] == 30000)]
    w1DropDf['date'] = w1DropDf.apply(lambda row : datetime.datetime.fromtimestamp(row['curTimestamp']), axis=1)

    minDropDf = dfAll[(dfAll['minPingRtt'] == 30000)]
    minDropDf['date'] = minDropDf.apply(lambda row : datetime.datetime.fromtimestamp(row['curTimestamp']), axis=1)

    srttDropDf = dfAll[(dfAll['srtt'] == 30000)]
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
    w0DropMap = w0DropDf[['curPosX', 'curPosY']][(w0DropDf['curPosX'] != 0) | (w0DropDf['curPosX'] != 0)].reset_index(drop=True) \
        .groupby(['curPosX', 'curPosY']).size().to_frame('count').reset_index() \
        .pivot(index='curPosY', columns='curPosX', values='count').fillna(0).astype(int)
    w0DropMap.index = w0DropMap.index.astype(int)
    w0DropMap.columns = w0DropMap.columns.astype(int)
    w0DropMap = w0DropMap.reindex(index=range(139), columns=range(265), fill_value=0).values

    w1DropMap = w1DropDf[['curPosX', 'curPosY']][(w1DropDf['curPosX'] != 0) | (w1DropDf['curPosX'] != 0)].reset_index(drop=True) \
        .groupby(['curPosX', 'curPosY']).size().to_frame('count').reset_index() \
        .pivot(index='curPosY', columns='curPosX', values='count').fillna(0).astype(int)
    w1DropMap.index = w1DropMap.index.astype(int)
    w1DropMap.columns = w1DropMap.columns.astype(int)
    w1DropMap = w1DropMap.reindex(index=range(139), columns=range(265), fill_value=0).values

    minDropMap = minDropDf[['curPosX', 'curPosY']][(minDropDf['curPosX'] != 0) | (minDropDf['curPosX'] != 0)].reset_index(drop=True) \
        .groupby(['curPosX', 'curPosY']).size().to_frame('count').reset_index() \
        .pivot(index='curPosY', columns='curPosX', values='count').fillna(0).astype(int)
    minDropMap.index = minDropMap.index.astype(int)
    minDropMap.columns = minDropMap.columns.astype(int)
    minDropMap = minDropMap.reindex(index=range(139), columns=range(265), fill_value=0).values

    srttDropMap = srttDropDf[['curPosX', 'curPosY']][(srttDropDf['curPosX'] != 0) | (srttDropDf['curPosX'] != 0)].reset_index(drop=True) \
        .groupby(['curPosX', 'curPosY']).size().to_frame('count').reset_index() \
        .pivot(index='curPosY', columns='curPosX', values='count').fillna(0).astype(int)
    srttDropMap.index = srttDropMap.index.astype(int)
    srttDropMap.columns = srttDropMap.columns.astype(int)
    srttDropMap = srttDropMap.reindex(index=range(139), columns=range(265), fill_value=0).values
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