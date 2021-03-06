# drawDelayScatter : 画时延散点图
# drawCDFAndBar : 画时延CDF图，时延分类柱状图
from matplotlib import pyplot as plt 
import seaborn as sns
import numpy as np
import pandas as pd 
import time
import os



# 画时延散点图
def drawDelayScatter(csvFile, delayDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读取单台车的data.csv数据，构造minPingRtt列')
    df = pd.read_csv(csvFile, na_filter=False, usecols=['curTimestamp', 
                                                        'W0pingrtt', 'W1pingrtt', 'srtt',
                                                        'src'],
                              dtype={'curTimestamp' : int, 
                                     'W0pingrtt': int, 
                                     'W1pingrtt': int,
                                     'srtt' : int,
                                     'src' : str})
    # print(df.describe())
    df['minPingRtt'] = df.apply(lambda x: min(x['W0pingrtt'], x['W1pingrtt']), axis=1)
    df['minPingRttSrc'] = df.apply(lambda x : '151' if x['W0pingrtt'] < x['W1pingrtt'] 
                                                             else '127', axis=1)
    #####################################################
    #####################################################
    print('过滤W0pingrtt, W1pingrtt, minPingRtt, srtt填充数据')
    w0PingRttFiltered = df[(df['W0pingrtt'] % 1000 != 0)][['curTimestamp', 'W0pingrtt']]

    w1PingRttFiltered = df[(df['W1pingrtt'] % 1000 != 0)][['curTimestamp', 'W1pingrtt']]

    minPingRttFiltered = df[(df['minPingRtt'] % 1000 != 0)][['curTimestamp', 'minPingRtt', 'minPingRttSrc']]
    minPingRttFilteredW0 = minPingRttFiltered[minPingRttFiltered['minPingRttSrc'] == '151']
    minPingRttFilteredW1 = minPingRttFiltered[minPingRttFiltered['minPingRttSrc'] == '127']
    
    srttFiltered = df[(df['srtt'] % 1000 != 0)][['curTimestamp', 'srtt', 'src']]
    srttFilteredW0 = srttFiltered[srttFiltered.src.str.contains('151')]
    srttFilteredW1 = srttFiltered[srttFiltered.src.str.contains('127')]
    #####################################################
    #####################################################
    print('构造散点图x轴日期刻度与y轴时延刻度')
    # 将unix时间戳转换为日历时间
    # 30.113.151.1车采集数据时间最长，从8月5日到8月20日，共16天。一天86400秒
    sTime, eTime = df['curTimestamp'].min(), df['curTimestamp'].max()
    xticks = [i for i in range(sTime, eTime+1, 86400)]
    yticks = np.arange(0, 3001, 500)
    xlabels = [time.strftime('%d日%H时', time.localtime(i)) for i in xticks]
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
    statics['minPingRtt中属于w0总数'] = len(minPingRttFilteredW0)
    statics['minPingRtt中属于w1总数'] = len(minPingRttFilteredW1)
    statics['过滤后srtt总数'] = len(srttFiltered)
    statics['srtt中属于w0总数'] = len(srttFilteredW0)
    statics['srtt中属于w1总数'] = len(srttFilteredW1)

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
    fig, ((w0Ax), (w1Ax), (minAx), (srttAx)) = plt.subplots(4, 1, sharex='col', sharey='col')
    #####################################################
    print("画wlan0时延散点图")
    w0Ax.set_title('wlan0时延散点图')

    w0Ax.scatter(list(w0PingRttFiltered['curTimestamp']), list(w0PingRttFiltered['W0pingrtt']), 
                c='tab:blue', s=0.5, alpha=0.5)
    #####################################################
    #####################################################
    print("画wlan1时延散点图")
    w1Ax.set_title('wlan1时延散点图')

    w1Ax.scatter(list(w1PingRttFiltered['curTimestamp']), list(w1PingRttFiltered['W1pingrtt']), 
                c='tab:red', s=0.5, alpha=0.5)
    #####################################################
    #####################################################
    print("画双网络最低时延散点图")
    minAx.set_title('双网络最低时延散点图')

    minAx.scatter(list(minPingRttFilteredW0['curTimestamp']), list(minPingRttFilteredW0['minPingRtt']), 
                c='tab:blue', s=0.5, alpha=0.5)
    minAx.scatter(list(minPingRttFilteredW1['curTimestamp']), list(minPingRttFilteredW1['minPingRtt']), 
                c='tab:red', s=0.5, alpha=0.5)
    #####################################################
    #####################################################
    print("画mptcp时延散点图")
    srttAx.set_title('mptcp时延散点图')
    
    srttAx.set_xlim([sTime, eTime])
    srttAx.set_xticks(xticks)
    srttAx.set_xticklabels(xlabels, rotation=45)
    srttAx.set_xlabel('日期')
    
    srttAx.set_ylim([0, 3000])
    srttAx.set_yticks(yticks, ylabels)
    srttAx.set_ylabel('时延 (ms)')

    srttAx.scatter(list(srttFilteredW0['curTimestamp']), list(srttFilteredW0['srtt']), 
                c='tab:blue', s=0.5, alpha=0.5)
    srttAx.scatter(list(srttFilteredW1['curTimestamp']), list(srttFilteredW1['srtt']), 
                c='tab:red', s=0.5, alpha=0.5)
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



# 画时延CDF图，时延分类柱状图
def drawCDFAndBar(csvFileList, delayDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读入所有data.csv文件，并连接为一个df')
    dfList = []
    for csvFile in csvFileList:
        df = pd.read_csv(csvFile, usecols=['W0pingrtt', 'W1pingrtt', 'srtt', 'src'],
                                dtype={'W0pingrtt' : int, 
                                       'W1pingrtt' : int,
                                       'srtt' : int,
                                       'src': str})
        dfList.append(df)
    dfAll = pd.concat(dfList, ignore_index=True)

    dfAll['minPingRtt'] = dfAll.apply(lambda x : min(x['W0pingrtt'], x['W1pingrtt']), axis=1)
    #####################################################
    #####################################################
    print('过滤W0pingrtt, W1pingrtt, minPingRtt, srtt填充数据')
    w0PingRttFiltered = dfAll[(dfAll['W0pingrtt'] % 1000 != 0)]['W0pingrtt']
    w1PingRttFiltered = dfAll[(dfAll['W1pingrtt'] % 1000 != 0)]['W1pingrtt']
    minPingRttFiltered = dfAll[(dfAll['minPingRtt'] % 1000 != 0)]['minPingRtt']
    srttFiltered = dfAll[(dfAll['srtt'] % 1000 != 0)]['srtt']

    srttFilteredW0 = dfAll[(dfAll['srtt'] % 1000 != 0) & (dfAll.src.str.contains('151'))]['srtt']
    srttFilteredW1 = dfAll[(dfAll['srtt'] % 1000 != 0) & (dfAll.src.str.contains('127'))]['srtt']
    #####################################################
    #####################################################
    print('构造CDF数据')
    ratio = np.arange(0, 1.01, 0.01)
    w0RttRatio = w0PingRttFiltered.quantile(ratio)
    w1RttRatio = w1PingRttFiltered.quantile(ratio)
    minRttRatio = minPingRttFiltered.quantile(ratio)
    srttRatio = srttFiltered.quantile(ratio)

    w0SrttRatio = srttFilteredW0.quantile(ratio)
    w1SrttRatio = srttFilteredW1.quantile(ratio)
    #####################################################
    #####################################################
    print('2020/12/10:16: 构造分类柱状图数据')
    bins = [0, 200, sys.maxsize]
    labels = ['<200ms', '>=200ms']
    # 注意：这里计算柱状图数据占比时被除数是dfAll而不是.*Filtered
    # 因为时延>=200ms的分类不足1%，因此合并['200ms-1s', '1s-30s', '>=30s']，且增加'Non-Usable'分类．
    w0RttBarData = pd.cut(w0PingRttFiltered, bins=bins, labels=labels, right=False).value_counts().sort_index() / len(dfAll)
    w1RttBarData = pd.cut(w1PingRttFiltered, bins=bins, labels=labels, right=False).value_counts().sort_index() / len(dfAll)
    minRttBarData = pd.cut(minPingRttFiltered, bins=bins, labels=labels, right=False).value_counts().sort_index() / len(dfAll)
    srttBarData = pd.cut(srttFiltered, bins=bins, labels=labels, right=False).value_counts().sort_index() / len(dfAll)

    labels += ['Non-Usable']
    w0RttBarData = list(w0RttBarData) + [1 - sum(list(w0RttBarData))]
    w1RttBarData = list(w1RttBarData) + [1 - sum(list(w1RttBarData))]
    minRttBarData = list(minRttBarData) + [1 - sum(list(minRttBarData))]
    srttBarData = list(srttBarData) + [1 - sum(list(srttBarData))]
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
    statics['过滤后w0Srtt总数'] = len(srttFilteredW0)
    statics['过滤后w1Srtt总数'] = len(srttFilteredW1)
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将关键统计数据写入文件**********')
    print('将非图表型统计数据写入文件')
    pd.DataFrame(statics, index=[0]).to_csv(os.path.join(delayDir, 'statics.csv'))

    print('将cdf统计数据写入文件')
    pd.DataFrame({'w0PingRtt':list(w0RttRatio), 
                  'w1PingRtt':list(w1RttRatio), 
                  'minPingRtt':list(minRttRatio), 
                  'srtt':list(srttRatio),
                  'w0Srtt':list(w0SrttRatio),
                  'w1Srtt':list(w1SrttRatio)}).to_csv(os.path.join(delayDir, '时延cdf数据.csv'))
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
    plt.xscale('log')
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
    print("画w0Srtt的CDF图")
    cdfW0Srtt, = plt.plot(list(w0SrttRatio), list(w0SrttRatio.index), c='orange')
    #####################################################
    #####################################################
    print("画w0rtt与w1rtt最小值的CDF图")
    cdfminW0AndW1, = plt.plot(list(minRttRatio), list(minRttRatio.index), c='green')
    #####################################################
    #####################################################
    print("画w1rtt的CDF图")
    cdfW1pingrtt, = plt.plot(list(w1RttRatio), list(w1RttRatio.index), c='indigo')
    #####################################################
    #####################################################
    print("画w1Srtt的CDF图")
    cdfW1Srtt, = plt.plot(list(w1SrttRatio), list(w1SrttRatio.index), c='violet')
    #####################################################
    #####################################################
    print("设置标注")
    plt.legend([cdfW0pingrtt, cdfW0Srtt, cdfminW0AndW1, cdfW1pingrtt, cdfW1Srtt],
            ['wlan0PingRtt', 
             'wlan0Srtt',
             'minPingRtt', 
             'wlan1PingRtt', 
             'wlan1Srtt'],
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


    # 2020/12/10:16
    ###############################################################################
    print('**********第四阶段：画时延分类柱状图**********')
    #####################################################
    print("设置时延分类柱状图坐标轴")
    plt.title('时延分类柱状图')

    plt.xlabel('时延分类')
    plt.ylabel('比例')
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (6.4, 4.8)

    width = 0.2
    x = np.arange(len(w0RttBarData))

    plt.bar(x - 1.5 * width, w0RttBarData, width=width, label='wlan0时延')
    plt.bar(x - 0.5 * width, w1RttBarData, width=width, label='wlan1时延')
    plt.bar(x + 0.5 * width, minRttBarData, width=width, label='双网络最低时延')
    plt.bar(x + 1.5 * width, srttBarData, width=width, label='mptcp时延')
    plt.xticks(x, labels)

    # 显示数值
    for xi in range(len(x)):
        plt.text(x[xi] - 1.5 * width, w0RttBarData[xi], '{:.2f}'.format(w0RttBarData[xi]), ha='center', va= 'bottom')
        plt.text(x[xi] - 0.5 * width, w1RttBarData[xi], '{:.2f}'.format(w1RttBarData[xi]), ha='center', va= 'bottom')
        plt.text(x[xi] + 0.5 * width, minRttBarData[xi], '{:.2f}'.format(minRttBarData[xi]), ha='center', va= 'bottom')
        plt.text(x[xi] + 1.5 * width, srttBarData[xi], '{:.2f}'.format(srttBarData[xi]), ha='center', va= 'bottom')

    plt.legend()
    #####################################################
    #####################################################
    figName = os.path.join(delayDir, '时延分类柱状图.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第四阶段结束**********')
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
        st = time.time()
        
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

            print('单车数据的时延CDF图，时延分类柱状图')
            drawCDFAndBar([csvFile], delayDir)
        
        et = time.time()
        print('单车{}时延分析耗时{}s'.format(fileName, int(et - st)))
    #####################################################
    print('**********时延分析->第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********时延分析->第二阶段：所有车数据统计**********')
    #####################################################
    st = time.time()
    
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

    print('所有车数据的时延CDF图，时延分类柱状图')
    drawCDFAndBar(csvFileList, delayDir)

    et = time.time()
    print('所有车时延分析耗时{}s'.format(int(et - st)))
    #####################################################
    print('**********时延分析->第二阶段结束**********')
    ###############################################################################