from draw_function.analysisApCover import drawConnLevel, drawNotConnLevel, drawApCover
from draw_function.analysisDrop import drawDrop
from draw_function.analysisHandover import drawHandover, drawHandoverFineGrained
from draw_function.analysisRtt import analysisRtt, drawCDFForAllAgvData, drawCDFForOneAgvData
from draw_function.analysisMptcp import drawSubflowUseTime, drawMptcpInSubflow, drawMptcpInHandover
from draw_function.analysisComm import drawComm

from draw_function.analysisDataHole import drawEmptyCDF

import os

if __name__ == '__main__':
    # 显示中文
    import locale
    locale.setlocale(locale.LC_CTYPE, 'zh_CN.utf8')
    from pylab import *
    mpl.rcParams['font.sans-serif'] = ['SimHei']
    mpl.rcParams['axes.unicode_minus'] = False

    # ###############################################################################
    # print('**********第一阶段：单车数据统计**********')
    # for i in range(1, 2):
    #     fileName = '30.113.151.' + str(i)
    #     csvPath = os.path.join(r'/home/cx/Desktop/sdb-dir/tmp', fileName)
    #     csvFile = os.path.join(csvPath, 'data.csv')
    #     scanCsvFile = os.path.join(csvPath, 'scanData.csv')
    #     connCsvFile = os.path.join(csvPath, 'connData.csv')
    #     tcpprobeCsvFile = os.path.join(csvPath, 'tcpprobeData.csv')
    #     if os.path.isdir(csvPath):
            # #####################################################
            # print("掉线分析")
            # dropDir = os.path.join(csvPath, 'drop')
            # if not os.path.isdir(dropDir):
            #     os.makedirs(dropDir)
            # drawDropWithCoordinates(csvFile, dropDir)
            # #####################################################
            # #####################################################
            # print("漫游分析")
            # handoverDir = os.path.join(csvPath, 'analysisHandover')
            # if not os.path.isdir(handoverDir):
            #     os.makedirs(handoverDir)
            
            # print('画单台车的漫游热力图,漫游时长CDF,漫游时长分类柱状图,漫游类型分类柱状图,漫游SNR增益CDF')
            # drawHandover(csvFile, connCsvFile, handoverDir)

            # print('画漫游事件全景图，漫游事件SNR分析图　')
            # w0HoCsvFile = os.path.join(handoverDir, 'WLAN0漫游时段汇总.csv')
            # w1HoCsvFile = os.path.join(handoverDir, 'WLAN1漫游时段汇总.csv')
            # count = 10
            # drawHandoverFineGrained(w0HoCsvFile, w1HoCsvFile, csvFile, connCsvFile, handoverDir, count)
            # #####################################################
            # #####################################################
            # print('时延分析')
            # analysisRttDir = os.path.join(csvPath, 'analysisRtt')
            # print(analysisRttDir)
            # if not os.path.isdir(analysisRttDir):
            #     os.makedirs(analysisRttDir)
            # print("w0rtt，w1rtt，w0rtt与w1rtt最小值，srtt随时间分布散点图")
            # analysisRtt(csvFile, analysisRttDir)
            # print("w0rtt，w1rtt，w0rtt与w1rtt最小值，srtt的CDF")
            # drawCDFForOneAgvData(csvFile, analysisRttDir)
            # #####################################################
            # #####################################################
            # print('mptcp分析')
            # mptcpDir = os.path.join(csvPath, 'analysisMptcp')
            # print(mptcpDir)
            # if not os.path.isdir(mptcpDir):
            #     os.makedirs(mptcpDir)

            # print("统计当前子流状态变动")
            # drawSubflowUseTime(tcpprobeCsvFile, mptcpDir)

            # count = 10
            # w0HoCsvFile = os.path.join(csvPath, 'analysisHandover/WLAN0漫游时段汇总.csv')

            # print('分析连续使用子流的snd_nxt, snd_una, snd_cwnd, ssthresh, snd_wnd, rcv_wnd, srtt')
            # w0SubflowDurationCsvFile = os.path.join(mptcpDir, 'w0SubflowDuration.csv')
            # subflowLenTuple = [20 * 1000, 30 * 1000]
            # drawMptcpInSubflow(csvFile, tcpprobeCsvFile, w0SubflowDurationCsvFile, w0HoCsvFile, mptcpDir, subflowLenTuple, count)
            
            # print('分析漫游事件对应的子流的snd_nxt, snd_una, snd_cwnd, ssthresh, snd_wnd, rcv_wnd, srtt')
            # subflowLen = 30 * 1000
            # drawMptcpInHandover(csvFile, tcpprobeCsvFile, w0HoCsvFile, mptcpDir, subflowLen, count)
            # #####################################################
            # #####################################################
            # print('应用特征分析')
            # commDir = os.path.join(csvPath, 'analysisApp')
            # print(commDir)
            # if not os.path.isdir(commDir):
            #     os.makedirs(commDir)
            # print("粗粒度分析")
            # drawComm(csvFile, commDir)
            # #####################################################
    # print('**********第一阶段结束**********')
    # ###############################################################################
    
    
    # ###############################################################################
    # print('**********第二阶段：所有车数据统计**********')
    # #####################################################
    # print('构造文件夹')
    # topTmpPath = r'/home/cx/Desktop/sdb-dir/tmp'
    # topDataPath = r'/home/cx/Desktop/sdb-dir/'
    # # csvFile与scanCsvFile按顺序一一对应
    # csvFileList = [os.path.join(os.path.join(topTmpPath, path), 'data.csv') 
    #                for path in os.listdir(topTmpPath)
    #                if os.path.isfile(os.path.join(os.path.join(topTmpPath, path), 'data.csv'))]
    # scanCsvFileList = [os.path.join(os.path.split(f)[0], 'scanData.csv') for f in csvFileList]
    # #####################################################
    # #####################################################
    # print("基站覆盖分析")
    # apCoverDir = os.path.join(topDataPath, 'analysisApCover')
    # if not os.path.isdir(apCoverDir):
    #     os.makedirs(apCoverDir)

    # print('所有车数据的无线网卡连接基站的SNR分布CDF')
    # drawConnLevel(csvFileList, apCoverDir)

    # print('所有车数据的无线网卡未连接基站时观测到的基站最大SNR分布CDF')
    # drawNotConnLevel(csvFileList, apCoverDir)

    # print('所有车数据的基站覆盖热力图')
    # goodSNR = -70
    # drawApCover(goodSNR, scanCsvFileList, apCoverDir)
    # #####################################################
    # #####################################################
    # print("所有车数据的w0rtt，w1rtt，w0rtt与w1rtt最小值，srtt的CDF图")
    # cdfDir = os.path.join(topDataPath, 'cdfDir')
    # if not os.path.isdir(cdfDir):
    #     os.makedirs(cdfDir)
    # drawCDFForAllAgvData(csvFileList, cdfDir)
    # #####################################################
    # print('**********第二阶段结束**********')
    # ###############################################################################
    
    
    ###############################################################################
    print('**********第三阶段：所有车conn, ping, tcpprobe, comm文件空洞统计**********')
    #####################################################
    print('构造文件空洞统计的顶级文件夹')
    topTmpPath = r'/home/cx/Desktop/sdb-dir/tmp'
    topDataPath = r'/home/cx/Desktop/sdb-dir/'
    topHoleDir = os.path.join(topDataPath, 'topHoleDir')
    if not os.path.isdir(topHoleDir):
        os.makedirs(topHoleDir)
    
    holeDirList = [os.path.join(os.path.join(topTmpPath, path), 'fillDir')
                   for path in os.listdir(topTmpPath)
                   if os.path.isdir(os.path.join(os.path.join(topTmpPath, path), 'fillDir'))]
    #####################################################
    #####################################################
    print("所有车的WLAN0的conn文件的空洞CDF图")
    w0ConnHoleCsvFileList = [os.path.join(holeDir, f) for holeDir in holeDirList
                                                      for f in os.listdir(holeDir)
                                                      if 'w0ConnHole' in f]
    drawEmptyCDF(w0ConnHoleCsvFileList, topHoleDir, 'WLAN0的conn文件')
    
    print("所有车的WLAN0的ping文件的空洞CDF图")
    w0PingHoleCsvFileList = [os.path.join(holeDir, f) for holeDir in holeDirList
                                                      for f in os.listdir(holeDir)
                                                      if 'Ping151' in f]
    drawEmptyCDF(w0PingHoleCsvFileList, topHoleDir, 'WLAN0的ping文件')
    #####################################################
    #####################################################
    print("所有车的WLAN1的conn文件的空洞CDF图")
    w1ConnHoleCsvFileList = [os.path.join(holeDir, f) for holeDir in holeDirList
                                                      for f in os.listdir(holeDir)
                                                      if 'w1ConnHole' in f]
    drawEmptyCDF(w1ConnHoleCsvFileList, topHoleDir, 'WLAN1的conn文件')

    print("所有车的WLAN1的ping文件的空洞CDF图")
    w1PingHoleCsvFileList = [os.path.join(holeDir, f) for holeDir in holeDirList
                                                      for f in os.listdir(holeDir)
                                                      if 'Ping127' in f]
    drawEmptyCDF(w1PingHoleCsvFileList, topHoleDir, 'WLAN1的ping文件')
    #####################################################
    #####################################################
    print("所有车的tcpprobe文件的空洞CDF图")
    tcpprobeHoleCsvFileList = [os.path.join(holeDir, f) for holeDir in holeDirList
                                                        for f in os.listdir(holeDir)
                                                        if 'Tcpprobe' in f]
    drawEmptyCDF(tcpprobeHoleCsvFileList, topHoleDir, 'tcpprobe文件')

    print("所有车的comm文件的空洞CDF图")
    commHoleCsvFileList = [os.path.join(holeDir, f) for holeDir in holeDirList
                                                    for f in os.listdir(holeDir)
                                                    if 'Comm' in f]
    drawEmptyCDF(commHoleCsvFileList, topHoleDir, 'comm文件')
    #####################################################
    print('**********第三阶段结束**********')
    ###############################################################################