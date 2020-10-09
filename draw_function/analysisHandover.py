# drawHandover : 画单台车的WLAN0与WLAN1漫游热力图，漫游SNR对比CDF，漫游RTT对比CDF，漫游时长CDF
from matplotlib import pyplot as plt 
import seaborn as sns
import numpy as np
import pandas as pd 
import time
import os
import sys

# 画单台车的WLAN0与WLAN1漫游热力图，漫游SNR对比CDF，漫游RTT对比CDF，漫游时长CDF
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
    connDf.sort_values(by='timestamp', inplace=True).reset_index(drop=True)
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
    #####################################################
    print('构造漫游时长CDF数据')
    w0DurationRatio = w0HoDf['duration'].quantile(ratio)
    w1DurationRatio = w1HoDf['duration'].quantile(ratio)
    #####################################################
    #####################################################
    print('构造漫游时长柱状图数据')
    bins = [0, 200, 1000, 5000, sys.maxsize]
    labels = ['<=200ms', '200ms-1s', '1s-5s', '>5s']
    w0DurationBarData = pd.cut(w0HoDf['duration'], bins=bins, labels=labels).value_counts().sort_index() / len(w0HoDf)
    w1DurationBarData = pd.cut(w1HoDf['duration'], bins=bins, labels=labels).value_counts().sort_index() / len(w1HoDf)
    #####################################################
    #####################################################
    print('构造After snr - Before snr的CDF数据')
    w0SNRRatio = (w0HoDf['level2'] - w0HoDf['level1']).quantile(ratio)
    w1SNRRatio = (w1HoDf['level2'] - w1HoDf['level1']).quantile(ratio)
    #####################################################
    #####################################################
    print('构造After rtt / Before rtt的CDF数据')
    print('过滤掉sys.maxsize与-sys.maxsize-1，注意过滤数量．')
    w0HoRtt = w0HoDf[['start', 'rtt1', 'rtt2']].merge(pd.DataFrame(w0RTTSampleTuple, columns=['rtt1SampleTime', 'rtt2SampleTime']), left_index=True)
    w0HoRtt = w0HoRtt[(w0HoRtt['rtt1'] != -sys.maxsize - 1) & (w0HoRtt['rtt2'] != sys.maxsize)]
    w0RTTRatio = (w0HoRtt['rtt2'] / w0HoRtt['rtt1']).quantile(ratio)

    w1HoRtt = w1HoDf[['start', 'rtt1', 'rtt2']].merge(pd.DataFrame(w1RTTSampleTuple, columns=['rtt1SampleTime', 'rtt2SampleTime']), left_index=True)
    w1HoRtt = w1HoRtt[(w1HoRtt['rtt1'] != -sys.maxsize - 1) & (w1HoRtt['rtt2'] != sys.maxsize)]
    w1RTTRatio = (w1HoRtt['rtt2'] / w1HoRtt['rtt1']).quantile(ratio)
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将关键统计数据写入文件**********')
    #####################################################
    print('将漫游事件全部数据写入文件')
    w0HoDf.to_csv(os.path.join(tmpDir, 'WLAN0漫游统计信息.csv'))
    w1HoDf.to_csv(os.path.join(tmpDir, 'WLAN1漫游统计信息.csv'))
    #####################################################
    #####################################################
    print('将漫游时长CDF信息写入文件')
    w0DurationRatio.to_csv(os.path.join(tmpDir, 'WLAN0漫游时长CDF信息.csv'))
    w1DurationRatio.to_csv(os.path.join(tmpDir, 'WLAN1漫游时长CDF信息.csv'))
    #####################################################
    #####################################################
    print('将漫游SNR增益信息写入文件')
    w0SNRRatio.to_csv(os.path.join(tmpDir, 'WLAN0漫游SNR增益信息.csv'))
    w1SNRRatio.to_csv(os.path.join(tmpDir, 'WLAN1漫游SNR增益信息.csv'))
    #####################################################
    #####################################################
    print('将漫游后RTT比漫游前RTT的CDF信息写入文件')
    w0RTTRatio.to_csv(os.path.join(tmpDir, 'WLAN0漫游前RTT比漫游后RTT的CDF信息.csv'))
    w1RTTRatio.to_csv(os.path.join(tmpDir, 'WLAN1漫游前RTT比漫游后RTT的CDF信息.csv'))

    print('将过滤后漫游前后RTT采样信息写入文件')
    w0HoRtt.to_csv(os.path.join(tmpDir, '过滤后WLAN0漫游前后RTT采样信息.csv'))
    w1HoRtt.to_csv(os.path.join(tmpDir, '过滤后WLAN1漫游前后RTT采样信息.csv'))
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
    plt.rcParams['figure.figsize'] = (11.0, 6.0)
    # 每个刻度5次漫游
    cbarMaxTick = max(list(map(max, w0HoMap)))
    ax = sns.heatmap(w0HoMap, cmap="Blues", vmin=0, 
                     cbar_kws={'ticks': range(0, cbarMaxTick+5, 5)})
    # 逆置Y轴
    ax.invert_yaxis()

    plt.savefig(os.path.join(tmpDir, 'WLAN0漫游热力图.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    #####################################################
    print("画WLAN1漫游热力图")
    plt.title('WLAN１漫游热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 6.0)
    # 每个刻度5次漫游
    cbarMaxTick = max(list(map(max, w1HoMap)))
    ax = sns.heatmap(w1HoMap, cmap="Blues", vmin=0, 
                     cbar_kws={'ticks': range(0, cbarMaxTick+5, 5)})
    # 逆置Y轴
    ax.invert_yaxis()

    plt.savefig(os.path.join(tmpDir, 'WLAN１漫游热力图.png'), dpi=150)
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
    plt.xlabel('漫游时长(ms)')

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
            loc='lower right')
    
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

    width = 0.3
    x = np.arange(len(w0DurationBarData))

    plt.bar(x, list(w0DurationBarData), width=width, label='WLAN0', tick_label=labels)
    plt.bar(x + width, list(w1DurationBarData), width=width, label='WLAN1')
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
    print('**********第六阶段：画WLAN0与WLAN1漫游SNR对比CDF**********')
    #####################################################
    print("设置漫游SNR对比CDF坐标轴")
    plt.title('漫游SNR对比CDF')
    # plt.xlim([-10, 10])
    plt.xlabel('漫游增益(dBm)')

    plt.ylim([0, 1])
    # range不能迭代float
    # TypeError: 'float' object cannot be interpreted as an integer
    plt.yticks([i for i in np.arange(0.0, 1.1, 0.1)])
    #####################################################
    #####################################################
    print("画WLAN0漫游SNR对比CDF")
    cdfW0HoSNR, = plt.plot(list(w0SNRRatio), list(w0SNRRatio.index), c='red')
    #####################################################
    #####################################################
    print("画WLAN1漫游SNR对比CDF")
    cdfW1HoSNR, = plt.plot(list(w1SNRRatio), list(w1SNRRatio.index), c='blue')
    #####################################################
    #####################################################
    print("设置标注")
    plt.legend([cdfW0HoSNR, cdfW1HoSNR],
            ['WLAN0', 
             'WLAN1'],
            loc='lower right')
    
    plt.savefig(os.path.join(tmpDir, '漫游SNR对比CDF.png'), dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第六阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第七阶段：画WLAN0与WLAN1漫游RTT对比CDF**********')
    #####################################################
    print("设置漫游RTT对比CDF坐标轴")
    plt.title('漫游RTT对比CDF')
    plt.xlim([0, 50])
    plt.xlabel('漫游前RTT / 漫游后RTT')
    # plt.xticks([0, 1, 5, 10, 20, 30, 50],
    #            ['0', '1', '5', '10', '20', '30', '50'])

    plt.ylim([0, 1])
    # range不能迭代float
    # TypeError: 'float' object cannot be interpreted as an integer
    plt.yticks([i for i in np.arange(0.0, 1.1, 0.1)])
    #####################################################
    #####################################################
    print("画WLAN0漫游RTT对比CDF")
    cdfW0HoRTT, = plt.plot(list(w0RTTRatio), list(w0RTTRatio.index), c='red')
    #####################################################
    #####################################################
    print("画WLAN1漫游RTT对比CDF")
    cdfW1HoRTT, = plt.plot(list(w1RTTRatio), list(w1RTTRatio.index), c='blue')
    #####################################################
    #####################################################
    print("设置标注")
    plt.legend([cdfW0HoRTT, cdfW1HoRTT],
            ['WLAN0', 
             'WLAN1'],
            loc='lower right')
    
    plt.savefig(os.path.join(tmpDir, '漫游RTT对比CDF.png'), dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第七阶段结束**********')
    ###############################################################################



# # 提取漫游时长各分类的时段，画SNR, 传输层时延，序列号，速度的散点图　
# def drawHandoverFineGrained(w0HoCsvFile, w1HoCsvFile, connCsvFile, tcpprobeCsvFile, tmpDir):
#     ###############################################################################
#     print('**********第一阶段：准备数据**********')
#     #####################################################
#     print('读取单台车的WLAN0漫游统计信息.csv文件')
#     w0HoDf = pd.read_csv(w0HoCsvFile, na_filter=False, usecols=['start', 'end', 'duration'],
#                               dtype={'start' : int, 
#                                      'end' : int,
#                                      'duration' : int})

#     print('读取单台车的WLAN1漫游统计信息.csv文件')
#     w1HoDf = pd.read_csv(w1HoCsvFile, na_filter=False, usecols=['start', 'end', 'duration'],
#                               dtype={'start' : int, 
#                                      'end' : int,
#                                      'duration' : int})               
#     #####################################################
#     #####################################################
#     print('读取单台车的connData.csv数据')
#     print('由于从scan文件提取的conn数据没有顺序，因此这里必须按时间戳排序')
#     connDf = pd.read_csv(connCsvFile, na_filter=False, usecols=['timestamp', 
#                                                             'W0APMac', 'W0level',
#                                                             'W1APMac', 'W1level'],
#                               dtype={'timestamp' : int, 
#                                      'W0APMac' : str,
#                                      'W0level': int, 
#                                      'W1APMac' : str,
#                                      'W1level': int,})
#     connDf.sort_values(by='timestamp', inplace=True).reset_index(drop=True)
#     # print(connDf.describe())
#     #####################################################
#     #####################################################
#     print('读取单台车的tcpprobeData.csv数据')
#     tcpprobeDf = pd.read_csv(tcpprobeCsvFile, na_filter=False, usecols=['timestamp', 
#                                                             'W0APMac', 'W0level',
#                                                             'W1APMac', 'W1level'],
#                               dtype={'timestamp' : int, 
#                                      'W0APMac' : str,
#                                      'W0level': int, 
#                                      'W1APMac' : str,
#                                      'W1level': int,})
#     #####################################################
#     #####################################################
#     print('按漫游时长各分类提取时段数据')
#     bins = [0, 200, 1000, 5000, sys.maxsize]
#     labels = ['<=200ms', '200ms-1s', '1s-5s', '>5s']
#     w0HoGroup = list(w0HoDf.groupby(pd.cut(w0HoDf['duration'], bins=bins, labels=labels).sort_index()))
#     for category, w0HoCategory in w0HoGroup:
#         print(category)
#         fileDir = os.path.join(tmpDir, category)
#         if not os.path.isdir(fileDir):
#             os.makedirs(fileDir)
#         for _, oneW0Ho in w0HoCategory.iterrows():
#             connDf['bin'] = pd.cut(connDf['timestamp'], [oneW0Ho['start'], oneW0Ho['end']])
#             oneW0HoconnDf = list(connDf.groupby('bin'))[0][1]
#             if 0 not in list(oneW0HoconnDf['W0level']):
#                 plt.scatter(list(oneW0HoconnDf['timestamp']), list(oneW0HoconnDf['W0level']), c='red', s=0.2, label='WLAN0')
#                 plt.savefig(os.path.join(fileDir, 'WLAN0-{}.png'.format(list(oneW0Ho[['start', 'end']]))), dpi=200)
#     #####################################################
#     print('**********第一阶段结束**********')
#     ###############################################################################