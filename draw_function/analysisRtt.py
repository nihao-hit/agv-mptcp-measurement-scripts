# drawDelayScatter : w0rtt，w1rtt，w0rtt与w1rtt最小值，srtt随时间分布散点图
# drawCDF : 画w0rtt、w1rtt、w0rtt与w1rtt最小值、srtt的CDF图
from matplotlib import pyplot as plt 
import seaborn as sns
import numpy as np
import pandas as pd 
import time
import os

# 画w0rtt，w1rtt，w0rtt与w1rtt最小值，srtt随时间分布散点图
def drawDelayScatter(csvFile, delayDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读取单台车的data.csv数据，构造minPingRtt列')
    df = pd.read_csv(csvFile, na_filter=False, usecols=['curTimestamp', 
                                                        'W0pingrtt', 'W1pingrtt', 'srtt'],
                              dtype={'curTimestamp' : int, 
                                     'W0pingrtt': int, 
                                     'W1pingrtt': int,
                                     'srtt' : int})
    # print(df.describe())
    df['minPingRtt'] = df.apply(lambda x: min(x['W0pingrtt'], x['W1pingrtt']), axis=1)
    #####################################################
    #####################################################
    print('过滤W0pingrtt, W1pingrtt, minPingRtt, srtt填充数据')
    w0PingRttFiltered = df[(df['W0pingrtt'] % 1000 != 0)]
    w1PingRttFiltered = df[(df['W1pingrtt'] % 1000 != 0)]
    minPingRttFiltered = df[(df['minPingRtt'] % 1000 != 0)]
    srttFiltered = df[(df['srtt'] % 1000 != 0)]
    #####################################################
    #####################################################
    print('构造散点图x轴日期刻度与y轴时延刻度')
    # 将unix时间戳转换为日历时间
    # 30.113.151.1车采集数据时间最长，从8月5日到8月20日，共16天。一天86400秒
    sTime, eTime = df['curTimestamp'].min(), df['curTimestamp'].max()
    xticks = [i for i in range(sTime, eTime+1, 86400)]
    yticks = np.arange(0, 3001, 500)
    xlabels = [time.strftime('%m月%d日%H时', time.localtime(i)) for i in xticks]
    ylabels = ['0', '0.5s', '1s', '1.5s', '2s', '2.5s', '3s']
    #####################################################
    #####################################################
    print('非图表型统计数据构造')
    staticsFile = os.path.join(delayDir, 'statics.csv')
    statics = dict()
    if os.path.isfile(staticsFile):
        statics = pd.read_csv(staticsFile).to_dict('list')

    # 数据总数，时间跨度，时间粒度
    statics['过滤后w0PingRtt总数'] = len(w0PingRttFiltered)
    statics['过滤后w1PingRtt总数'] = len(w1PingRttFiltered)
    statics['过滤后minPingRtt总数'] = len(minPingRttFiltered)
    statics['过滤后srtt总数'] = len(srttFiltered)

    statics['start'] = df['curTimestamp'].min()
    statics['end'] = df['curTimestamp'].max()
    statics['duration'] = statics['end'] - statics['start']
    statics['时间戳粒度'] = '秒'
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将关键统计数据写入文件**********')
    #####################################################
    print('将非图表型统计数据写入文件')
    pd.DataFrame(statics, index=[0]).to_csv(os.path.join(delayDir, 'statics.csv'))
    #####################################################
    print('**********第二阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第三阶段：画时延散点图**********')
    #####################################################
    fig, ((w0Ax), (w1Ax), (minAx), (srttAx)) = plt.subplots(1, 4, sharex='col')
    w0Ax.set_xlim([sTime, eTime])
    w0Ax.set_xticks(xticks)
    w0Ax.set_xticklabels(xlabels, rotation=45)
    w0Ax.set_xlabel('日期')
    #####################################################
    print("画wlan0时延散点图")
    w0Ax.set_title('wlan0时延散点图')
    
    w0Ax.set_ylim([0, 3])
    w0Ax.set_yticks(yticks, ylabels)
    w0Ax.set_ylabel('时延')

    w0Ax.scatter(list(w0PingRttFiltered['curTimestamp']), list(w0PingRttFiltered['W0pingrtt']), 
                s=1, alpha=0.1)
    #####################################################
    #####################################################
    print("画wlan1时延散点图")
    w1Ax.set_title('wlan1时延散点图')
    
    w1Ax.set_ylim([0, 3])
    w1Ax.set_yticks(yticks, ylabels)
    w1Ax.set_ylabel('时延')

    w1Ax.scatter(list(w1PingRttFiltered['curTimestamp']), list(w1PingRttFiltered['W1pingrtt']), 
                s=1, alpha=0.1)
    #####################################################
    #####################################################
    print("画双网络最低时延散点图")
    minAx.set_title('双网络最低时延散点图')
    
    minAx.set_ylim([0, 3])
    minAx.set_yticks(yticks, ylabels)
    minAx.set_ylabel('时延')

    minAx.scatter(list(minPingRttFiltered['curTimestamp']), list(minPingRttFiltered['minPingRtt']), 
                s=1, alpha=0.1)
    #####################################################
    #####################################################
    print("画mptcp时延散点图")
    srttAx.set_title('mptcp时延散点图')
    
    srttAx.set_ylim([0, 3])
    srttAx.set_yticks(yticks, ylabels)
    srttAx.set_ylabel('时延')

    srttAx.scatter(list(srttFiltered['curTimestamp']), list(srttFiltered['srtt']), 
                s=1, alpha=0.1)
    #####################################################
    #####################################################
    # # 设置图片长宽比，结合dpi确定图片大小
    # # 将12.0改为len(xticks)/2
    # plt.rcParams['figure.figsize'] = (len(xticks)/2, 4.8)

    # 调整图像避免截断xlabel
    plt.tight_layout()

    plt.savefig(os.path.join(delayDir, '时延散点图.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第三阶段结束**********')
    ###############################################################################



# 画w0rtt、w1rtt、w0rtt与w1rtt最小值、srtt的CDF图
def drawCDF(csvFileList, delayDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读入所有data.csv文件，并连接为一个df')
    dfList = []
    for csvFile in csvFileList:
        df = pd.read_csv(csvFile, usecols=['W0pingrtt', 'W1pingrtt', 'srtt'],
                                  dtype={'W0pingrtt' : int, 
                                         'W1pingrtt' : int,
                                         'srtt' : int})
        dfList.append(df)
    dfAll = pd.concat(dfList, ignore_index=True)
    dfAll['minPingRtt'] = dfAll.apply(lambda x : min(x['W0pingrtt'], x['W1pingrtt']), axis=1)
    #####################################################
    #####################################################
    print('过滤W0pingrtt, W1pingrtt, minPingRtt, srtt填充数据')
    w0PingRttFiltered = dfAll[(dfAll['W0pingrtt'] % 1000 != 0)]
    w1PingRttFiltered = dfAll[(dfAll['W1pingrtt'] % 1000 != 0)]
    minPingRttFiltered = dfAll[(dfAll['minPingRtt'] % 1000 != 0)]
    srttFiltered = dfAll[(dfAll['srtt'] % 1000 != 0)]
    #####################################################
    #####################################################
    print('构造CDF数据')
    ratio = np.arange(0, 1.01, 0.01)
    w0RttRatio = w0PingRttFiltered.quantile(ratio)
    w1RttRatio = w1PingRttFiltered.quantile(ratio)
    minRttRatio = minPingRttFiltered.quantile(ratio)
    srttRatio = srttFiltered.quantile(ratio)
    #####################################################
    #####################################################
    print('非图表型统计数据构造')
    staticsFile = os.path.join(delayDir, 'statics.csv')
    statics = dict()
    if os.path.isfile(staticsFile):
        statics = pd.read_csv(staticsFile).to_dict('list')

    # 数据总数，时间跨度，时间粒度
    statics['过滤后w0PingRtt总数'] = len(w0PingRttFiltered)
    statics['过滤后w1PingRtt总数'] = len(w1PingRttFiltered)
    statics['过滤后minPingRtt总数'] = len(minPingRttFiltered)
    statics['过滤后srtt总数'] = len(srttFiltered)
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将关键统计数据写入文件**********')
    print('将非图表型统计数据写入文件')
    pd.DataFrame(statics, index=[0]).to_csv(os.path.join(delayDir, 'statics.csv'))

    print('将cdf统计数据写入文件')
    pd.DataFrame({'w0PingRtt':w0RttRatio, 
                  'w1PingRtt':w1RttRatio, 
                  'minPingRtt':minRttRatio, 
                  'srtt':srttRatio}).to_csv(os.path.join(delayDir, '时延cdf数据.csv'))
    print('**********第二阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第三阶段：画时延CDF图**********')
    #####################################################
    print('画CDF图前的初始化：设置标题、坐标轴')
    plt.title('时延CDF图')

    # plt.xlim([0, 200])
    plt.ylim([0, 1])

    plt.xlabel('时延 (ms)')
    # plt.xticks([0, 10, 20, 50, 100, 200],
    #            ['0', '10ms', '20ms', '50ms', '100ms', '200ms'])
    plt.yticks(np.arange(0, 1.1, 0.1))
    #####################################################
    #####################################################
    print("画w0rtt的CDF图")
    # 如果不加','，报错
    # UserWarning: Legend does not support [<matplotlib.lines.Line2D object at 0x00000266279B1D08>] instances.
    # A proxy artist may be used instead.
    # See: http://matplotlib.org/users/legend_guide.html#creating-artists-specifically-for-adding-to-the-legend-aka-proxy-artists
    # loc='lower right')
    cdfW0pingrtt, = plt.plot(list(w0RttRatio), list(w0RttRatio.index), c='red')
    #####################################################
    #####################################################
    print("画w1rtt的CDF图")
    cdfW1pingrtt, = plt.plot(list(w1RttRatio), list(w1RttRatio.index), c='yellow')
    #####################################################
    #####################################################
    print("画w0rtt与w1rtt最小值的CDF图")
    cdfminW0AndW1, = plt.plot(list(minRttRatio), list(minRttRatio.index), c='blue')
    #####################################################
    #####################################################
    print("画srtt的CDF图")
    cdfsrtt, = plt.plot(list(srttRatio), list(srttRatio.index), c='green')
    #####################################################
    #####################################################
    print("设置标注")
    plt.legend([cdfW0pingrtt, cdfW1pingrtt, cdfminW0AndW1, cdfsrtt],
            ['wlan0时延', 
             'wlan1时延', 
             '双网络最低时延', 
             'mptcp时延'],
            loc='lower right')
    #####################################################
    #####################################################
    figName = os.path.join(delayDir, '时延CDF图.png')
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
    print('**********时延分析->第一阶段：单车数据统计**********')
    #####################################################
    for i in range(1, 42):
        fileName = '30.113.151.' + str(i)
        print(fileName)
        csvPath = os.path.join(r'/home/cx/Desktop/sdb-dir/tmp', fileName)
        csvFile = os.path.join(csvPath, 'data.csv')
        if os.path.isdir(csvPath):
            print("时延分析")
            delayDir = os.path.join(csvPath, 'analysisDelay')
            if not os.path.isdir(delayDir):
                os.makedirs(delayDir)

            print('单车数据的时延散点图')
            drawDelayScatter(csvFile, delayDir)

            print('单车数据的时延CDF图')
            drawCDF([csvFile], delayDir)
    #####################################################
    print('**********时延分析->第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********时延分析->第二阶段：所有车数据统计**********')
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
    print("时延分析")
    delayDir = os.path.join(topDataPath, 'analysisDelay')
    if not os.path.isdir(delayDir):
        os.makedirs(delayDir)

    print('所有车数据的时延CDF图')
    drawCDF(csvFileList, delayDir)
    #####################################################
    print('**********时延分析->第二阶段结束**********')
    ###############################################################################