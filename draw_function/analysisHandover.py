# drawHandover : 画单台车的漫游热力图,漫游时长CDF,漫游时长分类柱状图,漫游类型分类柱状图,漫游RSSI增益CDF
# drawHandoverFineGrained : 画漫游事件全景图，漫游事件RSSI分析图　
from matplotlib import pyplot as plt 
import seaborn as sns
import numpy as np
import pandas as pd 
import time
import datetime
import os
import sys

# 画单台车的漫游热力图,漫游时长CDF,漫游时长分类柱状图,漫游类型分类柱状图,漫游RSSI增益CDF
def drawHandover(csvFile, connCsvFile, tmpDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读取单台车的data.csv数据')
    df = pd.read_csv(csvFile, na_filter=False, usecols=['curTimestamp', 
                                                        'curPosX', 'curPosY',
                                                        'W0pingrtt', 'W1pingrtt'],
                              dtype={'curTimestamp' : int, 
                                     'curPosX' : int,
                                     'curPosY' : int,
                                     'W0pingrtt': int, 
                                     'W1pingrtt': int})
    # print(df.describe())
    #####################################################
    #####################################################
    print('读取单台车的connData.csv数据')
    print('由于从scan文件提取的conn数据没有顺序，因此这里必须按时间戳排序')
    connDf = pd.read_csv(connCsvFile, na_filter=False, usecols=['timestamp', 
                                                            'W0APMac', 'W0level',
                                                            'W1APMac', 'W1level'],
                              dtype={'timestamp' : int, 
                                     'W0APMac' : str,
                                     'W0level': int, 
                                     'W1APMac' : str,
                                     'W1level': int,})
    connDf.sort_values(by='timestamp', inplace=True)
    connDf.reset_index(drop=True, inplace=True)
    # print(connDf.describe())
    #####################################################
    #####################################################
    print('以时间戳为轴merge df与connDf，提取指定列数据')
    connDf['curTimestamp'] = (connDf['timestamp'] / 1e3).astype(int)
    # 2020/11/25:10: how参数从right改为inner，舍弃connDf时间轴先于和后于df的那部分数据
    dfAndConnDf = df.merge(connDf, on='curTimestamp', how='inner')

    curTimestamp = dfAndConnDf['timestamp']
    curPosX = dfAndConnDf['curPosX']
    curPosY = dfAndConnDf['curPosY']
    W0APMac = dfAndConnDf['W0APMac']
    W1APMac = dfAndConnDf['W1APMac']
    W0pingrtt = dfAndConnDf['W0pingrtt']
    W1pingrtt = dfAndConnDf['W1pingrtt']
    W0level = dfAndConnDf['W0level']
    W1level = dfAndConnDf['W1level']
    #####################################################
    #####################################################
    print('2020/11/25:10: 修改漫游时长为not-associated->ap2时段（flag=0, 1）或ap1->ap2时段（flag=2）')
    print('从dataframe统计漫游事件, 初始化数据结构')
    # ['start', 'end', 'duration', 'level1', 'level2', 'rtt1', 'rtt2', 'posX', 'posY', '0|1|2']
    # 0 : ap1->not-associated->ap2
    # 1 : ap1->not-associated->ap1
    # 2 : ap1->ap2
    w0HoList = []
    w0Ap1 = ''
    w0Ap1Idx = -1
    w0NotIdx = -1
    w0HoFlag = -1

    w1HoList = []
    w1Ap1 = ''
    w1Ap1Idx = -1
    w1NotIdx = -1
    w1HoFlag = -1

    # 补充数据结构，记录RTT采样时刻距离漫游时刻的距离
    w0RTTSampleTuple = []
    w1RTTSampleTuple = []
    #####################################################
    #####################################################
    print('提取漫游时段、漫游前后rtt与RSSI对比，构造dataframe')
    for i in range(len(curTimestamp)):
        #####################################################
        # w0漫游事件统计
        if W0APMac[i] != '' and W0APMac[i] != 'Not-Associated':
            #####################################################
            # 一次漫游事件统计
            if w0Ap1 != '' and (w0Ap1 != W0APMac[i] or w0HoFlag != -1):
                if w0Ap1 != W0APMac[i] and w0HoFlag != -1:
                    w0HoFlag = 0
                elif w0Ap1 == W0APMac[i] and w0HoFlag != -1:
                    w0HoFlag = 1
                else:
                    w0HoFlag = 2
                beforeRtt = -sys.maxsize - 1
                afterRtt = sys.maxsize
                w0RTTSample = [1, 1]

                # 由于rtt存在滞后性，因此将rtt的选取向后推1-3ｓ．
                # 对于漫游前，选最大值；对于漫游后，选最小值
                for j in range(w0Ap1Idx + 1, min(i + 1, w0Ap1Idx + 4)):
                    if W0pingrtt[j] % 1000 != 0 and W0pingrtt[j] > beforeRtt:
                        beforeRtt = W0pingrtt[j]
                        w0RTTSample[0] = j - w0Ap1Idx
                for j in range(i + 1, min(i + 4, len(curTimestamp))):
                    if W0pingrtt[j] % 1000 != 0 and W0pingrtt[j] < afterRtt:
                        afterRtt = W0pingrtt[j]
                        w0RTTSample[1] = j - i
                w0RTTSampleTuple.append(w0RTTSample)
                
                # 再抽象一层，解决flag=2, ap1->ap2时w0NotIdx == -1的bug
                w0HoStartIdx = w0NotIdx
                if w0HoStartIdx == -1:
                    w0HoStartIdx = w0Ap1Idx

                duration = curTimestamp[i] - curTimestamp[w0HoStartIdx]
                w0HoList.append([curTimestamp[w0HoStartIdx], curTimestamp[i], duration, 
                                 W0level[w0Ap1Idx], W0level[i], 
                                 beforeRtt, afterRtt,
                                 curPosX[w0HoStartIdx], curPosY[w0HoStartIdx],
                                 w0HoFlag])
        #####################################################
        # w0循环标志更新
                w0HoFlag = -1
                w0NotIdx = -1
            w0Ap1 = W0APMac[i]
            w0Ap1Idx = i
        if W0APMac[i] == 'Not-Associated':
            w0HoFlag = 0
            w0NotIdx = i
        #####################################################
        # w1漫游事件统计
        if W1APMac[i] != '' and W1APMac[i] != 'Not-Associated':
            #####################################################
            # 一次漫游事件统计
            if w1Ap1 != '' and (w1Ap1 != W1APMac[i] or w1HoFlag != -1):
                if w1Ap1 != W1APMac[i] and w1HoFlag != -1:
                    w1HoFlag = 0
                elif w1Ap1 == W1APMac[i] and w1HoFlag != -1:
                    w1HoFlag = 1
                else:
                    w1HoFlag = 2
                beforeRtt = -sys.maxsize - 1
                afterRtt = sys.maxsize
                w1RTTSample = [1, 1]

                # 由于rtt存在滞后性，因此将rtt的选取向后推１－3ｓ．
                #　对于漫游前，选最大值；对于漫游后，选最小值
                for j in range(w1Ap1Idx + 1, min(i + 1, w1Ap1Idx + 4)):
                    if W1pingrtt[j] % 1000 != 0 and W1pingrtt[j] > beforeRtt:
                        beforeRtt = W1pingrtt[j]
                        w1RTTSample[0] = j - w1Ap1Idx
                for j in range(i + 1, min(i + 4, len(curTimestamp))):
                    if W1pingrtt[j] % 1000 != 0 and W1pingrtt[j] < afterRtt:
                        afterRtt = W1pingrtt[j]
                        w1RTTSample[1] = j - i
                w1RTTSampleTuple.append(w1RTTSample)
                
                # 再抽象一层，解决flag=2, ap1->ap2时w0NotIdx == -1的bug
                w1HoStartIdx = w1NotIdx
                if w1HoStartIdx == -1:
                    w1HoStartIdx = w1Ap1Idx
                
                duration = curTimestamp[i] - curTimestamp[w1HoStartIdx]
                w1HoList.append([curTimestamp[w1HoStartIdx], curTimestamp[i], duration, 
                                 W1level[w1Ap1Idx], W1level[i], 
                                 beforeRtt, afterRtt,
                                 curPosX[w1HoStartIdx], curPosY[w1HoStartIdx],
                                 w1HoFlag])
        #####################################################
        # w1循环标志更新
                w1HoFlag = -1
                w1NotIdx = -1
            w1Ap1 = W1APMac[i]
            w1Ap1Idx = i
        if W1APMac[i] == 'Not-Associated':
            w1HoFlag = 0
            w1NotIdx = i
    w0HoDf = pd.DataFrame(w0HoList, columns=['start', 'end', 'duration', 
                                             'level1', 'level2', 
                                             'rtt1', 'rtt2',
                                             'posX', 'posY', 
                                             'flag'])
    w1HoDf = pd.DataFrame(w1HoList, columns=['start', 'end', 'duration', 
                                             'level1', 'level2', 
                                             'rtt1', 'rtt2',
                                             'posX', 'posY', 
                                             'flag'])
    
    #####################################################
    #####################################################
    print('为了方便人眼观察，为UNIX时间戳列添加日期时间列')
    w0HoDf['startDate'] = w0HoDf.apply(lambda row : datetime.datetime.fromtimestamp(row['start'] / 1000), axis=1)
    w0HoDf['endDate'] = w0HoDf.apply(lambda row : datetime.datetime.fromtimestamp(row['end'] / 1000), axis=1)

    w1HoDf['startDate'] = w1HoDf.apply(lambda row : datetime.datetime.fromtimestamp(row['start'] / 1000), axis=1)
    w1HoDf['endDate'] = w1HoDf.apply(lambda row : datetime.datetime.fromtimestamp(row['end'] / 1000), axis=1)
    
    print('构造RSSI增益列')
    w0HoDf['rssiGain'] = w0HoDf['level2'] - w0HoDf['level1']
    w1HoDf['rssiGain'] = w1HoDf['level2'] - w1HoDf['level1']
    #####################################################
    #####################################################
    print('构造漫游热力图数据')
    # w0HoMap = [[0]*265 for _ in range(139)]
    # w1HoMap = [[0]*265 for _ in range(139)]

    # １．提取坐标；２．过滤(0, 0)；３．重置索引
    # ４．按坐标分组；５．统计各坐标分组长度；６．生成新列count；７．重置索引；
    # ８．转换dataframe为二元数组坐标轴；９．将nan置为0；
    # ９．将index也就是posY转换为int；
    # １０．将columns也就是posX转换为int;
    # １１．使用连续的posY, posX替换index, columns，并返回二元数组．
    w0HoMap = w0HoDf[['posX', 'posY']][(w0HoDf['posX'] != 0) | (w0HoDf['posY'] != 0)].reset_index(drop=True) \
        .groupby(['posX', 'posY']).size().to_frame('count').reset_index() \
        .pivot(index='posY', columns='posX', values='count').fillna(0).astype(int)
    w0HoMap.index = w0HoMap.index.astype(int)
    w0HoMap.columns = w0HoMap.columns.astype(int)
    w0HoMap = w0HoMap.reindex(index=range(139), columns=range(265), fill_value=0).values
    
    w1HoMap = w1HoDf[['posX', 'posY']][(w1HoDf['posX'] != 0) | (w1HoDf['posY'] != 0)].reset_index(drop=True) \
        .groupby(['posX', 'posY']).size().to_frame('count').reset_index() \
        .pivot(index='posY', columns='posX', values='count').fillna(0).astype(int)
    w1HoMap.index = w1HoMap.index.astype(int)
    w1HoMap.columns = w1HoMap.columns.astype(int)
    w1HoMap = w1HoMap.reindex(index=range(139), columns=range(265), fill_value=0).values
    #####################################################
    ratio = np.arange(0, 1.01, 0.01)
    bins = [0, 200, 1000, 5000, sys.maxsize]
    labels = ['<=200ms', '200ms-1s', '1s-5s', '>5s']
    w0DurationCategory = dict(list(w0HoDf.groupby(pd.cut(w0HoDf['duration'], bins=bins, labels=labels).sort_index())))
    w1DurationCategory = dict(list(w1HoDf.groupby(pd.cut(w1HoDf['duration'], bins=bins, labels=labels).sort_index())))
    #####################################################
    print('构造漫游时长CDF数据')
    w0DurationRatio = w0HoDf['duration'].quantile(ratio)
    w1DurationRatio = w1HoDf['duration'].quantile(ratio)
    #####################################################
    #####################################################
    print('构造漫游时长柱状图数据')
    w0DurationBarData = pd.cut(w0HoDf['duration'], bins=bins, labels=labels).value_counts().sort_index() / len(w0HoDf)
    w1DurationBarData = pd.cut(w1HoDf['duration'], bins=bins, labels=labels).value_counts().sort_index() / len(w1HoDf)
    #####################################################
    #####################################################
    print('构造WLAN0漫游时长分类，漫游类型柱状图数据')
    w0DurationTypeCategory = dict()
    for k, v in w0DurationCategory.items():
        tmp = dict()
        for k1, v1 in v.groupby('flag'):
            tmp[k1] = len(v1)
        w0DurationTypeCategory[k] = tmp
    #####################################################
    #####################################################
    print('2020/11/25:16: 构造WLAN1漫游时长分类，漫游类型柱状图数据')
    w1DurationTypeCategory = dict()
    for k, v in w1DurationCategory.items():
        tmp = dict()
        for k1, v1 in v.groupby('flag'):
            tmp[k1] = len(v1)
        w1DurationTypeCategory[k] = tmp
    #####################################################
    #####################################################
    print('构造After RSSI - Before RSSI的CDF数据')
    w0RSSIRatio = (w0HoDf['level2'] - w0HoDf['level1']).quantile(ratio)
    w1RSSIRatio = (w1HoDf['level2'] - w1HoDf['level1']).quantile(ratio)
    #####################################################
    #####################################################
    print('非图表型统计数据构造')
    staticsFile = os.path.join(tmpDir, 'statics.csv')
    statics = dict()
    if os.path.isfile(staticsFile):
        statics = pd.read_csv(staticsFile).to_dict('list')

    # 数据总数，时间跨度，时间粒度
    statics['WLAN0漫游次数'] = len(w0HoDf)
    w0TypeCategory = dict(list(w0HoDf.groupby('flag')))
    statics['WLAN0 flag=0漫游次数'] = len(w0TypeCategory[0])
    statics['WLAN0 flag=1漫游次数'] = len(w0TypeCategory[1])
    statics['WLAN0 flag=2漫游次数'] = len(w0TypeCategory[2])

    statics['WLAN1漫游次数'] = len(w1HoDf)
    w1TypeCategory = dict(list(w1HoDf.groupby('flag')))
    statics['WLAN1 flag=0漫游次数'] = len(w1TypeCategory[0])
    statics['WLAN1 flag=1漫游次数'] = len(w1TypeCategory[1])
    # 2020/11/19:10 可能没有flag=2的漫游类别
    try:
        statics['WLAN1 flag=2漫游次数'] = len(w1TypeCategory[2])
    except:
        pass
    statics['start'] = curTimestamp.min()
    statics['end'] = curTimestamp.max()
    statics['duration'] = statics['end'] - statics['start']
    statics['漫游时间戳粒度'] = '毫秒'
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将关键统计数据写入文件**********')
    #####################################################
    print('将漫游时段汇总写入文件')
    w0HoDf.to_csv(os.path.join(tmpDir, 'WLAN0漫游时段汇总.csv'))
    w1HoDf.to_csv(os.path.join(tmpDir, 'WLAN1漫游时段汇总.csv'))
    #####################################################
    #####################################################
    print('将漫游时长CDF信息写入文件')
    w0DurationRatio.to_csv(os.path.join(tmpDir, 'WLAN0漫游时长CDF信息.csv'))
    w1DurationRatio.to_csv(os.path.join(tmpDir, 'WLAN1漫游时长CDF信息.csv'))
    #####################################################
    #####################################################
    print('将WLAN0漫游类型分类信息写入文件')
    pd.DataFrame(w0DurationTypeCategory).to_csv(os.path.join(tmpDir, 'WLAN0漫游类型分类信息.csv'))

    print('2020/11/25:16: 将WLAN1漫游类型分类信息写入文件')
    pd.DataFrame(w1DurationTypeCategory).to_csv(os.path.join(tmpDir, 'WLAN1漫游类型分类信息.csv'))
    #####################################################
    #####################################################
    print('将漫游RSSI增益信息写入文件')
    w0RSSIRatio.to_csv(os.path.join(tmpDir, 'WLAN0漫游RSSI增益信息.csv'))
    w1RSSIRatio.to_csv(os.path.join(tmpDir, 'WLAN1漫游RSSI增益信息.csv'))
    #####################################################
    #####################################################
    print('将非图表型统计数据写入文件')
    pd.DataFrame(statics, index=[0]).to_csv(os.path.join(tmpDir, 'statics.csv'))
    #####################################################
    print('**********第二阶段结束**********')
    ###############################################################################

     
    #####################################################
    print("抵消第一个图长宽比不起作用的bug，画两次")
    plt.title('w0-handover-count')
    plt.xlim([0, 264])
    plt.ylim([0, 138])

    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)

    # 每个刻度1000次掉线
    cbarMaxTick = max(list(map(max, w0HoMap)))
    ax = sns.heatmap(w0HoMap, cmap="Blues", vmin=0, 
                     cbar_kws={'ticks': range(0, cbarMaxTick+1000, 1000)})

    # # 设置标题
    # ax.set_title('w0-ap-count')

    # 逆置Y轴
    ax.invert_yaxis()

    plt.pause(1)
    plt.close()
    plt.pause(1)
    #########################################################################


    ###############################################################################
    print('**********第三阶段：画WLAN0与WLAN1漫游热力图**********')
    #####################################################
    print("画WLAN0漫游热力图")
    plt.title('WLAN0漫游热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)
    # 每个刻度5次漫游
    cbarMaxTick = max(list(map(max, w0HoMap)))
    ax = sns.heatmap(w0HoMap, cmap="Blues", vmin=0, 
                     cbar_kws={'ticks': range(0, cbarMaxTick+5, 5), 'label' : '漫游次数'})
    plt.xlabel('坐标X轴')
    plt.ylabel('坐标Y轴')
    # 逆置Y轴
    ax.invert_yaxis()

    plt.savefig(os.path.join(tmpDir, 'WLAN0漫游热力图.png'), dpi=100)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    #####################################################
    print("画WLAN1漫游热力图")
    plt.title('WLAN1漫游热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)
    # 每个刻度5次漫游
    cbarMaxTick = max(list(map(max, w1HoMap)))
    ax = sns.heatmap(w1HoMap, cmap="Blues", vmin=0, 
                     cbar_kws={'ticks': range(0, cbarMaxTick+5, 5), 'label' : '漫游次数'})
    plt.xlabel('坐标X轴')
    plt.ylabel('坐标Y轴')
    # 逆置Y轴
    ax.invert_yaxis()

    plt.savefig(os.path.join(tmpDir, 'WLAN1漫游热力图.png'), dpi=100)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第三阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第四阶段：画WLAN0与WLAN1漫游时长CDF**********')
    #####################################################
    print("设置漫游时长CDF坐标轴")
    plt.title('漫游时长CDF')
    plt.xlim([0, 5000])
    plt.xticks([0, 200, 1000, 5000], ['0', '200ms', '1s', '5s'])
    plt.xlabel('漫游时长')
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (6.4, 4.8)
    plt.ylim([0, 1])
    # range不能迭代float
    # TypeError: 'float' object cannot be interpreted as an integer
    plt.yticks([i for i in np.arange(0.0, 1.1, 0.1)])
    #####################################################
    #####################################################
    print("画WLAN0漫游时长CDF")
    cdfW0HoDuration, = plt.plot(list(w0DurationRatio), list(w0DurationRatio.index), c='red')
    #####################################################
    #####################################################
    print("画WLAN1漫游时长CDF")
    cdfW1HoDuration, = plt.plot(list(w1DurationRatio), list(w1DurationRatio.index), c='blue')
    #####################################################
    #####################################################
    print("设置标注")
    plt.legend([cdfW0HoDuration, cdfW1HoDuration],
            ['WLAN0', 
            'WLAN1'],
            loc='upper right')

    plt.savefig(os.path.join(tmpDir, '漫游时长CDF.png'), dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第四阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第五阶段：画WLAN0与WLAN1漫游时长分类柱状图**********')
    #####################################################
    print("设置漫游时长分类柱状图坐标轴")
    plt.title('漫游时长分类柱状图')

    plt.xlabel('漫游时长分类')
    plt.ylabel('比例')
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (6.4, 4.8)

    width = 0.3
    x = np.arange(len(w0DurationBarData))

    plt.bar(x, list(w0DurationBarData), width=width, label='WLAN0', tick_label=labels)
    plt.bar(x + width, list(w1DurationBarData), width=width, label='WLAN1')
    plt.legend()
    #####################################################
    #####################################################
    figName = os.path.join(tmpDir, '漫游时长分类柱状图.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第五阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第六阶段：画WLAN0漫游类型分类柱状图**********')
    #####################################################
    print("设置WLAN0漫游类型分类柱状图坐标轴")
    plt.title('WLAN0漫游类型分类柱状图')

    plt.xlabel('漫游时长分类')
    plt.ylabel('漫游次数')
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (6.4, 4.8)

    flag0, flag1, flag2 = [], [], []
    for k, v in w0DurationTypeCategory.items():
        flag0.append(v.setdefault(0, 0))
        flag1.append(v.setdefault(1, 0))
        flag2.append(v.setdefault(2, 0))

    width = 0.3
    x = np.arange(len(labels)) - width / 2

    plt.bar(x, flag0, width=width, label='ap1->not-associated->ap2')
    plt.bar(x + width, flag1, width=width, label='ap1->not-associated->ap1', tick_label=labels)
    plt.bar(x + 2 * width, flag2, width=width, label='ap1->ap2')
    plt.legend()

    # 显示数值
    for xi in range(len(x)):
        plt.text(x[xi], flag0[xi] + 10, '{}'.format(flag0[xi]), ha='center', va= 'bottom')
        plt.text(x[xi] + width, flag1[xi] + 10, '{}'.format(flag1[xi]), ha='center', va= 'bottom')
        plt.text(x[xi] + 2 * width, flag2[xi] + 10, '{}'.format(flag2[xi]), ha='center', va= 'bottom')
    #####################################################
    #####################################################
    figName = os.path.join(tmpDir, 'WLAN0漫游类型分类柱状图.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第六阶段结束**********')
    ###############################################################################


    # 2020/11/25:16
    ###############################################################################
    print('**********第七阶段：画WLAN1漫游类型分类柱状图**********')
    #####################################################
    print("设置WLAN1漫游类型分类柱状图坐标轴")
    plt.title('WLAN1漫游类型分类柱状图')

    plt.xlabel('漫游时长分类')
    plt.ylabel('漫游次数')
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (6.4, 4.8)

    flag0, flag1, flag2 = [], [], []
    for k, v in w1DurationTypeCategory.items():
        flag0.append(v.setdefault(0, 0))
        flag1.append(v.setdefault(1, 0))
        flag2.append(v.setdefault(2, 0))

    width = 0.3
    x = np.arange(len(labels)) - width / 2

    plt.bar(x, flag0, width=width, label='ap1->not-associated->ap2')
    plt.bar(x + width, flag1, width=width, label='ap1->not-associated->ap1', tick_label=labels)
    plt.bar(x + 2 * width, flag2, width=width, label='ap1->ap2')
    plt.legend()

    # 显示数值
    for xi in range(len(x)):
        plt.text(x[xi], flag0[xi] + 10, '{}'.format(flag0[xi]), ha='center', va= 'bottom')
        plt.text(x[xi] + width, flag1[xi] + 10, '{}'.format(flag1[xi]), ha='center', va= 'bottom')
        plt.text(x[xi] + 2 * width, flag2[xi] + 10, '{}'.format(flag2[xi]), ha='center', va= 'bottom')
    #####################################################
    #####################################################
    figName = os.path.join(tmpDir, 'WLAN1漫游类型分类柱状图.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第七阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第八阶段：画WLAN0与WLAN1漫游RSSI增益CDF**********')
    #####################################################
    print("设置漫游RSSI增益CDF坐标轴")
    plt.title('漫游RSSI增益CDF')
    # plt.xlim([-10, 10])
    plt.xlabel('漫游增益(dBm)')
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (6.4, 4.8)

    plt.ylim([0, 1])
    # range不能迭代float
    # TypeError: 'float' object cannot be interpreted as an integer
    plt.yticks([i for i in np.arange(0.0, 1.1, 0.1)])
    #####################################################
    #####################################################
    print("画WLAN0漫游RSSI增益CDF")
    cdfW0HoRSSI, = plt.plot(list(w0RSSIRatio), list(w0RSSIRatio.index), c='red')
    #####################################################
    #####################################################
    print("画WLAN1漫游RSSI增益CDF")
    cdfW1HoRSSI, = plt.plot(list(w1RSSIRatio), list(w1RSSIRatio.index), c='blue')
    #####################################################
    #####################################################
    print("设置标注")
    plt.legend([cdfW0HoRSSI, cdfW1HoRSSI],
            ['WLAN0', 
             'WLAN1'],
            loc='lower right')
    
    plt.savefig(os.path.join(tmpDir, '漫游RSSI增益CDF.png'), dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第八阶段结束**********')
    ###############################################################################



# 画漫游事件全景图，漫游事件RSSI分析图　
def drawHandoverFineGrained(w0HoCsvFile, w1HoCsvFile, csvFile, connCsvFile, tmpDir, count):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
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
    #####################################################
    print('读取单台车的data.csv数据')
    df = pd.read_csv(csvFile, na_filter=False, usecols=['curTimestamp', 
                                                        'W0APMac', 'W0level',
                                                        'scanW0APMacMax', 'scanW0APLevelMax',
                                                        'W0pingrtt',
                                                        'W1APMac', 'W1level',
                                                        'scanW1APMacMax', 'scanW1APLevelMax',
                                                        'W1pingrtt'],
                              dtype={'curTimestamp' : int, 
                                     'W0APMac' : str,
                                     'W0level' : int,
                                     'scanW0APMacMax' : str,
                                     'scanW0APLevelMax' : int,
                                     'W0pingrtt' : int,
                                     'W1APMac' : str,
                                     'W1level' : int,
                                     'scanW1APMacMax' : str,
                                     'scanW1APLevelMax' : int,
                                     'W1pingrtt' : int})
    #####################################################
    #####################################################
    print('读取单台车的connData.csv数据')
    print('由于从scan文件提取的conn数据没有顺序，因此这里必须按时间戳排序')
    connDf = pd.read_csv(connCsvFile, na_filter=False, usecols=['timestamp', 
                                                                'W0APMac', 'W0level'],
                            dtype={'timestamp' : int, 
                                    'W0APMac' : str,
                                    'W0level': int})
    connDf = connDf.sort_values(by='timestamp').reset_index(drop=True)
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    #####################################################
    startTime = connDf.iloc[0]['timestamp']
    endTime = connDf.iloc[-1]['timestamp']
    # 设置标题
    plt.title('WLAN0漫游事件全景图')
    # 设置坐标轴
    xticks = [i for i in range(startTime, endTime + 1800 * 1000, 3600 * 1000)]
    xlabels = [time.strftime('%m月%d日%H时', time.localtime(i/1000)) for i in xticks]
    plt.xticks(xticks, xlabels, rotation=45)
    plt.yticks([0, 1])
    plt.xlim([startTime, endTime])
    plt.ylim([0, 1])
    plt.xlabel('日期')
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (180.0, 4.8)
    #　画图
    for i in range(len(w0HoDf)):
        plt.vlines(w0HoDf.iloc[i]['start'], 0, 1)
    # plt.legend()
    # # 调整图像避免截断xlabel
    # plt.tight_layout()
    # 保存图片
    plt.savefig(os.path.join(tmpDir, 'WLAN0漫游事件全景图.png'), dpi=100)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################


    ###############################################################################
    print('**********第二阶段：画漫游事件全景图**********')
    startTime = connDf.iloc[0]['timestamp']
    endTime = connDf.iloc[-1]['timestamp']
    #####################################################
    # 设置标题
    plt.title('WLAN0漫游事件全景图')
    # 设置坐标轴
    xticks = [i for i in range(startTime, endTime + 1800 * 1000, 3600 * 1000)]
    xlabels = [time.strftime('%m月%d日%H时', time.localtime(i/1000)) for i in xticks]
    plt.xticks(xticks, xlabels, rotation=45)
    plt.yticks([0, 1])
    plt.xlim([startTime, endTime])
    plt.ylim([0, 1])
    plt.xlabel('日期')
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (180.0, 4.8)
    #　画图
    for i in range(len(w0HoDf)):
    #     label = 'ap1->ap2'
    #     c = 'green'
    #     if w0HoDf.iloc[i]['flag'] == 0:
    #         label = 'ap1->not-associated->ap2'
    #         c = 'red'
    #     if w0HoDf.iloc[i]['flag'] == 1:
    #         label = 'ap1->not-associated->ap1'
    #         c = 'blue'
    #     plt.vlines(w0HoDf.iloc[i]['start'], 0, 1, colors=c, label=label)
        plt.vlines(w0HoDf.iloc[i]['start'], 0, 1)
    # plt.legend()
    # # 调整图像避免截断xlabel
    # plt.tight_layout()
    # 保存图片
    plt.savefig(os.path.join(tmpDir, 'WLAN0漫游事件全景图.png'), dpi=100)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    #####################################################
    # 设置标题
    plt.title('WLAN1漫游事件全景图')
    # 设置坐标轴
    xticks = [i for i in range(startTime, endTime + 1800 * 1000, 3600 * 1000)]
    xlabels = [time.strftime('%m月%d日%H时', time.localtime(i/1000)) for i in xticks]
    plt.xticks(xticks, xlabels, rotation=45)
    plt.yticks([0, 1])
    plt.xlim([startTime, endTime])
    plt.ylim([0, 1])
    plt.xlabel('日期')
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (180.0, 4.8)
    #　画图
    for i in range(len(w1HoDf)):
        plt.vlines(w1HoDf.iloc[i]['start'], 0, 1)
    # # 调整图像避免截断xlabel
    # plt.tight_layout()
    # 保存图片
    plt.savefig(os.path.join(tmpDir, 'WLAN1漫游事件全景图.png'), dpi=100)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第二阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第三阶段：画WLAN0漫游事件RSSI分析图**********')
    #####################################################
    print('按漫游时长各分类提取时段数据进行分析')
    bins = [0, 200, 1000, 5000, sys.maxsize]
    labels = ['<=200ms', '200ms-1s', '1s-5s', '>5s']
    w0HoDurationCategory = dict(list(w0HoDf.groupby(pd.cut(w0HoDf['duration'], bins=bins, labels=labels).sort_index())))
    #####################################################
    #####################################################
    print('设置图片长宽比，结合dpi确定图片大小')
    plt.rcParams['figure.figsize'] = (6.4, 4.8)
    #####################################################
    #####################################################
    for durationLabel, hoList in w0HoDurationCategory.items():
        print(durationLabel)
        # 2020/11/25:16: 配合进行修改
        fileDir = os.path.join(os.path.join(tmpDir, 'wlan0'), durationLabel)
        if not os.path.isdir(fileDir):
            os.makedirs(fileDir)
        innerCount = count
        for _, ho in hoList.iterrows():
            if innerCount == 0:
                break
            innerCount -= 1
            #####################################################
            # 提取分析时段为[漫游开始时刻-10s, 漫游结束时刻+10s]
            hoStartTime = int(ho['start'] / 1000)
            hoEndTime = int(ho['end'] / 1000)
            analysisStartTime = hoStartTime - 10
            analysisEndTime = hoEndTime + 10
            df['bin'] = pd.cut(df['curTimestamp'], [analysisStartTime, analysisEndTime])
            oneW0HoDf = list(df.groupby('bin'))[0][1]
            #####################################################
            #####################################################
            # 对分析时段内的conn RSSI数据再次按照AP分组，并过滤零值
            hoConnDf = oneW0HoDf[(oneW0HoDf['W0APMac'] != '') & (oneW0HoDf['W0level'] != 0)]
            hoConnApGroup = dict(list(hoConnDf.groupby('W0APMac', sort=False)))
            # 对分析时段内的scan RSSI数据再次按照AP分组，并过滤零值
            hoScanDf = oneW0HoDf[(oneW0HoDf['scanW0APMacMax'] != '') & (oneW0HoDf['scanW0APLevelMax'] != 0)]
            hoScanApGroup = dict(list(hoScanDf.groupby('scanW0APMacMax', sort=False)))
            # 准备时延数据，并过滤零值
            hoRttDf = oneW0HoDf[oneW0HoDf['W0pingrtt'] % 1000 != 0]
            #####################################################
            #####################################################
            # 设置标题
            plt.title('漫游RSSI分析图')
            #####################################################
            #####################################################
            # 设置第一个坐标坐标轴
            plt.xlim([analysisStartTime * 1e3, analysisEndTime * 1e3])
            plt.xticks(list(map(lambda x : x * 1e3, list(oneW0HoDf['curTimestamp']))), 
                       list(map(lambda x : str(x)[-2:], list(oneW0HoDf['curTimestamp']))),
                       rotation=45)
            plt.xlabel('时间(s)')
            plt.ylabel('RSSI(dBm)')
            # 为每个ap分配一种颜色
            colors = ['red', 'orange', 'green', 'blue', 'purple', 'black']
            colorsMap = dict()
            idx = 0
            for k in list(hoConnApGroup.keys()) + list(hoScanApGroup.keys()):
                if k not in colorsMap:
                    colorsMap[k] = idx
                    idx = (idx + 1) % len(colors)
            # 画conn　RSSI折线图与scan RSSI折线图
            for k, v in hoConnApGroup.items():
                plt.plot(list(map(lambda x : x * 1e3, list(v['curTimestamp']))), list(v['W0level']), 
                        c=colors[colorsMap[k]], marker='+', ms=4, label='conn: ' + k)
            for k, v in hoScanApGroup.items():
                plt.plot(list(map(lambda x : x * 1e3, list(v['curTimestamp']))), list(v['scanW0APLevelMax']), 
                        c=colors[colorsMap[k]], marker='x', ms=4, label='scan: ' + k)
            #####################################################
            #####################################################
            # 提取所有在此时段的漫游事件并画竖线
            innerHoList = w0HoDf[(w0HoDf['start'] >= analysisStartTime * 1000) & (w0HoDf['start'] <= analysisEndTime * 1000)]
            for _, innerHo in innerHoList.iterrows():
                label = 'ap1->ap2'
                c = 'green'
                if innerHo['flag'] == 0:
                    label = 'ap1->not-associated->ap2'
                    c = 'red'
                if innerHo['flag'] == 1:
                    label = 'ap1->not-associated->ap1'
                    c = 'blue'
                plt.axvspan(innerHo['start'], innerHo['end'], alpha=0.3, color=c, label=label)
            #####################################################
            # 显示标注
            plt.legend()
            # #####################################################
            # # 设置第二个坐标轴
            # ax2 = plt.twinx()
            # ax2.set_ylabel('时延(ms)')
            # ax2.plot(list(hoRttDf['curTimestamp']), list(hoRttDf['W0pingrtt']), c='purple', marker='|', ms=4, label='时延')
            # # 显示标注
            # ax2.legend()
            # #####################################################
            #####################################################
            # 保存图片
            plt.savefig(os.path.join(fileDir, '{}-{}.png'.format(analysisStartTime, analysisEndTime)), dpi=200)
            plt.pause(1)
            plt.close()
            plt.pause(1)
            #####################################################
    #####################################################
    print('**********第三阶段结束**********')
    ###############################################################################

    # 2020/11/25:16:
    ###############################################################################
    print('**********第四阶段：画WLAN1漫游事件RSSI分析图**********')
    #####################################################
    print('按漫游时长各分类提取时段数据进行分析')
    bins = [0, 200, 1000, 5000, sys.maxsize]
    labels = ['<=200ms', '200ms-1s', '1s-5s', '>5s']
    w1HoDurationCategory = dict(list(w1HoDf.groupby(pd.cut(w1HoDf['duration'], bins=bins, labels=labels).sort_index())))
    #####################################################
    #####################################################
    print('设置图片长宽比，结合dpi确定图片大小')
    plt.rcParams['figure.figsize'] = (6.4, 4.8)
    #####################################################
    #####################################################
    for durationLabel, hoList in w1HoDurationCategory.items():
        print(durationLabel)
        fileDir = os.path.join(os.path.join(tmpDir, 'wlan1'), durationLabel)
        if not os.path.isdir(fileDir):
            os.makedirs(fileDir)
        innerCount = count
        for _, ho in hoList.iterrows():
            if innerCount == 0:
                break
            innerCount -= 1
            #####################################################
            # 提取分析时段为[漫游开始时刻-10s, 漫游结束时刻+10s]
            hoStartTime = int(ho['start'] / 1000)
            hoEndTime = int(ho['end'] / 1000)
            analysisStartTime = hoStartTime - 10
            analysisEndTime = hoEndTime + 10
            df['bin'] = pd.cut(df['curTimestamp'], [analysisStartTime, analysisEndTime])
            oneW1HoDf = list(df.groupby('bin'))[0][1]
            #####################################################
            #####################################################
            # 对分析时段内的conn RSSI数据再次按照AP分组，并过滤零值
            hoConnDf = oneW1HoDf[(oneW1HoDf['W1APMac'] != '') & (oneW1HoDf['W1level'] != 0)]
            hoConnApGroup = dict(list(hoConnDf.groupby('W1APMac', sort=False)))
            # 对分析时段内的scan RSSI数据再次按照AP分组，并过滤零值
            hoScanDf = oneW1HoDf[(oneW1HoDf['scanW1APMacMax'] != '') & (oneW1HoDf['scanW1APLevelMax'] != 0)]
            hoScanApGroup = dict(list(hoScanDf.groupby('scanW1APMacMax', sort=False)))
            # 准备时延数据，并过滤零值
            hoRttDf = oneW1HoDf[oneW1HoDf['W1pingrtt'] % 1000 != 0]
            #####################################################
            #####################################################
            # 设置标题
            plt.title('漫游RSSI分析图')
            #####################################################
            #####################################################
            # 设置第一个坐标坐标轴
            plt.xlim([analysisStartTime * 1e3, analysisEndTime * 1e3])
            plt.xticks(list(map(lambda x : x * 1e3, list(oneW1HoDf['curTimestamp']))), 
                       list(map(lambda x : str(x)[-2:], list(oneW1HoDf['curTimestamp']))),
                       rotation=45)
            plt.xlabel('时间(s)')
            plt.ylabel('RSSI(dBm)')
            # 为每个ap分配一种颜色
            colors = ['red', 'orange', 'green', 'blue', 'purple', 'black']
            colorsMap = dict()
            idx = 0
            for k in list(hoConnApGroup.keys()) + list(hoScanApGroup.keys()):
                if k not in colorsMap:
                    colorsMap[k] = idx
                    idx = (idx + 1) % len(colors)
            # 画conn　RSSI折线图与scan RSSI折线图
            for k, v in hoConnApGroup.items():
                plt.plot(list(map(lambda x : x * 1e3, list(v['curTimestamp']))), list(v['W1level']), 
                        c=colors[colorsMap[k]], marker='+', ms=4, label='conn: ' + k)
            for k, v in hoScanApGroup.items():
                plt.plot(list(map(lambda x : x * 1e3, list(v['curTimestamp']))), list(v['scanW1APLevelMax']), 
                        c=colors[colorsMap[k]], marker='x', ms=4, label='scan: ' + k)
            #####################################################
            #####################################################
            # 提取所有在此时段的漫游事件并画竖线
            innerHoList = w1HoDf[(w1HoDf['start'] >= analysisStartTime * 1000) & (w1HoDf['start'] <= analysisEndTime * 1000)]
            for _, innerHo in innerHoList.iterrows():
                label = 'ap1->ap2'
                c = 'green'
                if innerHo['flag'] == 0:
                    label = 'ap1->not-associated->ap2'
                    c = 'red'
                if innerHo['flag'] == 1:
                    label = 'ap1->not-associated->ap1'
                    c = 'blue'
                plt.axvspan(innerHo['start'], innerHo['end'], alpha=0.3, color=c, label=label)
            #####################################################
            # 显示标注
            plt.legend()
            # #####################################################
            # # 设置第二个坐标轴
            # ax2 = plt.twinx()
            # ax2.set_ylabel('时延(ms)')
            # ax2.plot(list(hoRttDf['curTimestamp']), list(hoRttDf['W1pingrtt']), c='purple', marker='|', ms=4, label='时延')
            # # 显示标注
            # ax2.legend()
            # #####################################################
            #####################################################
            # 保存图片
            plt.savefig(os.path.join(fileDir, '{}-{}.png'.format(analysisStartTime, analysisEndTime)), dpi=200)
            plt.pause(1)
            plt.close()
            plt.pause(1)
            #####################################################
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
    print('**********漫游分析->第一阶段：单车数据统计**********')
    #####################################################
    for i in range(1, 42):
        fileName = '30.113.151.' + str(i)
        print(fileName)
        csvPath = os.path.join(r'/home/cx/Desktop/sdb-dir/tmp', fileName)
        csvFile = os.path.join(csvPath, 'data.csv')
        connCsvFile = os.path.join(csvPath, 'connData.csv')
        if os.path.isdir(csvPath):
            print("漫游分析")
            handoverDir = os.path.join(csvPath, 'analysisHandover')
            if not os.path.isdir(handoverDir):
                os.makedirs(handoverDir)
            
            print('画单台车的漫游热力图,漫游时长CDF,漫游时长分类柱状图,漫游类型分类柱状图,漫游RSSI增益CDF')
            drawHandover(csvFile, connCsvFile, handoverDir)

            print('画漫游事件全景图，漫游事件RSSI分析图　')
            w0HoCsvFile = os.path.join(handoverDir, 'WLAN0漫游时段汇总.csv')
            w1HoCsvFile = os.path.join(handoverDir, 'WLAN1漫游时段汇总.csv')
            count = 10
            drawHandoverFineGrained(w0HoCsvFile, w1HoCsvFile, csvFile, connCsvFile, handoverDir, count)
    #####################################################
    print('**********漫游分析->第一阶段结束**********')
    ###############################################################################