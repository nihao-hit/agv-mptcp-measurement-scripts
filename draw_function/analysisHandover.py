# drawHandover : 画单台车的WLAN0与WLAN1漫游热力图，漫游SNR对比CDF，漫游RTT对比CDF，漫游时长CDF
from matplotlib import pyplot as plt 
import seaborn as sns
import numpy as np
import pandas as pd 
import time
import os
import sys

# 画单台车的WLAN0与WLAN1漫游热力图，漫游SNR对比CDF，漫游RTT对比CDF，漫游时长CDF
def drawHandover(csvFile, tmpDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读取单台车的csv数据')
    df = pd.read_csv(csvFile, na_filter=False, usecols=['curTimestamp', 
                                                        'W0APMac', 'W1APMac', 
                                                        'curPosX', 'curPosY',
                                                        'W0pingrtt', 'W1pingrtt',
                                                        'W0level', 'W1level'],
                              dtype={'curTimestamp' : int, 
                                     'W0APMac' : str, 
                                     'W1APMac' : str,
                                     'curPosX' : int,
                                     'curPosY' : int,
                                     'W0pingrtt': int, 
                                     'W1pingrtt': int,
                                     'W0level': int,
                                     'W1level': int})
    # print(df.describe())
    curTimestamp = df['curTimestamp']
    curPosX = df['curPosX']
    curPosY = df['curPosY']
    W0APMac = df['W0APMac']
    W1APMac = df['W1APMac']
    W0pingrtt = df['W0pingrtt']
    W1pingrtt = df['W1pingrtt']
    W0level = df['W0level']
    W1level = df['W1level']
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
                beforeRtt = W0pingrtt[w0Ap1Idx]
                afterRtt = W0pingrtt[i]
                # 由于rtt存在滞后性，因此将rtt的选取向后推１－２ｓ．
                #　对于漫游前，选最大值；对于漫游后，选最小值
                for j in range(w0Ap1Idx + 1, min(i + 1, w0Ap1Idx + 3)):
                    if W0pingrtt[j] % 1000 != 0:
                        beforeRtt = max(beforeRtt, W0pingrtt[j])
                for j in range(i + 1, min(i + 3, len(curTimestamp))):
                    if W0pingrtt[j] % 1000 != 0:
                        afterRtt = min(afterRtt, W0pingrtt[j])
                
                duration = curTimestamp[i] - curTimestamp[w0Ap1Idx]
                w0HoList.append([curTimestamp[w0Ap1Idx], curTimestamp[i], duration, 
                                 W0level[w0Ap1Idx], W0level[i], 
                                 W0pingrtt[w0Ap1Idx], W0pingrtt[i],
                                 curPosX[w0Ap1Idx], curPosY[i],
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
                beforeRtt = W1pingrtt[w1Ap1Idx]
                afterRtt = W1pingrtt[i]
                # 由于rtt存在滞后性，因此将rtt的选取向后推１－２ｓ．
                #　对于漫游前，选最大值；对于漫游后，选最小值
                for j in range(w1Ap1Idx + 1, min(i + 1, w1Ap1Idx + 3)):
                    if W1pingrtt[j] % 1000 != 0:
                        beforeRtt = max(beforeRtt, W1pingrtt[j])
                for j in range(i + 1, min(i + 3, len(curTimestamp))):
                    if W1pingrtt[j] % 1000 != 0:
                        afterRtt = min(afterRtt, W1pingrtt[j])
                
                duration = curTimestamp[i] - curTimestamp[w1Ap1Idx]
                w1HoList.append([curTimestamp[w1Ap1Idx], curTimestamp[i], duration, 
                                 W1level[w1Ap1Idx], W1level[i], 
                                 W1pingrtt[w1Ap1Idx], W1pingrtt[i],
                                 curPosX[w1Ap1Idx], curPosY[i],
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
    print('构造After snr - Before snr的CDF数据')
    w0DurationRatio = w0HoDf['duration'].quantile(ratio)
    w1DurationRatio = w1HoDf['duration'].quantile(ratio)
    #####################################################
    #####################################################
    print('构造After snr - Before snr的CDF数据')
    w0SNRRatio = (w0HoDf['level2'] - w0HoDf['level1']).quantile(ratio)
    w1SNRRatio = (w1HoDf['level2'] - w1HoDf['level1']).quantile(ratio)
    #####################################################
    #####################################################
    print('构造Before rtt / After rtt的CDF数据')
    w0RTTRatio = (w0HoDf['rtt1'] / w0HoDf['rtt2']).quantile(ratio)
    w1RTTRatio = (w1HoDf['rtt1'] / w1HoDf['rtt2']).quantile(ratio)
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
    print('将漫游前RTT比漫游后RTT的CDF信息写入文件')
    w0RTTRatio.to_csv(os.path.join(tmpDir, 'WLAN0漫游前RTT比漫游后RTT的CDF信息.csv'))
    w1RTTRatio.to_csv(os.path.join(tmpDir, 'WLAN1漫游前RTT比漫游后RTT的CDF信息.csv'))
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

    plt.savefig(os.path.join(tmpDir, 'w0handover.png'), dpi=150)
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
    print('**********第四阶段：画WLAN0与WLAN1漫游SNR对比CDF，漫游RTT对比CDF，漫游时长CDF**********')
    #####################################################
    print("设置漫游时长CDF坐标轴")
    plt.title('漫游时长CDF')
    plt.xlim([1, 30])
    plt.xlabel('漫游时长(s)')

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
    print('**********第五阶段：画WLAN0与WLAN1漫游SNR对比CDF**********')
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
    print('**********第五阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第六阶段：画WLAN0与WLAN1漫游RTT对比CDF**********')
    #####################################################
    print("设置漫游RTT对比CDF坐标轴")
    plt.title('漫游RTT对比CDF')
    plt.xlim([1, 50])
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
    print('**********第六阶段结束**********')
    ###############################################################################