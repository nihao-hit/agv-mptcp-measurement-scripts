# drawConnLevel : 画无线网卡连接基站的RSSI分布CDF
# drawNotConnLevel : 画无线网卡未连接基站时观测到的基站最大RSSI分布CDF
# drawApCover : 基站覆盖热力图，基站覆盖空白热力图
# drawApCover3D : 基站覆盖三维柱状图
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



# 画无线网卡连接基站的RSSI分布CDF
def drawConnLevel(csvFileList, tmpDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读入所有csv文件，并连接为一个dataframe')
    print('提取level, rtt, 坐标数据')
    dfList = []
    for csvFile in csvFileList:
        df = pd.read_csv(csvFile, usecols=['curTimestamp', 'W0level', 'W1level'],
                                dtype={'curTimestamp' : int,
                                       'W0level' : int, 
                                       'W1level' : int})
        dfList.append(df)
    dfAll = pd.concat(dfList, ignore_index=True)
    #####################################################
    #####################################################
    print('分离w0与w1的数据')
    ratio = np.arange(0, 1.01, 0.01)

    w0Df = dfAll.loc[:,['W0level']]

    w1Df = dfAll.loc[:, ['W1level']]
    #####################################################
    #####################################################
    print('过滤level=0也就是除去数据空洞与未关联基站的时刻数据，构造level的CDF数据')
    w0DfFiltered = w0Df[(w0Df['W0level'] != 0)].reset_index(drop=True)
    w0LevelRatio = w0DfFiltered['W0level'].quantile(ratio)
    
    w1DfFiltered = w1Df[(w1Df['W1level'] != 0)].reset_index(drop=True)
    w1LevelRatio = w1DfFiltered['W1level'].quantile(ratio)
    #####################################################
    #####################################################
    print('非图表型统计数据构造')
    staticsFile = os.path.join(tmpDir, 'statics.csv')
    statics = dict()
    if os.path.isfile(staticsFile):
        statics = pd.read_csv(staticsFile).to_dict('list')
        
    # 数据总数，时间跨度，时间粒度
    statics['conn数据总数'] = len(dfAll)
    statics['WLAN0 RSSI数据总数'] = len(w0Df)
    statics['WLAN0 RSSI过滤后数据总数'] = len(w0DfFiltered)
    statics['WLAN1 RSSI数据总数'] = len(w1Df)
    statics['WLAN1 RSSI过滤后数据总数'] = len(w1DfFiltered)
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
    w0LevelRatio.to_csv(os.path.join(tmpDir, 'WLAN0信号强度统计信息.csv'))

    w1LevelRatio.to_csv(os.path.join(tmpDir, 'WLAN1信号强度统计信息.csv'))

    pd.DataFrame(statics, index=[0]).to_csv(os.path.join(tmpDir, 'statics.csv'))
    print('**********第二阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第三阶段：画无线网络的RSSI图**********')
    #####################################################
    print('画CDF图前的初始化：设置标题、坐标轴')
    plt.title('无线网络的RSSI')

    plt.xlim([-110, -10])
    plt.xlabel('信号强度(dBm)')

    plt.ylim([0, 1])
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
    print("设置标注")
    plt.legend([cdfW0Level, cdfW1Level],
            ['WLAN0', 
             'WLAN1'],
            loc='lower right')
    #####################################################
    #####################################################
    figName = os.path.join(tmpDir, '无线网络的RSSI.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第三阶段结束**********')
    ###############################################################################



# 画无线网卡未连接基站时观测到的基站最大RSSI分布CDF
def drawNotConnLevel(csvFileList, tmpDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读入所有csv文件，并连接为一个dataframe')
    print('提取level, rtt, 坐标数据')
    dfList = []
    for csvFile in csvFileList:
        df = pd.read_csv(csvFile, usecols=['W0APMac', 'W1APMac',
                                           'scanW0APLevelMax', 'scanW1APLevelMax'],
                                dtype={'W0APMac' : str, 
                                       'W1APMac' : str,
                                       'scanW0APLevelMax' : int,
                                       'scanW1APLevelMax' : int})
        dfList.append(df)
    dfAll = pd.concat(dfList, ignore_index=True)
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
    print('**********第三阶段：画未关联基站的最大RSSI图**********')
    #####################################################
    print('画CDF图前的初始化：设置标题、坐标轴')
    plt.title('未关联基站的最大RSSI')

    plt.xlim([-110, -10])
    plt.xlabel('信号强度(dBm)')

    plt.ylim([0, 1])
    plt.yticks(np.arange(0, 1.1, 0.1))
    #####################################################
    #####################################################
    print("画WLAN0的未关联基站的最大RSSI图")
    cdfW0Level, = plt.plot(list(w0LevelRatio), list(w0LevelRatio.index), c='red')
    #####################################################
    #####################################################
    print("画WLAN1的未关联基站的最大RSSI图")
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
    figName = os.path.join(tmpDir, '未关联基站的最大RSSI' + '.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第三阶段结束**********')
    ###############################################################################



# 基站覆盖热力图
# 取每个坐标最大一次探测到的AP数作为覆盖数量
# 标记数据中出现的每一个坐标为车走过的坐标，没出现的坐标则可能是墙、柱子，以及其余区域
# 从坐标系中剔除车没走过的坐标，然后统计剩下的坐标中AP覆盖数为0的坐标
# （车可能存在人为移动，导致一些车平时不会走过，AP覆盖根本不重要的坐标被统计）
def drawApCover(minConnRSSI, scanCsvFileList, tmpDir):
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
                    
                    tmpw0goodApCount = len(list(filter(lambda level : level >= minConnRSSI, scanStatus.w0Level)))
                    if tmpw0goodApCount > w0goodApCount[posY][posX]:
                        w0goodApCount[posY][posX] = tmpw0goodApCount
                        w0goodApCountAppend[posY][posX] = '{}|{}'.format(agvId, scanStatus.timestamp)
                    
                    if len(scanStatus.w1Level) > w1apCount[posY][posX]:
                        w1apCount[posY][posX] = len(scanStatus.w1Level)
                        w1apCountAppend[posY][posX] = '{}|{}'.format(agvId, scanStatus.timestamp)
                    
                    tmpw1goodApCount = len(list(filter(lambda level : level >= minConnRSSI, scanStatus.w1Level)))
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
            for x in range(len(w0NoApCover)):
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
            for x in range(len(w0NoGoodApCover)):
                if w0NoGoodApCover[y][x] == 1:
                    f.write('{},{}\n'.format(x, y))
    #####################################################
    #####################################################
    print('将没有WLAN1基站覆盖的点写入文件')
    with open(os.path.join(tmpDir, 'w1NoApCover.csv'), 'w') as f:
        for y in range(len(w1NoApCover)):
            for x in range(len(w1NoApCover)):
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
            for x in range(len(w1NoGoodApCover)):
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
    plt.legend('有效基站RSSI >= ' + str(minConnRSSI), loc='upper right')
    # 逆置Y轴
    ax.invert_yaxis()
    plt.savefig(os.path.join(tmpDir, 'WLAN0有效基站覆盖热力图-RSSI>=' + str(minConnRSSI) + '.png'), dpi=150)
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
    plt.legend('有效基站RSSI >= ' + str(minConnRSSI), loc='upper right')
    # 逆置Y轴
    ax.invert_yaxis()
    plt.savefig(os.path.join(tmpDir, 'WLAN1有效基站覆盖热力图-RSSI>=' + str(minConnRSSI) + '.png'), dpi=150)
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
    ax = sns.heatmap(w0NoApCover, cmap="Blues", vmin=0,
                     cbar_kws={'ticks':[0, 1]})
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
    ax = sns.heatmap(w1NoApCover, cmap="Blues", vmin=0,
                     cbar_kws={'ticks':[0, 1]})
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
    ax = sns.heatmap(w0NoGoodApCover, cmap="Blues", vmin=0,
                     cbar_kws={'ticks':[0, 1]})
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
    ax = sns.heatmap(w1NoGoodApCover, cmap="Blues", vmin=0,
                     cbar_kws={'ticks':[0, 1]})
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



# 基站覆盖三维柱状图
def drawApCover3D(csvFileList, tmpDir):
    scanW0APCount = []
    scanW1APCount = []
    curPosX = []
    curPosY = []
    for csvFile in csvFileList:
        df = pd.read_csv(csvFile, usecols=['scanW0APCount', 'scanW1APCount',
                                           'curPosX', 'curPosY'],
                                dtype={'scanW0APCount' : int, 
                                       'scanW1APCount' : int, 
                                       'curPosX' : int,
                                       'curPosY' : int})
        scanW0APCount += list(df['scanW0APCount'])
        scanW1APCount += list(df['scanW1APCount'])
        curPosX += list(df['curPosX'])
        curPosY += list(df['curPosY'])

    # curPosX为列下标，curPosY为行下标
    agvWalk = [[0]*265 for _ in range(139)]

    w0apCount = [[0]*265 for _ in range(139)]
    w1apCount = [[0]*265 for _ in range(139)]
    # 0表明没车走过，1表明有车走过
    neverWalk = [[0]*265 for _ in range(139)]
    # 为方便画热力图，1表明没有AP覆盖，0表明有AP覆盖
    w0NoApCover = [[0]*265 for _ in range(139)]
    w1NoApCover = [[0]*265 for _ in range(139)]

    for i in range(len(curPosX)):
        agvWalk[curPosY[i]][curPosX[i]] += 1
        w0apCount[curPosY[i]][curPosX[i]] = max(w0apCount[curPosY[i]][curPosX[i]], scanW0APCount[i])
        w1apCount[curPosY[i]][curPosX[i]] = max(w1apCount[curPosY[i]][curPosX[i]], scanW1APCount[i])
        neverWalk[curPosY[i]][curPosX[i]] = 1
        
    #################################################
    print("记录所有车都没有经过的点，以及有车经过的点但是没有AP覆盖的点")
    for y in range(len(w0NoApCover)):
            for x in range(len(w0NoApCover[0])):
                if neverWalk[y][x] == 1 and w0apCount[y][x] == 0:
                    w0NoApCover[y][x] = 1

    for y in range(len(w1NoApCover)):
            for x in range(len(w1NoApCover[0])):
                if neverWalk[y][x] == 1 and w1apCount[y][x] == 0:
                    w1NoApCover[y][x] = 1

    with open(os.path.join(tmpDir, 'neverWalk.csv'), 'w') as f:
        f.write('{},{}\n'.format('curPosX', 'curPosY'))
        for y in range(len(neverWalk)):
            for x in range(len(neverWalk[0])):
                if neverWalk[y][x] == 0:
                    f.write('{},{}\n'.format(x, y))
    
    with open(os.path.join(tmpDir, 'w0NoApCover.csv'), 'w') as f:
        f.write('{},{}\n'.format('curPosX', 'curPosY'))
        for y in range(len(w0NoApCover)):
            for x in range(len(w0NoApCover[0])):
                if w0NoApCover[y][x] == 1:
                    f.write('{},{}\n'.format(x, y))
    
    with open(os.path.join(tmpDir, 'w1NoApCover.csv'), 'w') as f:
        f.write('{},{}\n'.format('curPosX', 'curPosY'))
        for y in range(len(w1NoApCover)):
            for x in range(len(w1NoApCover[0])):
                if w1NoApCover[y][x] == 1:
                    f.write('{},{}\n'.format(x, y))
    ################################################

    fig = plt.figure(figsize=(11.0, 6.0))
    axWlan0ApCover = Axes3D(fig)
    # axWlan0ApNoCover = fig.add_subplot(122, projection='3d')

    # fake data
    _x = np.arange(265)
    _y = np.arange(139)
    _xx, _yy = np.meshgrid(_x, _y)
    x, y = _xx.ravel(), _yy.ravel()

    topWlan0ApCover = np.array(w0apCount).ravel()
    # topWlan0ApNoCover = np.array(w0NoApCover).ravel()
    bottom = np.zeros_like(topWlan0ApCover)

    axWlan0ApCover.bar3d(x, y, bottom, 1, 1, topWlan0ApCover, shade=True)
    axWlan0ApCover.set_title('WLAN0基站覆盖三维柱状图')

    # axWlan0ApNoCover.bar3d(x, y, bottom, 1, 1, topWlan0ApNoCover, shade=True)
    # axWlan0ApNoCover.set_title('WLAN0无基站覆盖三维柱状图')

    plt.show()

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


    #####################################################
    print("画所有车数据的w0 AP覆盖热力图")
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

    # # 设置标题
    # ax.set_title('w0-ap-count')

    # 逆置Y轴
    ax.invert_yaxis()

    # sns.heatmap(w0NoApCover, cmap="Reds")

    plt.savefig(os.path.join(tmpDir, 'WLAN0基站覆盖热力图.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################


    #####################################################
    print("画所有车数据的w1 AP覆盖热力图")
    plt.title('WLAN1基站覆盖热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])

    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)

    ax = sns.heatmap(w1apCount, cmap="Blues", vmin=0,
                     cbar_kws={'ticks':range(0, 41, 5), 'label':'基站数'})

    plt.xlabel('坐标X轴')
    plt.ylabel('坐标Y轴')

    # # 设置标题
    # ax.set_title('w1-ap-count')

    # 逆置Y轴
    ax.invert_yaxis()

    # sns.heatmap(w1NoApCover, cmap="Reds")

    plt.savefig(os.path.join(tmpDir, 'WLAN1基站覆盖热力图.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################


    #####################################################
    print("高亮w0 AP没有覆盖的热力图")
    plt.title('WLAN0无基站覆盖热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])

    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)

    ax = sns.heatmap(w0NoApCover, cmap="Blues", vmin=0,
                     cbar_kws={'ticks':[0, 1]})

    plt.xlabel('坐标X轴')
    plt.ylabel('坐标Y轴')

    # # 设置标题
    # ax.set_title('w0-no-ap-cover')

    # 逆置Y轴
    ax.invert_yaxis()

    plt.savefig(os.path.join(tmpDir, 'WLAN0无基站覆盖热力图.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################


    #####################################################
    print("高亮w1 AP没有覆盖的热力图")
    plt.title('WLAN1无基站覆盖热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])

    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)

    ax = sns.heatmap(w1NoApCover, cmap="Blues", vmin=0,
                     cbar_kws={'ticks':[0, 1]})

    plt.xlabel('坐标X轴')
    plt.ylabel('坐标Y轴')

    # # 设置标题
    # ax.set_title('w1-no-ap-cover')

    # 逆置Y轴
    ax.invert_yaxis()

    plt.savefig(os.path.join(tmpDir, 'WLAN1无基站覆盖热力图.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################


    #####################################################
    print("画所有车跑过的热力图")
    plt.title('AGV轨迹热力图')
    plt.xlim([0, 264])
    plt.ylim([0, 138])

    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 5.7)

    ax = sns.heatmap(agvWalk, cmap="Blues", vmin=0,
                     cbar_kws={'label':'经过次数'})

    plt.xlabel('坐标X轴')
    plt.ylabel('坐标Y轴')

    # # 设置标题
    # ax.set_title('w1-no-ap-cover')

    # 逆置Y轴
    ax.invert_yaxis()

    plt.savefig(os.path.join(tmpDir, 'AGV轨迹热力图.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################




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
        fileName = '30.113.151.' + str(i)
        print(fileName)
        csvPath = os.path.join(r'/home/cx/Desktop/sdb-dir/tmp', fileName)
        csvFile = os.path.join(csvPath, 'data.csv')
        scanCsvFile = os.path.join(csvPath, 'scanData.csv')
        if os.path.isdir(csvPath):
            print("基站覆盖分析")
            apCoverDir = os.path.join(csvPath, 'analysisApCover')
            if not os.path.isdir(apCoverDir):
                os.makedirs(apCoverDir)

            print('单车数据的无线网卡连接基站的RSSI分布CDF')
            drawConnLevel([csvFile], apCoverDir)

            print('单车数据的无线网卡未连接基站时观测到的基站最大RSSI分布CDF')
            drawNotConnLevel([csvFile], apCoverDir)

            print('单车数据的基站覆盖热力图')
            goodRSSI = -70
            drawApCover(goodRSSI, [scanCsvFile], apCoverDir)
    #####################################################
    print('**********基站覆盖分析->第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********基站覆盖分析->第二阶段：所有车数据统计**********')
    #####################################################
    print('构造文件夹')
    topTmpPath = r'/home/cx/Desktop/sdb-dir/tmp'
    topDataPath = r'/home/cx/Desktop/sdb-dir/'
    # csvFile与scanCsvFile按顺序一一对应
    csvFileList = [os.path.join(os.path.join(topTmpPath, path), 'data.csv') 
                   for path in os.listdir(topTmpPath)
                   if os.path.isfile(os.path.join(os.path.join(topTmpPath, path), 'data.csv'))]
    scanCsvFileList = [os.path.join(os.path.split(f)[0], 'scanData.csv') for f in csvFileList]
    #####################################################
    #####################################################
    print("基站覆盖分析")
    apCoverDir = os.path.join(topDataPath, 'analysisApCover')
    if not os.path.isdir(apCoverDir):
        os.makedirs(apCoverDir)

    print('所有车数据的无线网卡连接基站的RSSI分布CDF')
    drawConnLevel(csvFileList, apCoverDir)

    print('所有车数据的无线网卡未连接基站时观测到的基站最大RSSI分布CDF')
    drawNotConnLevel(csvFileList, apCoverDir)

    print('所有车数据的基站覆盖热力图')
    goodRSSI = -70
    drawApCover(goodRSSI, scanCsvFileList, apCoverDir)
    #####################################################
    print('**********基站覆盖分析->第二阶段结束**********')
    ###############################################################################