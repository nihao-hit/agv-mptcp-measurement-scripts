# drawHandover : 画单台车的漫游热力图,漫游时长CDF,漫游时长分类柱状图,漫游类型分类柱状图,漫游SNR增益CDF
# drawHandoverFineGrained : 画漫游事件全景图，漫游事件SNR分析图　
from matplotlib import pyplot as plt 
import seaborn as sns
import numpy as np
import pandas as pd 
import time
import datetime
import os
import sys

# 画单台车的漫游热力图,漫游时长CDF,漫游时长分类柱状图,漫游类型分类柱状图,漫游SNR增益CDF
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
    dfAndConnDf = df.merge(connDf, on='curTimestamp', how='right')

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
    print('从dataframe统计漫游事件, 初始化数据结构')
    # ['start', 'end', 'duration', 'level1', 'level2', 'rtt1', 'rtt2', 'posX', 'posY', '0|1|2']
    # 0 : ap1->not-associated->ap2
    # 1 : ap1->not-associated->ap1
    # 2 : ap1->ap2
    w0HoList = []
    w0Ap1 = ''
    w0Ap1Idx = -1
    w0HoFlag = -1

    w1HoList = []
    w1Ap1 = ''
    w1Ap1Idx = -1
    w1HoFlag = -1

    # 补充数据结构，记录RTT采样时刻距离漫游时刻的距离
    w0RTTSampleTuple = []
    w1RTTSampleTuple = []
    #####################################################
    #####################################################
    print('提取漫游时段、漫游前后rtt与snr对比，构造dataframe')
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
                
                duration = curTimestamp[i] - curTimestamp[w0Ap1Idx]
                w0HoList.append([curTimestamp[w0Ap1Idx], curTimestamp[i], duration, 
                                 W0level[w0Ap1Idx], W0level[i], 
                                 beforeRtt, afterRtt,
                                 curPosX[w0Ap1Idx], curPosY[w0Ap1Idx],
                                 w0HoFlag])
        #####################################################
        # w0循环标志更新
                w0HoFlag = -1
            w0Ap1 = W0APMac[i]
            w0Ap1Idx = i
        if W0APMac[i] == 'Not-Associated':
            w0HoFlag = 0
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
                
                duration = curTimestamp[i] - curTimestamp[w1Ap1Idx]
                w1HoList.append([curTimestamp[w1Ap1Idx], curTimestamp[i], duration, 
                                 W1level[w1Ap1Idx], W1level[i], 
                                 beforeRtt, afterRtt,
                                 curPosX[w1Ap1Idx], curPosY[w1Ap1Idx],
                                 w1HoFlag])
        #####################################################
        # w1循环标志更新
                w1HoFlag = -1
            w1Ap1 = W1APMac[i]
            w1Ap1Idx = i
        if W1APMac[i] == 'Not-Associated':
            w1HoFlag = 0
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
    
    print('构造SNR增益列')
    w0HoDf['snrGain'] = w0HoDf['level2'] - w0HoDf['level1']
    w1HoDf['snrGain'] = w1HoDf['level2'] - w1HoDf['level1']
    #####################################################
    #####################################################
    print('构造漫游热力图数据')
    # w0HoMap = [[0]*265 for _ in range(139)]
    # w1HoMap = [[0]*265 for _ in range(139)]

    # １．提取坐标；２．过滤(0, 0)；３．重置索引
    # ４．按坐标分组；５．统计各坐标分组长度；６．生成新列count；７．重置索引；
    # ８．转换dataframe为二元数组坐标轴；９．将nan置为0；１０．转换dataframe为int；
    w0HoMap = w0HoDf[['posX', 'posY']][(w0HoDf['posX'] != 0) | (w0HoDf['posY'] != 0)].reset_index(drop=True) \
        .groupby(['posX', 'posY']).size().to_frame('count').reset_index() \
        .pivot(index='posY', columns='posX', values='count').fillna(0).astype(int).values
    
    w1HoMap = w1HoDf[['posX', 'posY']][(w1HoDf['posX'] != 0) | (w1HoDf['posY'] != 0)].reset_index(drop=True) \
        .groupby(['posX', 'posY']).size().to_frame('count').reset_index() \
        .pivot(index='posY', columns='posX', values='count').fillna(0).astype(int).values
    #####################################################
    ratio = np.arange(0, 1.01, 0.01)
    bins = [0, 200, 1000, 5000, sys.maxsize]
    labels = ['<=200ms', '200ms-1s', '1s-5s', '>5s']
    w0DurationCategory = dict(list(w0HoDf.groupby(pd.cut(w0HoDf['duration'], bins=bins, labels=labels).sort_index())))
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
    print('WLAN1因为数据缺失的问题没有研究意义')
    w0DurationTypeCategory = dict()
    for k, v in w0DurationCategory.items():
        tmp = dict()
        for k1, v1 in v.groupby('flag'):
            tmp[k1] = len(v1)
        w0DurationTypeCategory[k] = tmp
    #####################################################
    #####################################################
    print('构造After snr - Before snr的CDF数据')
    w0SNRRatio = (w0HoDf['level2'] - w0HoDf['level1']).quantile(ratio)
    w1SNRRatio = (w1HoDf['level2'] - w1HoDf['level1']).quantile(ratio)
    #####################################################
    #####################################################
    print('非图表型统计数据构造')
    statics = dict()
    for k, v in w0DurationCategory.items():
        tmp = dict()
        for k1, v1 in v.groupby('flag'):
            tmp[k1] = v1['snrGain'].describe()
        statics[k] = tmp
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
    #####################################################
    #####################################################
    print('将漫游SNR增益信息写入文件')
    w0SNRRatio.to_csv(os.path.join(tmpDir, 'WLAN0漫游SNR增益信息.csv'))
    w1SNRRatio.to_csv(os.path.join(tmpDir, 'WLAN1漫游SNR增益信息.csv'))
    #####################################################
    #####################################################
    print('将非图表型统计数据写入文件')
    pd.DataFrame(statics).to_csv(os.path.join(tmpDir, 'statics.csv'))
    #####################################################
    print('**********第二阶段结束**********')
    ###############################################################################

     
    #####################################################
    print("抵消第一个图长宽比不起作用的bug，画两次")
    plt.title('w0-handover-count')
    plt.xlim([0, 264])
    plt.ylim([0, 138])

    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 6.0)

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


    ###############################################################################
    print('**********第七阶段：画WLAN0与WLAN1漫游SNR增益CDF**********')
    #####################################################
    print("设置漫游SNR增益CDF坐标轴")
    plt.title('漫游SNR增益CDF')
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
    print("画WLAN0漫游SNR增益CDF")
    cdfW0HoSNR, = plt.plot(list(w0SNRRatio), list(w0SNRRatio.index), c='red')
    #####################################################
    #####################################################
    print("画WLAN1漫游SNR增益CDF")
    cdfW1HoSNR, = plt.plot(list(w1SNRRatio), list(w1SNRRatio.index), c='blue')
    #####################################################
    #####################################################
    print("设置标注")
    plt.legend([cdfW0HoSNR, cdfW1HoSNR],
            ['WLAN0', 
             'WLAN1'],
            loc='lower right')
    
    plt.savefig(os.path.join(tmpDir, '漫游SNR增益CDF.png'), dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第七阶段结束**********')
    ###############################################################################



# 画漫游事件全景图，漫游事件SNR分析图　
def drawHandoverFineGrained(w0HoCsvFile, w1HoCsvFile, csvFile, connCsvFile, tmpDir):
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
                                                        'W0pingrtt'],
                              dtype={'curTimestamp' : int, 
                                     'W0APMac' : str,
                                     'W0level' : int,
                                     'scanW0APMacMax' : str,
                                     'scanW0APLevelMax' : int,
                                     'W0pingrtt' : int})
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
    plt.rcParams['figure.figsize'] = (360.0, 4.8)
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
    plt.rcParams['figure.figsize'] = (360.0, 4.8)
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
    print('**********第三阶段：画漫游事件SNR与时延分析图**********')
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
        fileDir = os.path.join(tmpDir, durationLabel)
        if not os.path.isdir(fileDir):
            os.makedirs(fileDir)
        for _, ho in hoList.iterrows():
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
            # 对分析时段内的conn SNR数据再次按照AP分组，并过滤零值
            hoConnDf = oneW0HoDf[(oneW0HoDf['W0APMac'] != '') & (oneW0HoDf['W0level'] != 0)]
            hoConnApGroup = dict(list(hoConnDf.groupby('W0APMac', sort=False)))
            # 对分析时段内的scan SNR数据再次按照AP分组，并过滤零值
            hoScanDf = oneW0HoDf[(oneW0HoDf['scanW0APMacMax'] != '') & (oneW0HoDf['scanW0APLevelMax'] != 0)]
            hoScanApGroup = dict(list(hoScanDf.groupby('scanW0APMacMax', sort=False)))
            # 准备时延数据，并过滤零值
            hoRttDf = oneW0HoDf[oneW0HoDf['W0pingrtt'] % 1000 != 0]
            #####################################################
            #####################################################
            # 设置标题
            plt.title('漫游事件SNR与时延分析图')
            #####################################################
            #####################################################
            # 设置第一个坐标坐标轴
            plt.xlim([analysisStartTime, analysisEndTime])
            plt.xticks(list(oneW0HoDf['curTimestamp']), rotation=45)
            plt.xlabel('时间(s)')
            plt.ylabel('SNR(dBm)')
            # 为每个ap分配一种颜色
            colors = ['red', 'orange', 'green', 'blue', 'purple', 'black']
            colorsMap = dict()
            idx = 0
            for k in list(hoConnApGroup.keys()) + list(hoScanApGroup.keys()):
                if k not in colorsMap:
                    colorsMap[k] = idx
                    idx = (idx + 1) % len(colors)
            # 画conn　SNR折线图与scan SNR折线图
            for k, v in hoConnApGroup.items():
                plt.plot(list(v['curTimestamp']), list(v['W0level']), 
                        c=colors[colorsMap[k]], marker='+', ms=4, label='conn: ' + k)
            for k, v in hoScanApGroup.items():
                plt.plot(list(v['curTimestamp']), list(v['scanW0APLevelMax']), 
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
                width = int(innerHo['duration'] / 1000) if innerHo['duration'] >= 1000 else 1
                plt.axvline(int(innerHo['start'] / 1000), lw=width, color=c, label=label)
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