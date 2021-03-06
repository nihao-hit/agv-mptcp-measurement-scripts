# drawConnLevel : 画AGV连接基站的RSSI分布CDF，rssi与时延关系图
# drawNotConnLevel : 画AGV Not-Associated时扫描到的基站最大RSSI图
# drawApCover : 基站覆盖热力图，基站覆盖空白热力图，有效基站覆盖热力图，有效基站覆盖空白热力图
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
import numpy as np
import pandas as pd 
import time
import os
import re

# 时间戳精度为s
class ScanStatus:
    timestamp = 0
    # 在解析comm文件时赋值
    curPosX = 0
    curPosY = 0

    w0ApMac = []
    w0Channel = []
    w0Level = []

    w1ApMac = []
    w1Channel = []
    w1Level = []

    def __init__(self):
        self.timestamp = 0
        # 在解析comm文件时赋值
        self.posX = 0
        self.posY = 0

        self.w0ApMac = []
        self.w0Channel = []
        self.w0Level = []

        self.w1ApMac = []
        self.w1Channel = []
        self.w1Level = []
    
    def __setitem__(self, k, v):
        self.k = v

    def __getitem__(self, k):
        return getattr(self, k)

    def __str__(self):
        return str(self.__dict__)

    def keys(self):
        return [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]



# 画AGV连接基站的RSSI分布CDF，rssi与时延关系图
def drawConnLevel(csvFileList, tmpDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读入所有csv文件，并连接为一个dataframe')
    print('提取level, rtt, 坐标数据')
    dfList = []
    for csvFile in csvFileList:
        df = pd.read_csv(csvFile, na_filter=False, usecols=['curTimestamp', 
                            'W0level', 'W0pingrtt', 'W1level', 'W1pingrtt', 'speed'],
                                dtype={'curTimestamp' : int,
                                       'W0level' : int, 
                                       'W0pingrtt' : int,
                                       'W1level' : int,
                                       'W1pingrtt' : int,
                                       'speed' : float})
        dfList.append(df)
    dfAll = pd.concat(dfList, ignore_index=True)
    #####################################################
    #####################################################
    print('分离w0与w1的数据')
    ratio = np.arange(0, 1.01, 0.01)

    w0Df = dfAll.loc[:, ['W0level', 'speed', 'W0pingrtt']]

    w1Df = dfAll.loc[:, ['W1level', 'speed', 'W1pingrtt']]
    #####################################################
    #####################################################
    print('1.过滤level=0也就是除去数据空洞与未关联基站的时刻数据')
    print('2.过滤speed=0也就是车静止的时刻数据')
    print('2021/3/12: 过滤pingRtt % 1000 == 0的填充数据，避免测量脚本空洞影响')
    w0DfFiltered = w0Df[(w0Df['W0level'] != 0) 
                      & (w0Df['speed'] != 0.0) 
                      & (w0Df['W0pingrtt'] % 1000 != 0)].reset_index(drop=True)
    w0LevelRatio = w0DfFiltered['W0level'].quantile(ratio)
    
    w1DfFiltered = w1Df[(w1Df['W1level'] != 0) 
                      & (w1Df['speed'] != 0.0)
                      & (w1Df['W1pingrtt'] % 1000 != 0)].reset_index(drop=True)
    w1LevelRatio = w1DfFiltered['W1level'].quantile(ratio)
    #####################################################
    #####################################################
    print('2020/11/24:10: 构造rssi与时延关系图')
    print('在过滤后的数据中将pingrtt > 3s替换为3s')
    w0DfFiltered.loc[(w0DfFiltered['W0pingrtt'] > 3000), 'W0pingrtt'] = 3000
    
    w0x1 = range(w0DfFiltered['W0level'].min(), w0DfFiltered['W0level'].max() + 1)
    w0y1 = [list(w0DfFiltered[w0DfFiltered['W0level'] == ix]['W0pingrtt']) for ix in w0x1]
    w0y2 = list(map(lambda x : len(x) / len(w0DfFiltered), w0y1))

    w1DfFiltered.loc[(w1DfFiltered['W1pingrtt'] > 3000), 'W1pingrtt'] = 3000
    
    w1x1 = range(w1DfFiltered['W1level'].min(), w1DfFiltered['W1level'].max() + 1)
    w1y1 = [list(w1DfFiltered[w1DfFiltered['W1level'] == ix]['W1pingrtt']) for ix in w1x1]
    w1y2 = list(map(lambda x : len(x) / len(w1DfFiltered), w1y1))
    #####################################################
    #####################################################
    print('非图表型统计数据构造')
    staticsFile = os.path.join(tmpDir, 'statics.csv')
    statics = dict()
    if os.path.isfile(staticsFile):
        statics = pd.read_csv(staticsFile).to_dict('list')
        
    # 数据总数，时间跨度，时间粒度
    statics['连接基站的rssi数据总数'] = len(dfAll)
    statics['wlan0过滤level=0speed=0pingrtt%1000==0后数据总数'] = len(w0DfFiltered)
    statics['wlan1过滤level=0speed=0pingrtt%1000==0后数据总数'] = len(w1DfFiltered)
    statics['start'] = dfAll['curTimestamp'].min()
    statics['end'] = dfAll['curTimestamp'].max()
    statics['duration'] = statics['end'] - statics['start']
    statics['时间粒度'] = '秒'

    # 极值：关联基站的最小RSSI
    statics['WLAN0最小RSSI'] = w0DfFiltered['W0level'].min()
    statics['WLAN0最大RSSI'] = w0DfFiltered['W0level'].max()
    statics['WLAN1最小RSSI'] = w1DfFiltered['W1level'].min()
    statics['WLAN1最大RSSI'] = w1DfFiltered['W1level'].max()
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将关键统计数据写入文件**********')
    #####################################################
    w0LevelRatio.to_csv(os.path.join(tmpDir, 'WLAN0信号强度统计信息.csv'))
    # 2020/11/24:12: 配合进行改动
    pd.DataFrame({'rssi':w0x1, 'rtt':w0y2}).to_csv(os.path.join(tmpDir, 'WLAN0 rssi与时延关系统计信息.csv'))

    w1LevelRatio.to_csv(os.path.join(tmpDir, 'WLAN1信号强度统计信息.csv'))
    pd.DataFrame({'rssi':w1x1, 'rtt':w1y2}).to_csv(os.path.join(tmpDir, 'WLAN1 rssi与时延关系统计信息.csv'))

    pd.DataFrame(statics, index=[0]).to_csv(os.path.join(tmpDir, 'statics.csv'))
    #####################################################
    print('**********第二阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第三阶段：画无线网络的RSSI图**********')
    #####################################################
    print('设置图片长宽比，结合dpi确定图片大小')
    plt.rcParams['figure.figsize'] = (6.4, 4.8)
    
    print('画CDF图前的初始化：设置标题、坐标轴')
    plt.title('AGV连接基站的RSSI分布CDF图')

    plt.xlim([-110, -10])
    plt.xlabel('RSSI(dBm)')

    plt.ylim([0, 1])
    plt.ylabel('CDF')
    plt.yticks(np.arange(0, 1.1, 0.1))
    #####################################################
    #####################################################
    print("画WLAN0的RSSI图")
    cdfW0Level, = plt.plot(list(w0LevelRatio), list(w0LevelRatio.index), c='red')
    #####################################################
    #####################################################
    print("画WLAN1的RSSI图")
    cdfW1Level, = plt.plot(list(w1LevelRatio), list(w1LevelRatio.index), c='blue')
    #####################################################
    #####################################################
    print('标注25%, 50%, 75%值')
    vlinesLabels = {0.25:'25%', 0.5:'50%', 0.75:'75%'}
    for ymax in [0.25, 0.5, 0.75]:
        w0x = w0LevelRatio[ymax]
        w1x = w1LevelRatio[ymax]

        # plt.vlines(w0x, 0, ymax, colors=['red'], linestyles='dotted')
        plt.text(w0x, ymax, s='{}\n{}dBm'.format(vlinesLabels[ymax], str(int(w0x))))
        
        # plt.vlines(w1x, 0, ymax, colors=['red'], linestyles='dotted')
        plt.text(w1x, ymax, s='{}\n{}dBm'.format(vlinesLabels[ymax], str(int(w1x))))
    #####################################################
    #####################################################
    print("设置标注")
    plt.legend([cdfW0Level, cdfW1Level],
            ['WLAN0', 
             'WLAN1'],
            loc='lower right')
    #####################################################
    #####################################################
    figName = os.path.join(tmpDir, 'AGV连接基站的RSSI分布CDF图.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第三阶段结束**********')
    ###############################################################################


    # 2020/11/24:12: 配合进行添加
    ###############################################################################
    print('**********第四阶段：画rssi与时延关系图**********')
    #####################################################
    print('画wlan0基站rssi与时延关系图')
    plt.rcParams['figure.figsize'] = (12.8, 4.8)
    
    fig, ax1 = plt.subplots()
    plt.title('wlan0基站rssi与时延关系图')

    ax1.set_xlabel('rssi (dBm)')
    ax1.set_ylabel('时延 (ms)')
    ax1.boxplot(w0y1, positions=w0x1)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('百分比　(%)', color=color)  # we already handled the x-label with ax1
    ax2.plot(w0x1, w0y2, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    # 旋转共用x轴labels
    for xtick in ax1.get_xticklabels():
        xtick.set_rotation(45)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped

    figName = os.path.join(tmpDir, 'wlan0基站rssi与时延关系图.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    #####################################################
    print('画wlan1基站rssi与时延关系图')
    plt.rcParams['figure.figsize'] = (12.8, 4.8)
    
    fig, ax1 = plt.subplots()
    plt.title('wlan1基站rssi与时延关系图')

    ax1.set_xlabel('rssi (dBm)')
    ax1.set_ylabel('时延 (ms)')
    ax1.boxplot(w1y1, positions=w1x1)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('百分比　(%)', color=color)  # we already handled the x-label with ax1
    ax2.plot(w1x1, w1y2, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    # 旋转共用x轴labels
    for xtick in ax1.get_xticklabels():
        xtick.set_rotation(45)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped

    figName = os.path.join(tmpDir, 'wlan1基站rssi与时延关系图.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第四阶段结束**********')
    ###############################################################################



# 画AGV Not-Associated时扫描到的基站最大RSSI图
def drawNotConnLevel(csvFileList, connCsvFileList, tmpDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读入所有connData.csv文件，data.csv文件，并以second为轴进行联结．')
    print('提取level, rtt, 坐标数据')
    dfAndConnDfList = []
    for i in range(len(csvFileList)):
        df = pd.read_csv(csvFileList[i], na_filter=False, usecols=['curTimestamp',
                                        'scanW0APLevelMax', 'scanW1APLevelMax'],
                                dtype={'curTimestamp' : int, 
                                    'scanW0APLevelMax' : int,
                                    'scanW1APLevelMax' : int})
        connDf = pd.read_csv(connCsvFileList[i], na_filter=False, usecols=['timestamp', 
                                    'W0APMac', 'W1APMac'],
                                dtype={'timestamp' : int, 
                                    'W0APMac' : str,
                                    'W1APMac' : str})
        # connDf.sort_values(by='timestamp', inplace=True)
        # connDf.reset_index(drop=True, inplace=True)
        connDf['second'] = (connDf['timestamp'] / 1e6).astype(int)
        dfAndConnDf = df.merge(connDf, how='inner', left_on='curTimestamp', right_on='second')
        dfAndConnDfList.append(dfAndConnDf)
    dfAll = pd.concat(dfAndConnDfList, ignore_index=True)
    #####################################################
    #####################################################
    print('分离w0与w1的数据')
    ratio = np.arange(0, 1.01, 0.01)

    w0Df = dfAll.loc[:,['W0APMac', 'scanW0APLevelMax']]

    w1Df = dfAll.loc[:, ['W1APMac', 'scanW1APLevelMax']]
    #####################################################
    #####################################################
    print('保留apMac==Not-Associated且扫描基站最大level!=0也就是未连接基站的时间戳对应的数据，构造level的CDF数据')
    w0DfFiltered = w0Df[(w0Df['W0APMac'] == 'Not-Associated') & (w0Df['scanW0APLevelMax'] != 0)].reset_index(drop=True)
    w0LevelRatio = w0DfFiltered['scanW0APLevelMax'].quantile(ratio)
    
    w1DfFiltered = w1Df[(w1Df['W1APMac'] == 'Not-Associated') & (w1Df['scanW1APLevelMax'] != 0)].reset_index(drop=True)
    w1LevelRatio = w1DfFiltered['scanW1APLevelMax'].quantile(ratio)
    #####################################################
    #####################################################
    print('非图表型统计数据构造')
    staticsFile = os.path.join(tmpDir, 'statics.csv')
    statics = dict()
    if os.path.isfile(staticsFile):
        statics = pd.read_csv(staticsFile).to_dict('list')
    
    # 数据总数
    statics['WLAN0 Not-Associated数据总数'] = len(w0DfFiltered)
    statics['WLAN1 Not-Associated数据总数'] = len(w1DfFiltered)

    # 极值：未关联基站的最大RSSI分布
    statics['WLAN0未关联基站最大RSSI1'] = w0DfFiltered['scanW0APLevelMax'].min()
    statics['WLAN0未关联基站最大RSSI2'] = w0DfFiltered['scanW0APLevelMax'].max()
    statics['WLAN1未关联基站最大RSSI1'] = w1DfFiltered['scanW1APLevelMax'].min()
    statics['WLAN1未关联基站最大RSSI2'] = w1DfFiltered['scanW1APLevelMax'].max()
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将关键统计数据写入文件**********')
    w0LevelRatio.to_csv(os.path.join(tmpDir, 'WLAN0未关联基站最大RSSI统计信息.csv'))

    w1LevelRatio.to_csv(os.path.join(tmpDir, 'WLAN1未关联基站最大RSSI统计信息.csv'))

    pd.DataFrame(statics, index=[0]).to_csv(os.path.join(tmpDir, 'statics.csv'))
    print('**********第二阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第三阶段：画Not-Associated时扫描到的基站最大RSSI图**********')
    #####################################################
    print('设置图片长宽比，结合dpi确定图片大小')
    plt.rcParams['figure.figsize'] = (6.4, 4.8)
    
    print('画CDF图前的初始化：设置标题、坐标轴')
    plt.title('AGV Not-Associated时扫描到的基站最大RSSI图')

    # plt.xlim([-110, -10])
    plt.xlabel('RSSI(dBm)')

    plt.ylim([0, 1])
    plt.yticks(np.arange(0, 1.1, 0.1))
    #####################################################
    #####################################################
    print("画AGV Not-Associated时扫描到的WLAN0基站最大RSSI图")
    cdfW0Level, = plt.plot(list(w0LevelRatio), list(w0LevelRatio.index), c='red')
    #####################################################
    #####################################################
    print("画AGV Not-Associated时扫描到的WLAN1基站最大RSSI图")
    cdfW1Level, = plt.plot(list(w1LevelRatio), list(w1LevelRatio.index), c='blue')
    #####################################################
    #####################################################
    print("设置标注")
    plt.legend([cdfW0Level, cdfW1Level],
            ['WLAN0', 
             'WLAN1'],
            loc='lower right')
    #####################################################
    #####################################################
    figName = os.path.join(tmpDir, 'AGV Not-Associated时扫描到的基站最大RSSI图' + '.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第三阶段结束**********')
    ###############################################################################



# 基站覆盖热力图，基站覆盖空白热力图，有效基站覆盖热力图，有效基站覆盖空白热力图
# 取每个坐标最大一次探测到的AP数作为覆盖数量
# 标记数据中出现的每一个坐标为车走过的坐标，没出现的坐标则可能是墙、柱子，以及其余区域
# 从坐标系中剔除车没走过的坐标，然后统计剩下的坐标中AP覆盖数为0的坐标
def drawApCover(minW0ConnRSSI, minW1ConnRSSI, scanCsvFileList, tmpDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('构造基站覆盖CDF数据，有效基站覆盖CDF数据，以及统计所有车都没有经过的点')
    # curPosX为列下标，curPosY为行下标
    w0apCount = [[0]*265 for _ in range(139)]
    w1apCount = [[0]*265 for _ in range(139)]

    w0goodApCount = [[0]*265 for _ in range(139)]
    w1goodApCount = [[0]*265 for _ in range(139)]

    # 0表明没车走过，1表明有车走过
    neverWalk = [[0]*265 for _ in range(139)]
    #####################################################
    #####################################################
    print('2020/11/16:14:　补充数据结构记录统计结果的时间戳以及所属车，方便正确性分析从统计结果定位到原始数据')
    w0apCountAppend = [['']*265 for _ in range(139)]
    w1apCountAppend = [['']*265 for _ in range(139)]

    w0goodApCountAppend = [['']*265 for _ in range(139)]
    w1goodApCountAppend = [['']*265 for _ in range(139)]
    #####################################################
    #####################################################
    print('由于将所有scanCsv文件都读入内存会oom，因此改为单行依次处理')
    for scanCsvFile in scanCsvFileList:
        with open(scanCsvFile, 'r') as f:
            for line in f.readlines():
                #####################################################
                # 读入一行数据，构造ScanStatus对象
                scanStatus = ScanStatus()

                line = line.split(',')
                scanStatus.timestamp = int(line[0])
                posX = int(line[1])
                posY = int(line[2])
                w0ApCount = int(line[3])
                w1ApCount = int(line[4])
                try:
                    w0Idx = 5
                    if w0ApCount != 0:
                        scanStatus.w0ApMac = line[w0Idx : w0Idx + w0ApCount]
                        scanStatus.w0Channel = list(map(float, line[w0Idx + w0ApCount : w0Idx + 2 * w0ApCount]))
                        scanStatus.w0Level = list(map(int, line[w0Idx + 2 * w0ApCount : w0Idx + 3 * w0ApCount]))

                    w1Idx = w0Idx + 3 * w0ApCount
                    if w1ApCount != 0:
                        scanStatus.w1ApMac = line[w1Idx : w1Idx + w1ApCount]
                        scanStatus.w1Channel = list(map(float, line[w1Idx + w1ApCount : w1Idx + 2 * w1ApCount]))
                        scanStatus.w1Level = list(map(int, line[w1Idx + 2 * w1ApCount : w1Idx + 3 * w1ApCount]))
                except ValueError:
                    # 由于数据收集脚本的偶发问题，ApMac, Channel, Level的长度可能并不一致
                    # 此种异常数量约为数十次．
                    pass
                ####################################################
                #####################################################
                # 对ScanStatus对象进行处理
                else:
                    # 2020/11/16:14: 配合进行修改
                    agvId = re.findall('(?<=30.113.151.)\d+', scanCsvFile)[0]

                    if len(scanStatus.w0Level) > w0apCount[posY][posX]:
                        w0apCount[posY][posX] = len(scanStatus.w0Level)
                        w0apCountAppend[posY][posX] = '{}|{}'.format(agvId, scanStatus.timestamp)
                    
                    tmpw0goodApCount = len(list(filter(lambda level : level >= minW0ConnRSSI, scanStatus.w0Level)))
                    if tmpw0goodApCount > w0goodApCount[posY][posX]:
                        w0goodApCount[posY][posX] = tmpw0goodApCount
                        w0goodApCountAppend[posY][posX] = '{}|{}'.format(agvId, scanStatus.timestamp)
                    
                    if len(scanStatus.w1Level) > w1apCount[posY][posX]:
                        w1apCount[posY][posX] = len(scanStatus.w1Level)
                        w1apCountAppend[posY][posX] = '{}|{}'.format(agvId, scanStatus.timestamp)
                    
                    tmpw1goodApCount = len(list(filter(lambda level : level >= minW1ConnRSSI, scanStatus.w1Level)))
                    if tmpw1goodApCount > w1goodApCount[posY][posX]:
                        w1goodApCount[posY][posX] = tmpw1goodApCount
                        w1goodApCountAppend[posY][posX] = '{}|{}'.format(agvId, scanStatus.timestamp)

                    neverWalk[posY][posX] = 1
                #####################################################
    #####################################################
    print("统计有车经过但是没有AP覆盖的点")
    # 为方便画热力图，1表明没有AP覆盖，0表明有AP覆盖
    w0NoApCover = [[0]*265 for _ in range(139)]
    w1NoApCover = [[0]*265 for _ in range(139)]

    for y in range(len(w0NoApCover)):
            for x in range(len(w0NoApCover[0])):
                if neverWalk[y][x] == 1 and w0apCount[y][x] == 0:
                    w0NoApCover[y][x] = 1

    for y in range(len(w1NoApCover)):
            for x in range(len(w1NoApCover[0])):
                if neverWalk[y][x] == 1 and w1apCount[y][x] == 0:
                    w1NoApCover[y][x] = 1
    #####################################################
    #####################################################
    print("2020/11/22: 统计有车经过但是没有有效AP覆盖的点")
    # 为方便画热力图，1表明没有AP覆盖，0表明有AP覆盖
    w0NoGoodApCover = [[0]*265 for _ in range(139)]
    w1NoGoodApCover = [[0]*265 for _ in range(139)]

    for y in range(len(w0NoGoodApCover)):
            for x in range(len(w0NoGoodApCover[0])):
                if neverWalk[y][x] == 1 and w0goodApCount[y][x] == 0:
                    w0NoGoodApCover[y][x] = 1

    for y in range(len(w1NoGoodApCover)):
            for x in range(len(w1NoGoodApCover[0])):
                if neverWalk[y][x] == 1 and w1goodApCount[y][x] == 0:
                    w1NoGoodApCover[y][x] = 1
    #####################################################
    #####################################################
    print('2020/11/22:14: 非图表型统计数据构造')
    staticsFile = os.path.join(tmpDir, 'statics.csv')
    statics = dict()
    if os.path.isfile(staticsFile):
        statics = pd.read_csv(staticsFile).to_dict('list')
    
    # 数据总数
    statics['agvWalk'] = sum([len(list(filter(lambda x : x == 1, row))) for row in neverWalk])
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将关键统计数据写入文件**********')
    #####################################################
    print("将无车经过的点写入文件")
    with open(os.path.join(tmpDir, 'neverWalk.csv'), 'w') as f:
        s = '\n'.join([','.join(list(map(str, row))) for row in neverWalk])
        f.write(s)
    #####################################################
    #####################################################
    print('将没有WLAN0基站覆盖的点写入文件')
    with open(os.path.join(tmpDir, 'w0NoApCover.csv'), 'w') as f:
        for y in range(len(w0NoApCover)):
            for x in range(len(w0NoApCover[0])):
                if w0NoApCover[y][x] == 1:
                    f.write('{},{}\n'.format(x, y))
    #####################################################
    #####################################################
    print('将WLAN0基站覆盖数写入文件')
    with open(os.path.join(tmpDir, 'w0apCount.csv'), 'w') as f:
        s = '\n'.join([','.join(list(map(str, row))) for row in w0apCount])
        f.write(s)
    #####################################################
    #####################################################
    print('将WLAN0有效基站覆盖数写入文件')
    with open(os.path.join(tmpDir, 'w0goodApCount.csv'), 'w') as f:
        s = '\n'.join([','.join(list(map(str, row))) for row in w0goodApCount])
        f.write(s)
    #####################################################
    #####################################################
    # 2020/11/16:14: 配合进行补充
    print('将WLAN0基站覆盖数及有效基站覆盖数对应的时间戳及所属车写入文件')
    with open(os.path.join(tmpDir, 'w0apCountAppend.csv'), 'w') as f:
        s = '\n'.join([','.join(row) for row in w0apCountAppend])
        f.write(s)

    with open(os.path.join(tmpDir, 'w0goodApCountAppend.csv'), 'w') as f:
        s = '\n'.join([','.join(row) for row in w0goodApCountAppend])
        f.write(s)
    #####################################################
    #####################################################
    # 2020/11/22:14: 配合进行补充
    print('将WLAN0有效基站覆盖空白坐标写入文件')
    with open(os.path.join(tmpDir, 'w0NoGoodApCover.csv'), 'w') as f:
        for y in range(len(w0NoGoodApCover)):
            for x in range(len(w0NoGoodApCover[0])):
                if w0NoGoodApCover[y][x] == 1:
                    f.write('{},{}\n'.format(x, y))
    #####################################################
    #####################################################
    print('将没有WLAN1基站覆盖的点写入文件')
    with open(os.path.join(tmpDir, 'w1NoApCover.csv'), 'w') as f:
        for y in range(len(w1NoApCover)):
            for x in range(len(w1NoApCover[0])):
                if w1NoApCover[y][x] == 1:
                    f.write('{},{}\n'.format(x, y))
    #####################################################
    #####################################################
    print('将WLAN1基站覆盖数写入文件')
    with open(os.path.join(tmpDir, 'w1apCount.csv'), 'w') as f:
        s = '\n'.join([','.join(list(map(str, row))) for row in w1apCount])
        f.write(s)
    #####################################################
    #####################################################
    print('将WLAN1有效基站覆盖数写入文件')
    with open(os.path.join(tmpDir, 'w1goodApCount.csv'), 'w') as f:
        s = '\n'.join([','.join(list(map(str, row))) for row in w1goodApCount])
        f.write(s)
    #####################################################
    #####################################################
    # 2020/11/16:14: 配合进行补充
    print('将WLAN1基站覆盖数及有效基站覆盖数对应的时间戳及所属车写入文件')
    with open(os.path.join(tmpDir, 'w1apCountAppend.csv'), 'w') as f:
        s = '\n'.join([','.join(row) for row in w1apCountAppend])
        f.write(s)

    with open(os.path.join(tmpDir, 'w1goodApCountAppend.csv'), 'w') as f:
        s = '\n'.join([','.join(row) for row in w1goodApCountAppend])
        f.write(s)
    #####################################################
    #####################################################
    # 2020/11/22:14: 配合进行补充
    print('将WLAN1有效基站覆盖空白坐标写入文件')
    with open(os.path.join(tmpDir, 'w1NoGoodApCover.csv'), 'w') as f:
        for y in range(len(w1NoGoodApCover)):
            for x in range(len(w1NoGoodApCover[0])):
                if w1NoGoodApCover[y][x] == 1:
                    f.write('{},{}\n'.format(x, y))
    #####################################################
    #####################################################
    # 2020/11/22:14: 配合进行添加
    print('将非图表型统计数据写入文件')
    pd.DataFrame(statics, index=[0]).to_csv(os.path.join(tmpDir, 'statics.csv'))
    #####################################################
    print('**********第二阶段结束**********')
    ###############################################################################


    #####################################################
    print("抵消第一个图长宽比不起作用的bug，画两次")
    plt.xlim([0, 264])
    plt.ylim([0, 138])

    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)

    ax = sns.heatmap(w0apCount, cmap="Blues")

    # 逆置Y轴
    ax.invert_yaxis()

    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################


    ###############################################################################
    print('**********第三阶段：画WLAN0与WLAN1基站覆盖热力图**********')
    #####################################################
    print("画所有车数据的WLAN0基站覆盖热力图")
    plt.title('WLAN0基站覆盖热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)
    # w0apcover最大值为35，w1apcover最大值为25，因此颜色条刻度可按5递增
    ax = sns.heatmap(w0apCount, cmap="Blues", vmin=0, 
                     cbar_kws={'ticks': range(0, 41, 5), 'label' : '基站数'})
    plt.xlabel('坐标X轴')
    plt.ylabel('坐标Y轴')
    # 逆置Y轴
    ax.invert_yaxis()
    plt.savefig(os.path.join(tmpDir, 'WLAN0基站覆盖热力图.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    #####################################################
    print("画所有车数据的WLAN1基站覆盖热力图")
    plt.title('WLAN1基站覆盖热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)
    ax = sns.heatmap(w1apCount, cmap="Blues", vmin=0,
                     cbar_kws={'ticks':range(0, 41, 5), 'label':'基站数'})
    plt.xlabel('坐标X轴')
    plt.ylabel('坐标Y轴')
    # 逆置Y轴
    ax.invert_yaxis()
    plt.savefig(os.path.join(tmpDir, 'WLAN1基站覆盖热力图.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第三阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第四阶段：画WLAN0与WLAN1有效基站覆盖热力图**********')
    #####################################################
    print("画所有车数据的WLAN0有效基站覆盖热力图")
    plt.title('WLAN0有效基站覆盖热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)
    # w0apcover最大值为35，w1apcover最大值为25，因此颜色条刻度可按5递增
    ax = sns.heatmap(w0goodApCount, cmap="Blues", vmin=0, 
                     cbar_kws={'ticks': range(0, 41, 5), 'label' : '有效基站数'})
    plt.xlabel('坐标X轴')
    plt.ylabel('坐标Y轴')
    #　添加判断基站有效的RSSI标注
    plt.legend('有效基站RSSI >= ' + str(minW0ConnRSSI), loc='upper right')
    # 逆置Y轴
    ax.invert_yaxis()
    plt.savefig(os.path.join(tmpDir, 'WLAN0有效基站覆盖热力图-RSSI>=' + str(minW0ConnRSSI) + '.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    #####################################################
    print("画所有车数据的WLAN1有效基站覆盖热力图")
    plt.title('WLAN1有效基站覆盖热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)
    ax = sns.heatmap(w1goodApCount, cmap="Blues", vmin=0,
                     cbar_kws={'ticks':range(0, 41, 5), 'label':'有效基站数'})
    plt.xlabel('坐标X轴')
    plt.ylabel('坐标Y轴')
    #　添加判断基站有效的RSSI标注
    plt.legend('有效基站RSSI >= ' + str(minW1ConnRSSI), loc='upper right')
    # 逆置Y轴
    ax.invert_yaxis()
    plt.savefig(os.path.join(tmpDir, 'WLAN1有效基站覆盖热力图-RSSI>=' + str(minW1ConnRSSI) + '.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第四阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第五阶段：画WLAN0与WLAN1没有基站覆盖热力图**********')
    #####################################################
    print("高亮WLAN0没有基站覆盖的热力图")
    plt.title('WLAN0无基站覆盖热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)
    # 2021/3/7: 添加仓库背景
    w0Bg = pd.DataFrame(w0apCount).astype(bool).astype(int).values.tolist()
    ax = sns.heatmap(np.array(w0Bg) + np.array(w0NoApCover) * 20, cbar=False, cmap='Blues')
    plt.xlabel('坐标X轴')
    plt.ylabel('坐标Y轴')
    # 逆置Y轴
    ax.invert_yaxis()
    plt.savefig(os.path.join(tmpDir, 'WLAN0无基站覆盖热力图.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    #####################################################
    print("高亮WLAN1没有基站覆盖的热力图")
    plt.title('WLAN1无基站覆盖热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)
    # 2021/3/7: 添加仓库背景
    w1Bg = pd.DataFrame(w1apCount).astype(bool).astype(int)
    ax = sns.heatmap(np.array(w1Bg) + np.array(w1NoApCover) * 20, cbar=False, cmap='Blues')
    plt.xlabel('坐标X轴')
    plt.ylabel('坐标Y轴')
    # 逆置Y轴
    ax.invert_yaxis()
    plt.savefig(os.path.join(tmpDir, 'WLAN1无基站覆盖热力图.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第五阶段结束**********')
    ###############################################################################


    ###############################################################################
    # 2020/11/22:14: 配合进行添加
    print('**********第六阶段：画WLAN0与WLAN1没有有效基站覆盖热力图**********')
    #####################################################
    print("高亮WLAN0没有有效基站覆盖的热力图")
    plt.title('WLAN0有效基站覆盖空白热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)
    # 2021/3/7: 添加仓库背景
    w0Bg = pd.DataFrame(w0apCount).astype(bool).astype(int)
    ax = sns.heatmap(np.array(w0Bg) + np.array(w0NoGoodApCover) * 20, cbar=False, cmap='Blues')
    plt.xlabel('坐标X轴')
    plt.ylabel('坐标Y轴')
    # 逆置Y轴
    ax.invert_yaxis()
    plt.savefig(os.path.join(tmpDir, 'WLAN0有效基站覆盖空白热力图.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    #####################################################
    print("高亮WLAN1没有有效基站覆盖的热力图")
    plt.title('WLAN1有效基站覆盖空白热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)
    # 2021/3/7: 添加仓库背景
    w1Bg = pd.DataFrame(w1apCount).astype(bool).astype(int)
    ax = sns.heatmap(np.array(w1Bg) + np.array(w1NoGoodApCover) * 20, cbar=False, cmap='Blues')
    plt.xlabel('坐标X轴')
    plt.ylabel('坐标Y轴')
    # 逆置Y轴
    ax.invert_yaxis()
    plt.savefig(os.path.join(tmpDir, 'WLAN1有效基站覆盖空白热力图.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第六阶段结束**********')
    ###############################################################################




# 画基站rssi，时延分布等高线图
def drawApContour(csvFileList, tmpDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读入所有csv文件，并连接为一个dataframe')
    dfList = []
    for csvFile in csvFileList:
        df = pd.read_csv(csvFile, na_filter=False, usecols=['curTimestamp', 'curPosX', 'curPosY',
                            'W0APMac', 'W0level', 'W0pingrtt', 'W1APMac', 'W1level', 'W1pingrtt', 
                            'speed'],
                                dtype={'curTimestamp' : int,
                                       'curPosX': int,
                                       'curPosY': int,
                                       'W0APMac': str,
                                       'W0level' : int, 
                                       'W0pingrtt' : int,
                                       'W1APMac': str,
                                       'W1level' : int,
                                       'W1pingrtt' : int,
                                       'speed' : float})
        dfList.append(df)
    dfAll = pd.concat(dfList, ignore_index=True)
    #####################################################
    #####################################################
    print('分离w0与w1的数据，按(apMac, posX, posY)分组计算每个基站在不同位置的rssi, 时延均值')
    w0Df = dfAll.loc[:,['curPosX', 'curPosY', 'W0APMac', 'W0level', 'W0pingrtt']]
    w0ApDict = dict(list(w0Df[((w0Df['curPosX'] != 0) | (w0Df['curPosY'] != 0)) 
                             & (w0Df['W0level'] != 0) & (w0Df['W0pingrtt'] % 1000 != 0)].groupby('W0APMac')))
    w0ApRssiDict = dict(); w0ApDelayDict = dict()
    for k, v in w0ApDict.items():
        apRssiAndDelayDf = v.groupby(['curPosX', 'curPosY']).mean().reset_index()
        # 计算wlan0基站k在不同位置的rssi均值
        apRssiDf = apRssiAndDelayDf.pivot(index='curPosY', columns='curPosX', values='W0level').fillna(0).astype(int)
        apRssiDf.index = apRssiDf.index.astype(int)
        apRssiDf.columns = apRssiDf.columns.astype(int)
        w0ApRssiDict[k] = apRssiDf.reindex(index=range(139), columns=range(265), fill_value=0).values
        # 计算wlan0基站k在不同位置的时延均值
        apDelayDf = apRssiAndDelayDf.pivot(index='curPosY', columns='curPosX', values='W0pingrtt').fillna(0).astype(int)
        apDelayDf.index = apDelayDf.index.astype(int)
        apDelayDf.columns = apDelayDf.columns.astype(int)
        w0ApDelayDict[k] = apDelayDf.reindex(index=range(139), columns=range(265), fill_value=0).values

    w1Df = dfAll.loc[:,['curPosX', 'curPosY', 'W1APMac', 'W1level', 'W1pingrtt']]
    w1ApDict = dict(list(w1Df[((w1Df['curPosX'] != 0) | (w1Df['curPosY'] != 0)) 
                             & (w1Df['W1level'] != 0) & (w1Df['W1pingrtt'] % 1000 != 0)].groupby('W1APMac')))
    w1ApRssiDict = dict(); w1ApDelayDict = dict()
    for k, v in w1ApDict.items():
        apRssiAndDelayDf = v.groupby(['curPosX', 'curPosY']).mean().reset_index()
        # 计算wlan1基站k在不同位置的rssi均值
        apRssiDf = apRssiAndDelayDf.pivot(index='curPosY', columns='curPosX', values='W1level').fillna(0).astype(int)
        apRssiDf.index = apRssiDf.index.astype(int)
        apRssiDf.columns = apRssiDf.columns.astype(int)
        w1ApRssiDict[k] = apRssiDf.reindex(index=range(139), columns=range(265), fill_value=0).values
        # 计算wlan1基站k在不同位置的时延均值
        apDelayDf = apRssiAndDelayDf.pivot(index='curPosY', columns='curPosX', values='W1pingrtt').fillna(0).astype(int)
        apDelayDf.index = apDelayDf.index.astype(int)
        apDelayDf.columns = apDelayDf.columns.astype(int)
        w1ApDelayDict[k] = apDelayDf.reindex(index=range(139), columns=range(265), fill_value=0).values
    # 生成X, Y坐标
    x = range(265)
    y = range(139)
    X, Y = meshgrid(x, y)
    #####################################################
    #####################################################
    print('非图表型统计数据构造')
    staticsFile = os.path.join(tmpDir, 'statics.csv')
    statics = dict()
    if os.path.isfile(staticsFile):
        statics = pd.read_csv(staticsFile).to_dict('list')

    # 数据总数
    statics['w0基站数'] = len(w0ApDict)
    statics['w1基站数'] = len(w1ApDict)
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将关键统计数据写入文件**********')
    #####################################################
    print('将非图表型统计数据写入文件')
    pd.DataFrame(statics, index=[0]).to_csv(os.path.join(tmpDir, 'statics.csv'))
    #####################################################
    #####################################################
    print('暂存基站rssi/时延分布等高线图数据')
    contourDir = os.path.join(tmpDir, 'contourData')
    if not os.path.isdir(contourDir):
        os.makedirs(contourDir)
    for k, v in w0ApRssiDict.items():
        fileName = 'w0ApRssi-{}.csv'.format(k)
        pd.DataFrame(v).to_csv(os.path.join(contourDir, fileName), index=False, header=False)
    for k, v in w0ApDelayDict.items():
        fileName = 'w0ApDelay-{}.csv'.format(k)
        pd.DataFrame(v).to_csv(os.path.join(contourDir, fileName), index=False, header=False)
    for k, v in w1ApRssiDict.items():
        fileName = 'w1ApRssi-{}.csv'.format(k)
        pd.DataFrame(v).to_csv(os.path.join(contourDir, fileName), index=False, header=False)
    for k, v in w1ApDelayDict.items():
        fileName = 'w1ApDelay-{}.csv'.format(k)
        pd.DataFrame(v).to_csv(os.path.join(contourDir, fileName), index=False, header=False)
    #####################################################
    print('**********第二阶段结束**********')
    ###############################################################################


    # ###############################################################################
    # print('**********第三阶段：画基站rssi分布等高线图**********')
    # #####################################################
    # print('设置图片长宽比，结合dpi确定图片大小')
    # plt.rcParams['figure.figsize'] = (11.0, 5.7)
    
    # print('画CDF图前的初始化：设置标题、坐标轴')
    # plt.title('AGV连接基站的RSSI分布CDF图')

    # plt.xlim([-110, -10])
    # plt.xlabel('RSSI(dBm)')

    # plt.ylim([0, 1])
    # plt.ylabel('CDF')
    # plt.yticks(np.arange(0, 1.1, 0.1))
    # #####################################################
    # #####################################################
    # print("画WLAN0的RSSI图")
    # plt.contour(X, Y, w0ApRssiDict.values()[0])
    # #####################################################
    # #####################################################
    # figName = os.path.join(tmpDir, 'WLAN0基站rssi分布等高线图.png')
    # print('保存到：', figName)
    # plt.savefig(figName, dpi=150)
    # plt.pause(1)
    # plt.close()
    # plt.pause(1)
    # #####################################################
    # print('**********第三阶段结束**********')
    # ###############################################################################




if __name__ == '__main__':
    # 显示中文
    import locale
    locale.setlocale(locale.LC_CTYPE, 'zh_CN.utf8')
    from pylab import *
    mpl.rcParams['font.sans-serif'] = ['SimHei']
    mpl.rcParams['axes.unicode_minus'] = False

    ###############################################################################
    print('**********基站覆盖分析->第一阶段：单车数据统计**********')
    #####################################################
    for i in range(1, 42):
        st = time.time()

        fileName = '30.113.151.' + str(i)
        print(fileName)
        csvPath = os.path.join(r'/home/cx/Desktop/sdb-dir/tmp', fileName)
        csvFile = os.path.join(csvPath, 'data.csv')
        connCsvFile = os.path.join(csvPath, 'connData.csv')
        scanCsvFile = os.path.join(csvPath, 'scanData.csv')
        if os.path.isdir(csvPath):
            print("基站覆盖分析")
            apCoverDir = os.path.join(csvPath, 'analysisApCover')
            if not os.path.isdir(apCoverDir):
                os.makedirs(apCoverDir)

            print('单车数据的AGV连接基站的RSSI分布CDF，rssi与时延关系图')
            drawConnLevel([csvFile], apCoverDir)

            print('单车数据的AGV Not-Associated时扫描到的基站最大RSSI分布CDF')
            drawNotConnLevel([csvFile], [connCsvFile], apCoverDir)

            print('单车数据的基站覆盖热力图')
            w0GoodRSSI = -83
            w1GoodRSSI = -68
            drawApCover(w0GoodRSSI, w1GoodRSSI, [scanCsvFile], apCoverDir)

            print('单车数据的基站rssi/时延分布等高线图')
            drawApContour([csvFile], apCoverDir)
        et = time.time()
        print('单车{}基站覆盖分析耗时{}s'.format(fileName, int(et - st)))
    #####################################################
    print('**********基站覆盖分析->第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********基站覆盖分析->第二阶段：所有车数据统计**********')
    #####################################################
    st = time.time()

    print('构造文件夹')
    topTmpPath = r'/home/cx/Desktop/sdb-dir/tmp'
    topDataPath = r'/home/cx/Desktop/sdb-dir/'
    # csvFile与scanCsvFile按顺序一一对应
    csvFileList = [os.path.join(os.path.join(topTmpPath, path), 'data.csv') 
                   for path in os.listdir(topTmpPath)
                   if os.path.isfile(os.path.join(os.path.join(topTmpPath, path), 'data.csv'))]
    connCsvFileList = [os.path.join(os.path.split(f)[0], 'connData.csv') for f in csvFileList]
    scanCsvFileList = [os.path.join(os.path.split(f)[0], 'scanData.csv') for f in csvFileList]
    #####################################################
    #####################################################
    print("基站覆盖分析")
    apCoverDir = os.path.join(topDataPath, 'analysisApCover')
    if not os.path.isdir(apCoverDir):
        os.makedirs(apCoverDir)

    print('所有车数据的AGV连接基站的RSSI分布CDF')
    drawConnLevel(csvFileList, apCoverDir)

    print('所有车数据的AGV Not-Associated时扫描到的基站最大RSSI分布CDF')
    drawNotConnLevel(csvFileList, connCsvFileList, apCoverDir)

    print('所有车数据的基站覆盖热力图')
    w0GoodRSSI = -83
    w1GoodRSSI = -68
    drawApCover(w0GoodRSSI, w1GoodRSSI, scanCsvFileList, apCoverDir)

    print('所有车数据的基站rssi/时延分布等高线图')
    drawApContour(csvFileList, apCoverDir)

    et = time.time()
    print('所有车基站覆盖分析耗时{}s'.format(int(et - st)))
    #####################################################
    print('**********基站覆盖分析->第二阶段结束**********')
    ###############################################################################