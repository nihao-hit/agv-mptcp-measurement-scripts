# analysisRtt : w0rtt，w1rtt，w0rtt与w1rtt最小值，srtt随时间分布散点图
# drawCDFForAllAgvData : 画所有车数据的w0rtt、w1rtt、w0rtt与w1rtt最小值、srtt的CDF图
# drawCDFForOneAgvData : 画单台车数据的w0rtt、w1rtt、w0rtt与w1rtt最小值、srtt的CDF图
from matplotlib import pyplot as plt 
import seaborn as sns
import numpy as np
import pandas as pd 
import time
import os

# w0rtt，w1rtt，w0rtt与w1rtt最小值，srtt随时间分布散点图
def analysisRtt(csvFile, tmpDir):
    df = pd.read_csv(csvFile, usecols=['curTimestamp', 'W0pingrtt', 'W1pingrtt', 'srtt',
                                       'curPosX', 'curPosY'],
                              dtype={'curTimestamp' : int, 
                                     'W0pingrtt' : int, 
                                     'W1pingrtt' : int,
                                     'srtt': int,
                                     'curPosX' : int,
                                     'curPosY' : int})
    curTimestamp = df['curTimestamp']
    # curPosX = df['curPosX']
    # curPosY = df['curPosY']
    W0pingrtt = df['W0pingrtt']
    W1pingrtt = df['W1pingrtt']
    srtt = df['srtt']

    # with open(os.path.join(tmpDir, 'rtts.csv'), 'w') as f:
    #     f.write('{:<14},{:<12},{:<12},{:<12},{:<7},{:<7}\n'. \
    #         format('curTimestamp', 'W0pingrtt', 'W1pingrtt', 'srtt', 'curPosX', 'curPosY'))
    #     for i in range(len(curTimestamp)):
    #         f.write('{:<14},{:<12},{:<12},{:<12},{:<7},{:<7}\n'. \
    #             format(curTimestamp[i], W0pingrtt[i], W1pingrtt[i], srtt[i], curPosX[i], curPosY[i]))

    #######################################
    # 统计w0超时30s，w1超时30s，srtt超时30s的时段及时长
    # 写入文件
    w0s = 0
    w1s = 0
    srttStart = 0
    w0DropTimes = []
    w1DropTimes = []
    srttDropTimes = []
    for i in range(len(curTimestamp)):
        if W0pingrtt[i] >= 30000:
            if w0s == 0:
                w0s = curTimestamp[i]
        else:
            if w0s != 0:
                w0DropTimes.append((w0s, curTimestamp[i]-1))
                w0s = 0
    for i in range(len(curTimestamp)):
        if W1pingrtt[i] >= 30000:
            if w1s == 0:
                w1s = curTimestamp[i]
        else:
            if w1s != 0:
                w1DropTimes.append((w1s, curTimestamp[i]-1))
                w1s = 0
    for i in range(len(curTimestamp)):
        if srtt[i] >= 30000:
            if srttStart == 0:
                srttStart = curTimestamp[i]
        else:
            if srttStart != 0:
                srttDropTimes.append((srttStart, curTimestamp[i]-1))
                srttStart = 0
    with open(os.path.join(tmpDir, 'w0drops.csv'), 'w') as f:
        f.write('{},{},{},{},{}\n'. \
            format('startDate', 'endDate', 'startTimestamp', 'endTimestamp', 'duration'))
        for tpl in w0DropTimes:
            f.write('{},{},{},{},{}\n'.format(
                time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(tpl[0])),
                time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(tpl[1])),
                tpl[0],
                tpl[1],
                tpl[1] - tpl[0] + 1
                )
            )
    with open(os.path.join(tmpDir, 'w1drops.csv'), 'w') as f:
        f.write('{},{},{},{},{}\n'. \
            format('startDate', 'endDate', 'startTimestamp', 'endTimestamp', 'duration'))
        for tpl in w1DropTimes:
            f.write('{},{},{},{},{}\n'.format(
                time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(tpl[0])),
                time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(tpl[1])),
                tpl[0],
                tpl[1],
                tpl[1] - tpl[0] + 1
                )
            )
    with open(os.path.join(tmpDir, 'srttDrops.csv'), 'w') as f:
        f.write('{},{},{},{},{}\n'. \
            format('startDate', 'endDate', 'startTimestamp', 'endTimestamp', 'duration'))
        for tpl in srttDropTimes:
            f.write('{},{},{},{},{}\n'.format(
                time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(tpl[0])),
                time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(tpl[1])),
                tpl[0],
                tpl[1],
                tpl[1] - tpl[0] + 1
                )
            )
    ########################################################################

    #####################################################################
    minW0AndW1 = [min(W0pingrtt[i], W1pingrtt[i]) for i in range(len(W0pingrtt))]
    
    # 将unix时间戳转换为日历时间
    # 30.113.151.1车采集数据时间最长，从8月5日到8月20日，共16天。一天86400秒
    sTime, eTime = curTimestamp[0], curTimestamp[len(curTimestamp)-1]
    xticks = [i for i in range(sTime, eTime+43200, 86400)]
    yticks = np.arange(0, 3.5, 0.5)
    xlabels = [time.strftime('%m月%d日', time.localtime(i)) for i in xticks]
    ylabels = ['0', '0.5s', '1s', '1.5s', '2s', '2.5s', '3s']

    # w0rtt，w1rtt，w0rtt与w1rtt最小值，srtt随时间分布散点图
    #####################################################################
    # 不知道为什么画w0-ping-rtt长宽比总是不起作用，所以只好画两次
    print("画w0rtt随时间分布散点图")
    plt.title('w0-ping-rtt')

    plt.xlim([sTime, eTime])
    plt.ylim([0, 5])

    plt.xticks(xticks, rotation=45)
    plt.xlabel(' '.join(list(map(str, xlabels))))

    # 设置坐标轴，不显示x轴刻度值，只显示标签值
    plt.tick_params(labelbottom=False)

    # 设置图片长宽比，结合dpi确定图片大小
    # 目前来看展示20天数据的时候(12.0, 4.0)比较好，那么为了自适应天数,
    # 将12.0改为len(xticks)/2
    plt.rcParams['figure.figsize'] = (len(xticks)/2, 4.0)

    plt.scatter(curTimestamp, list(map(lambda x: x/1000, W0pingrtt)), s=1)
    # plt.savefig(os.path.join(tmpDir, 'w0-ping-rtt.png'),
    #             dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    ##########################################################


    ##########################################################
    # print('准备w0rtt、w1rtt、minRtt、srtt数据，只保留w0rtt、w1rtt、srtt都有数据的时刻'
    #       '这是因为本来就是为了对比四者的区别，因此要控制变量。')
    print('准备w0rtt、w1rtt、minRtt、srtt数据，对w0rtt与w1rtt，分别保留正常数据，'
          '对minRtt与srtt，只保留minRtt、srtt都有数据的时刻')
    w0rttX = []
    w1rttX = []

    w0rttY = []
    w1rttY = []

    minRttAndSrttX = []
    minRttY = []
    srttY = []
    for i in range(len(curTimestamp)):
        if W0pingrtt[i] % 1000 != 0:
            w0rttX.append(curTimestamp[i])
            w0rttY.append(W0pingrtt[i]/1000)
        if W1pingrtt[i] % 1000 != 0:
            w1rttX.append(curTimestamp[i])
            w1rttY.append(W1pingrtt[i]/1000)
        if minW0AndW1[i] % 1000 != 0 and srtt[i] % 1000 != 0:
            minRttAndSrttX.append(curTimestamp[i])
            minRttY.append(minW0AndW1[i]/1000)
            srttY.append(srtt[i]/1000)
    ##########################################################


    #######################################################
    print("画w0rtt随时间分布散点图")
    plt.title('WLAN0时延分布图')

    plt.xlim([sTime, eTime])
    plt.ylim([0, 3])

    plt.xticks(xticks, xlabels, rotation=45)
    plt.yticks(yticks, ylabels)

    plt.xlabel('日期')
    plt.ylabel('时延')

    # # 设置坐标轴，不显示x轴刻度值，只显示标签值
    # plt.tick_params(labelbottom=False)

    # 设置图片长宽比，结合dpi确定图片大小
    # 将12.0改为len(xticks)/2
    plt.rcParams['figure.figsize'] = (len(xticks)/2, 4.0)

    plt.scatter(w0rttX, w0rttY, s=1)

    # 调整图像避免截断xlabel
    plt.tight_layout()

    plt.savefig(os.path.join(tmpDir, 'WLAN0时延分布图-' + str(len(w0rttX)) + '.png'),
                dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    ########################################################


    ######################################################
    print("画w1rtt随时间分布散点图")
    plt.title('WLAN1时延分布图')

    plt.xlim([sTime, eTime])
    plt.ylim([0, 3])

    plt.xticks(xticks, xlabels, rotation=45)
    plt.yticks(yticks, ylabels)

    plt.xlabel('日期')
    plt.ylabel('时延')

    # # 设置坐标轴，不显示x轴刻度值，只显示标签值
    # plt.tick_params(labelbottom=False)

    # 设置图片长宽比，结合dpi确定图片大小
    # 将12.0改为len(xticks)/2
    plt.rcParams['figure.figsize'] = (len(xticks)/2, 4.0)
    
    plt.scatter(w1rttX, w1rttY, s=1)
    # 调整图像避免截断xlabel
    plt.tight_layout()
    plt.savefig(os.path.join(tmpDir, 'WLAN1时延分布图-' + str(len(w1rttX)) + '.png'),
                dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    ######################################################


    #########################################################
    print("画w0rtt与w1rtt最小值随时间分布散点图")
    plt.title('min(WLAN0, WLAN1)时延分布图')

    plt.xlim([sTime, eTime])
    plt.ylim([0, 3])

    plt.xticks(xticks, xlabels, rotation=45)
    plt.yticks(yticks, ylabels)

    plt.xlabel('日期')
    plt.ylabel('时延')

    # # 设置坐标轴，不显示x轴刻度值，只显示标签值
    # plt.tick_params(labelbottom=False)

    # 设置图片长宽比，结合dpi确定图片大小
    # 将12.0改为len(xticks)/2
    plt.rcParams['figure.figsize'] = (len(xticks)/2, 4.0)

    plt.scatter(minRttAndSrttX, minRttY, s=1)
    # 调整图像避免截断xlabel
    plt.tight_layout()
    plt.savefig(os.path.join(tmpDir, 'min(WLAN0, WLAN1)时延分布图-' + str(len(minRttAndSrttX)) + '.png'),
                dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    ###############################################################


    #############################################################
    print("画srtt随时间分布散点图")
    plt.title('MPTCP时延分布图')

    plt.xlim([sTime, eTime])
    plt.ylim([0, 3])

    plt.xticks(xticks, xlabels, rotation=45)
    plt.yticks(yticks, ylabels)

    plt.xlabel('日期')
    plt.ylabel('时延')

    # # 设置坐标轴，不显示x轴刻度值，只显示标签值
    # plt.tick_params(labelbottom=False)

    # 设置图片长宽比，结合dpi确定图片大小
    # 将12.0改为len(xticks)/2
    plt.rcParams['figure.figsize'] = (len(xticks)/2, 4.0)

    plt.scatter(minRttAndSrttX, srttY, s=1)
    # 调整图像避免截断xlabel
    plt.tight_layout()
    plt.savefig(os.path.join(tmpDir, 'MPTCP时延分布图-' + str(len(minRttAndSrttX)) + '.png'),
                dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #######################################################################




# 画所有车数据的w0rtt、w1rtt、w0rtt与w1rtt最小值、srtt的CDF图
def drawCDFForAllAgvData(csvFileList, tmpDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读入所有csv文件，并连接为一个dataframe')
    dfList = []
    for csvFile in csvFileList:
        df = pd.read_csv(csvFile, usecols=['W0pingrtt', 'W1pingrtt', 'srtt'],
                                  dtype={'W0pingrtt' : int, 
                                         'W1pingrtt' : int,
                                         'srtt':int})
        dfList.append(df)
    dfAll = pd.concat(dfList, ignore_index=True)
    #####################################################
    #####################################################
    print('只保留w0rtt、w1rtt、srtt都有数据的时间戳对应的时延数据，并生成min(w0rtt, w1rtt)')
    dfAllFiltered = dfAll[(dfAll['W0pingrtt'] % 1000 != 0) & 
                          (dfAll['W1pingrtt'] % 1000 != 0) & 
                          (dfAll['srtt'] % 1000 != 0)].reset_index(drop=True)
    dfAllFiltered['minRtt'] = dfAllFiltered.apply(lambda row: min(row['W0pingrtt'], row['W1pingrtt']), axis=1)
    #####################################################
    #####################################################
    print('构造CDF数据')
    ratio = np.arange(0, 1.01, 0.01)
    w0RttRatio = dfAllFiltered['W0pingrtt'].quantile(ratio)
    w1RttRatio = dfAllFiltered['W1pingrtt'].quantile(ratio)
    minRttRatio = dfAllFiltered['minRtt'].quantile(ratio)
    srttRatio = dfAllFiltered['srtt'].quantile(ratio)
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将关键统计数据写入文件**********')
    # pd.set_option('display.float_format', lambda x: '%.f' % x)
    staticsDfAll = dfAll.describe(percentiles=ratio).astype(int)
    staticsDfAll.to_csv(os.path.join(tmpDir, '数据清洗前统计信息.csv'))

    staticsDfAllFiltered = dfAllFiltered.describe(percentiles=ratio).astype(int)
    staticsDfAllFiltered.to_csv(os.path.join(tmpDir, '数据清洗后统计信息.csv'))
    print('**********第二阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第三阶段：画图**********')
    #####################################################
    print('画CDF图前的初始化：设置标题、坐标轴')
    plt.title('所有车的时延CDF')

    plt.xlim([0, 200])
    plt.ylim([0, 1])

    plt.xticks([0, 10, 20, 50, 100, 200],
               ['0', '10ms', '20ms', '50ms', '100ms', '200ms'])
    plt.yticks(np.arange(0, 1.1, 0.1))

    # # 设置坐标轴刻度间隔为对数型
    # # error: 有非正数数据
    # ax = plt.gca()
    # ax.set_xscale('log', basex=2)
    # ax.set_xticks([10, 100, 250, 500, 1000, 5000, 10000], minor=True)
    # ax.set_xticklabels(['10ms', '100ms', '250ms', '0.5s', '1s', '5s', '10s'])
    # ax.set_xticklabels(['']*7, minor=True)
    #####################################################
    #####################################################
    print("画所有车的w0rtt的CDF图")
    # 如果不加','，报错
    # UserWarning: Legend does not support [<matplotlib.lines.Line2D object at 0x00000266279B1D08>] instances.
    # A proxy artist may be used instead.
    # See: http://matplotlib.org/users/legend_guide.html#creating-artists-specifically-for-adding-to-the-legend-aka-proxy-artists
    # loc='lower right')
    cdfW0pingrtt, = plt.plot(list(w0RttRatio), list(w0RttRatio.index), c='red')
    #####################################################
    #####################################################
    print("画所有车的w1rtt的CDF图")
    cdfW1pingrtt, = plt.plot(list(w1RttRatio), list(w1RttRatio.index), c='yellow')
    #####################################################
    #####################################################
    print("画所有车的w0rtt与w1rtt最小值的CDF图")
    cdfminW0AndW1, = plt.plot(list(minRttRatio), list(minRttRatio.index), c='blue')
    #####################################################
    #####################################################
    print("画所有车的srtt的CDF图")
    cdfsrtt, = plt.plot(list(srttRatio), list(srttRatio.index), c='green')
    #####################################################
    #####################################################
    print("设置标注")
    plt.legend([cdfW0pingrtt, cdfW1pingrtt, cdfminW0AndW1, cdfsrtt],
            ['WLAN0时延', 
             'WLAN1时延', 
             'min(WLAN0, WLAN1)时延', 
             'MPTCP时延'],
            loc='lower right')
    #####################################################
    #####################################################
    figName = os.path.join(tmpDir, '所有车的时延CDF-' + '.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第三阶段结束**********')
    ###############################################################################
    



# 画单台车数据的w0rtt、w1rtt、w0rtt与w1rtt最小值、srtt的CDF图
def drawCDFForOneAgvData(csvFile, tmpDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读入csv文件为一个dataframe')
    dfAll = pd.read_csv(csvFile, usecols=['W0pingrtt', 'W1pingrtt', 'srtt'],
                                  dtype={'W0pingrtt' : int, 
                                         'W1pingrtt' : int,
                                         'srtt':int})
    #####################################################
    #####################################################
    print('只保留w0rtt、w1rtt、srtt都有数据的时间戳对应的时延数据，并生成min(w0rtt, w1rtt)')
    dfAllFiltered = dfAll[(dfAll['W0pingrtt'] % 1000 != 0) & 
                          (dfAll['W1pingrtt'] % 1000 != 0) & 
                          (dfAll['srtt'] % 1000 != 0)].reset_index(drop=True)
    dfAllFiltered['minRtt'] = dfAllFiltered.apply(lambda row: min(row['W0pingrtt'], row['W1pingrtt']), axis=1)
    #####################################################
    #####################################################
    print('构造CDF数据')
    ratio = np.arange(0, 1.01, 0.01)
    w0RttRatio = dfAllFiltered['W0pingrtt'].quantile(ratio)
    w1RttRatio = dfAllFiltered['W1pingrtt'].quantile(ratio)
    minRttRatio = dfAllFiltered['minRtt'].quantile(ratio)
    srttRatio = dfAllFiltered['srtt'].quantile(ratio)
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将关键统计数据写入文件**********')
    # pd.set_option('display.float_format', lambda x: '%.f' % x)
    staticsDfAll = dfAll.describe(percentiles=ratio).astype(int)
    staticsDfAll.to_csv(os.path.join(tmpDir, '数据清洗前统计信息.csv'))

    staticsDfAllFiltered = dfAllFiltered.describe(percentiles=ratio).astype(int)
    staticsDfAllFiltered.to_csv(os.path.join(tmpDir, '数据清洗后统计信息.csv'))
    print('**********第二阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第三阶段：画图**********')
    #####################################################
    print('画CDF图前的初始化：设置标题、坐标轴')
    plt.title('单台车的时延CDF')

    plt.xlim([0, 200])
    plt.ylim([0, 1])

    plt.xticks([0, 10, 20, 50, 100, 200],
               ['0', '10ms', '20ms', '50ms', '100ms', '200ms'])
    plt.yticks(np.arange(0, 1.1, 0.1))

    # # 设置坐标轴刻度间隔为对数型
    # # error: 有非正数数据
    # ax = plt.gca()
    # ax.set_xscale('log', basex=2)
    # ax.set_xticks([10, 100, 250, 500, 1000, 5000, 10000], minor=True)
    # ax.set_xticklabels(['10ms', '100ms', '250ms', '0.5s', '1s', '5s', '10s'])
    # ax.set_xticklabels(['']*7, minor=True)
    #####################################################
    #####################################################
    print("画单台车的w0rtt的CDF图")
    # 如果不加','，报错
    # UserWarning: Legend does not support [<matplotlib.lines.Line2D object at 0x00000266279B1D08>] instances.
    # A proxy artist may be used instead.
    # See: http://matplotlib.org/users/legend_guide.html#creating-artists-specifically-for-adding-to-the-legend-aka-proxy-artists
    # loc='lower right')
    cdfW0pingrtt, = plt.plot(list(w0RttRatio), list(w0RttRatio.index), c='red')
    #####################################################
    #####################################################
    print("画单台车的w1rtt的CDF图")
    cdfW1pingrtt, = plt.plot(list(w1RttRatio), list(w1RttRatio.index), c='yellow')
    #####################################################
    #####################################################
    print("画单台车的w0rtt与w1rtt最小值的CDF图")
    cdfminW0AndW1, = plt.plot(list(minRttRatio), list(minRttRatio.index), c='blue')
    #####################################################
    #####################################################
    print("画单台车的srtt的CDF图")
    cdfsrtt, = plt.plot(list(srttRatio), list(srttRatio.index), c='green')
    #####################################################
    #####################################################
    print("设置标注")
    plt.legend([cdfW0pingrtt, cdfW1pingrtt, cdfminW0AndW1, cdfsrtt],
            ['WLAN0时延', 
             'WLAN1时延', 
             'min(WLAN0, WLAN1)时延', 
             'MPTCP时延'],
            loc='lower right')
    #####################################################
    #####################################################
    figName = os.path.join(tmpDir, '单台车的时延CDF' + '.png')
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第三阶段结束**********')
    ###############################################################################