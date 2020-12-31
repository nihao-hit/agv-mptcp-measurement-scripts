# drawApplication : 画分类任务时长与距离直方图，任务轨迹图
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
import seaborn as sns
import numpy as np
import pandas as pd 
import time
import datetime
import os
import sys
import math

# 画分类任务时长与距离直方图，任务轨迹图
def drawApplication(csvFile, jobCsvFile, appDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读取单台车的data.csv数据')
    df = pd.read_csv(csvFile, 
                                 usecols=['agvCode', 'dspStatus', 'destPosX', 'destPosY', 
                                          'curPosX', 'curPosY', 'curTimestamp', 'direction', 
                                          'speed', 'withBucket', 'jobSn'],
                                 dtype={'agvCode' : str, 'dspStatus' : str, 
                                        'destPosX' : int, 'destPosY' : int, 
                                        'curPosX' : int, 'curPosY' : int, 
                                        'curTimestamp' : int, 'direction' : float, 
                                        'speed' : float, 'withBucket' : int, 
                                        'jobSn' : int},
                                 na_filter=False)
    #####################################################
    #####################################################
    print('读取单台车的job.csv数据')
    jobDf = pd.read_csv(jobCsvFile, 
                                 usecols=['timestamp', 'status', 'jobId', 'bucketId', 
                                          'jobType', 'wayPointId'],
                                 dtype={'timestamp' : int, 'status' : str, 
                                        'jobId' : int, 'bucketId' : int, 
                                        'jobType' : str, 'wayPointId' : int})
    #####################################################
    #####################################################
    print('分析任务')
    # 1.为方便后续处理，保留我们感兴趣的df列；2.分组df；3.提取每个分组的第一行与最后一行；4.将jobSn从index转为column；
    # 5.将jobDf分组并保留分组第一行，然后将jobId从index转为column；
    # 6.left join df and jobDf，因为df时段可能由于其他测量数据而被截短；
    # 7.重置dfAndJobDf列标签；
    # 8.drop不需要的列，过滤jobId=0的非任务
    dfAndJobDf = df[['jobSn', 'curTimestamp', 'curPosX', 'curPosY', 'destPosX', 'destPosY']] \
                   .groupby('jobSn').agg(['first', 'last']).reset_index()   \
                   .merge(jobDf.groupby('jobId').first().reset_index(), how='left', left_on='jobSn', right_on='jobId')
    dfAndJobDf.columns = ['jobId', 'startTs', 'endTs', 'startPosX', '_1', 
                          'startPosY', '_2', '_3', 'endPosX', '_4', 'endPosY', 
                          '_5', '_6', '_7', 'bucketId', 'jobType', 'wayPointId']
    dfAndJobDf = dfAndJobDf.drop(['_1','_2', '_3', '_4', '_5', '_6', '_7'], axis=1)[dfAndJobDf['jobId'] != 0]
    #####################################################
    #####################################################
    print('构造时长与距离列，按jobType分类任务')
    dfAndJobDf['duration'] = dfAndJobDf['endTs'] - dfAndJobDf['startTs']
    dfAndJobDf['distance'] = dfAndJobDf.apply(lambda row : int(math.sqrt(
                                              pow(row['startPosX'] - row['endPosX'], 2) + 
                                              pow(row['startPosY'] - row['endPosY'], 2)
                                                                        )),
                                              axis=1)
    jobDict = dict(list(dfAndJobDf.groupby('jobType')))
    moveJob = jobDict['Move']
    bucketMoveJob = jobDict['BucketMove']
    chargeJob = jobDict['Charge']
    #####################################################
    #####################################################
    print('关注分类任务中的经历时长离群点')
    slowMoveJob = moveJob[moveJob['duration'] >= moveJob['duration'].quantile(0.9)]
    slowBucketMoveJob = bucketMoveJob[bucketMoveJob['duration'] >= bucketMoveJob['duration'].quantile(0.9)]
    slowChargeJob = chargeJob[chargeJob['duration'] >= chargeJob['duration'].quantile(0.9)]
    #####################################################
    #####################################################
    print('非图表型统计数据构造')
    staticsFile = os.path.join(appDir, 'statics.csv')
    statics = dict()
    if os.path.isfile(staticsFile):
        statics = pd.read_csv(staticsFile).to_dict('list')

    # 数据总数，时间跨度，时间粒度
    statics['任务数'] = len(dfAndJobDf)
    statics['Move任务数'] = len(moveJob)
    statics['BucketMove任务数'] = len(bucketMoveJob)
    statics['Charge任务数'] = len(chargeJob)
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将关键统计数据写入文件**********')
    #####################################################
    print('将任务统计信息写入文件')
    dfAndJobDf.to_csv(os.path.join(appDir, 'dfAndJobDf.csv'))
    #####################################################
    #####################################################
    print('将分类任务中的经历时长离群点统计信息写入文件')
    slowMoveJob.to_csv(os.path.join(appDir, 'slowMoveJob.csv'))
    slowBucketMoveJob.to_csv(os.path.join(appDir, 'slowBucketMoveJob.csv'))
    slowChargeJob.to_csv(os.path.join(appDir, 'slowChargeJob.csv'))
    #####################################################
    #####################################################
    print('将非图表型统计数据写入文件')
    pd.DataFrame(statics, index=[0]).to_csv(os.path.join(appDir, 'statics.csv'))
    #####################################################
    print('**********第二阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第三阶段：画分类任务时长与距离直方图**********')
    #####################################################
    fig, ((moveDrtAx, moveDstAx), 
        (bucketDrtAx, bucketDstAx), 
        (chargeDrtAx, chargeDstAx)) = plt.subplots(3, 2)
    #####################################################
    #####################################################
    print("画moveJob时长直方图")
    bins = list(map(int, np.linspace(moveJob['duration'].min(), moveJob['duration'].max(), 20)))
    moveDrtAx.set_xticks(bins[::2])
    # 旋转xlabels
    moveDrtAx.tick_params(axis='x', labelrotation=45)
    # 设置xlabel
    moveDrtAx.set_xlabel('moveJob/duration (s)')
    moveDrtAx.hist(list(moveJob['duration']), bins=bins)

    print("画moveJob距离直方图")
    bins = list(map(int, np.linspace(moveJob['distance'].min(), moveJob['distance'].max(), 20)))
    moveDstAx.set_xticks(bins[::2])
    # 旋转xlabels
    moveDstAx.tick_params(axis='x', labelrotation=45)
    # 设置xlabel
    moveDstAx.set_xlabel('moveJob/distance (m)')
    moveDstAx.hist(list(moveJob['distance']), bins=bins)
    #####################################################
    #####################################################
    print("画bucketMoveJob时长直方图")
    bins = list(map(int, np.linspace(bucketMoveJob['duration'].min(), bucketMoveJob['duration'].max(), 20)))
    bucketDrtAx.set_xticks(bins[::2])
    # 旋转xlabels
    bucketDrtAx.tick_params(axis='x', labelrotation=45)
    # 设置xlabel
    bucketDrtAx.set_xlabel('bucketMoveJob/duration (s)')
    bucketDrtAx.hist(list(bucketMoveJob['duration']), bins=bins)

    print("画bucketMoveJob距离直方图")
    bins = list(map(int, np.linspace(bucketMoveJob['distance'].min(), bucketMoveJob['distance'].max(), 20)))
    bucketDstAx.set_xticks(bins[::2])
    # 旋转xlabels
    bucketDstAx.tick_params(axis='x', labelrotation=45)
    # 设置xlabel
    bucketDstAx.set_xlabel('bucketMoveJob/distance (m)')
    bucketDstAx.hist(list(bucketMoveJob['distance']), bins=bins)
    #####################################################
    #####################################################
    print("画chargeJob时长直方图")
    bins = list(map(int, np.linspace(chargeJob['duration'].min(), chargeJob['duration'].max(), 20)))
    chargeDrtAx.set_xticks(bins[::2])
    # 旋转xlabels
    chargeDrtAx.tick_params(axis='x', labelrotation=45)
    # 设置xlabel
    chargeDrtAx.set_xlabel('chargeJob/duration (s)')
    chargeDrtAx.hist(list(chargeJob['duration']), bins=bins)

    print("画chargeJob距离直方图")
    bins = list(map(int, np.linspace(chargeJob['distance'].min(), chargeJob['distance'].max(), 20)))
    chargeDstAx.set_xticks(bins[::2])
    # 旋转xlabels
    chargeDstAx.tick_params(axis='x', labelrotation=45)
    # 设置xlabel
    chargeDstAx.set_xlabel('chargeJob/distance (m)')
    chargeDstAx.hist(list(chargeJob['distance']), bins=bins)
    #####################################################
    #####################################################
    # 设置标题
    fig.suptitle("分类任务时长与距离直方图")

    # 减小字体
    plt.rcParams.update({'font.size': 5})

    # 调整图像避免截断xlabel
    fig.tight_layout()

    fig.savefig(os.path.join(appDir, '分类任务时长与距离直方图.png'), dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第三阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第四阶段：画分类任务轨迹图**********')
    #####################################################
    jobDataDict = dict(list(df[df['jobSn'] != 0].groupby('jobSn')))
    
    print('创建slow.*JobDir')
    slowMoveJobDir = os.path.join(appDir, 'slowMoveJob')
    if not os.path.isdir(slowMoveJobDir):
        os.makedirs(slowMoveJobDir)
    slowBucketMoveJobDir = os.path.join(appDir, 'slowBucketMoveJob')
    if not os.path.isdir(slowBucketMoveJobDir):
        os.makedirs(slowBucketMoveJobDir)
    slowChargeJobDir = os.path.join(appDir, 'slowChargeJob')
    if not os.path.isdir(slowChargeJobDir):
        os.makedirs(slowChargeJobDir)
    
    def drawJobTrack(jobId, outputDir):
        ax = plt.gca()
        # 逆置Y轴
        ax.invert_yaxis()
        ax.set_xlim([0, 264])
        ax.set_ylim([0, 138])
        ax.set_title('{}/{}'.format(os.path.split(outputDir)[1], jobId))
        sns.scatterplot(data=jobDataDict[row['jobId']], x="curPosX", y="curPosY", hue="curTimestamp", ax=ax, s=2)

        plt.savefig(os.path.join(outputDir, '{}.png'.format(jobId)), dpi=200)
        plt.pause(1)
        plt.close()
        plt.pause(1)
    #####################################################
    #####################################################
    print('画moveJob的经历时长离群点任务轨迹图')
    for _, row in slowMoveJob.iterrows():
        print('slowMoveJob : {}'.format(row['jobId']))
        drawJobTrack(row['jobId'], slowMoveJobDir)
        
    print('画bucketMoveJob的经历时长离群点任务轨迹图')
    for _, row in slowBucketMoveJob.iterrows():
        print('slowBucketMoveJob : {}'.format(row['jobId']))
        drawJobTrack(row['jobId'], slowBucketMoveJobDir)

    print('画chargeJob的经历时长离群点任务轨迹图')
    for _, row in slowChargeJob.iterrows():
        print('slowChargeJob : {}'.format(row['jobId']))
        drawJobTrack(row['jobId'], slowChargeJobDir)
    #####################################################
    print('**********第四阶段结束**********')
    ###############################################################################




def drawNine(csvFile, jobMetaCsvFile, notifyCsvFile,
             w0HoCsvFile, w0DropCsvFile, w0NoGoodApCoverCsvFile,
             w1HoCsvFile, w1DropCsvFile, w1NoGoodApCoverCsvFile,
             mptcpDropCsvFile, w1ApCountCsvFile, 
             mptcpCsvFile, subflowCsvFile, 
             appDir):
    #####################################################
    print('读入任务元数据与全部时刻数据')
    df = pd.read_csv(csvFile, dtype={'W0APMac':str, 'W1APMac':str, 'src':str}, na_filter=False)
    jobMetaDf = pd.read_csv(jobMetaCsvFile)
    # 作为热力图背景
    w1ApCountDf = pd.read_csv(w1ApCountCsvFile, header=None).astype(bool).astype(int)
    # 停车事件
    suspendDf = pd.read_csv(notifyCsvFile)
    suspendDf = suspendDf[suspendDf['type'] == 'AGV_SUSPEND']
    
    # mptcp连接及subflow存在指示
    mptcpDf = pd.read_csv(mptcpCsvFile, usecols=['mptcpNum', 'connStats', 'originMptcpFirstTs', 'originMptcpLastTs'],
                                        dtype={'connStats':str})
    mptcpDf = mptcpDf[mptcpDf.connStats.str.contains('7070')]
    mptcpDf['originMptcpFirstTs'] = mptcpDf['originMptcpFirstTs'] / 1e3
    mptcpDf['originMptcpLastTs'] = mptcpDf['originMptcpLastTs'] / 1e3
    
    subflowDf = pd.read_csv(subflowCsvFile, usecols=['subStats', 'originSubFirstTs', 'originSubLastTs'],
                                            dtype={'subStats':str})
    subflowDf = subflowDf[subflowDf.subStats.str.contains('7070')]
    subflowDf['originSubFirstTs'] = subflowDf['originSubFirstTs'] / 1e3
    subflowDf['originSubLastTs'] = subflowDf['originSubLastTs'] / 1e3
    #####################################################
    #####################################################
    # 2020/12/31:10: 记录任务及关联mptcp连接，停车，掉线，漫游事件
    jobMetaDf['mptcpNums'] = ''
    jobMetaDf['suspends'] = ''
    jobMetaDf['mptcpDrops'] = ''
    jobMetaDf['w0Drops'] = ''
    jobMetaDf['w1Drops'] = ''
    jobMetaDf['w0Hos'] = ''
    jobMetaDf['w1Hos'] = ''
    #####################################################
    #####################################################
    print('构造文件夹')
    figDir = os.path.join(appDir, '{}NineFig'.format(os.path.split(jobMetaCsvFile)[1][:-4]))
    if not os.path.isdir(figDir):
        os.makedirs(figDir)
    #####################################################
    #####################################################
    for _, jobRow in jobMetaDf.iterrows():
        print('jobId : {}'.format(jobRow['jobId']))
        fig, ((jobTrackAx, dropAx, hoAx), 
              (noGoodApCoverAx, w0RssiAx, w1RssiAx), 
              (srttAx, w0PingRttAx, w1PingRttAx)) = plt.subplots(3, 3)
        #####################################################
        #####################################################
        print('画任务轨迹图')
        # 添加仓库轮廓背景
        sns.heatmap(data=w1ApCountDf, cbar=False, cmap='Blues', vmax=20, ax=jobTrackAx)

        jobTrackAx.set_title('任务轨迹图')
        # 2020/12/31:13: 将任务时间序列数据提取条件从jobId修改为指定时段，因为任务进行时jobId可能为0.
        jobDf = df[(df['curTimestamp'] >= jobRow['startTs']) & 
                   (df['curTimestamp'] <= jobRow['endTs'])]
        jobTrackAx.set_xlim([0, 264])
        jobTrackAx.set_ylim([0, 138])
        sns.scatterplot(data=jobDf, x='curPosX', y='curPosY', hue='curTimestamp', ax=jobTrackAx, s=1)
        
        # 添加停车事件
        for _, row in suspendDf.iterrows():
            tmpDf = jobDf[jobDf['curTimestamp'] == row['timestamp']]
            if len(tmpDf) == 1:
                suspendPosX = tmpDf['curPosX'].max()
                suspendPosY = tmpDf['curPosY'].max()
                jobTrackAx.plot([suspendPosX], [suspendPosY], marker='o', ms=2)
                jobTrackAx.annotate('AGV_SUSPEND', xy=(suspendPosX, suspendPosY), xytext=(0.9, 0.9),
                                    textcoords='axes fraction',
                                    arrowprops=dict(arrowstyle='->'))
                # 2020/12/31:10: 记录任务及关联mptcp连接，停车，掉线，漫游事件
                jobMetaDf.loc[jobMetaDf['jobId'] == jobRow['jobId'], 'suspends'] += '{}|'.format(row['timestamp'])
        #####################################################
        #####################################################
        print('画掉线热力图')
        # 添加仓库轮廓背景
        sns.heatmap(data=w1ApCountDf, cbar=False, cmap='Blues', vmax=20, ax=dropAx)

        dropAx.set_title('掉线热力图')
        mptcpDropDf = pd.read_csv(mptcpDropCsvFile)
        mptcpDropDf = mptcpDropDf[(mptcpDropDf['curTimestamp'] >= jobDf['curTimestamp'].min()) & 
                                  (mptcpDropDf['curTimestamp'] <= jobDf['curTimestamp'].max())]
        mptcpDropDf['type'] = 'mptcp'

        w0DropDf = pd.read_csv(w0DropCsvFile)
        w0DropDf = w0DropDf[(w0DropDf['curTimestamp'] >= jobDf['curTimestamp'].min()) & 
                            (w0DropDf['curTimestamp'] <= jobDf['curTimestamp'].max())]
        w0DropDf['type'] = 'wlan0'

        w1DropDf = pd.read_csv(w1DropCsvFile)
        w1DropDf = w1DropDf[(w1DropDf['curTimestamp'] >= jobDf['curTimestamp'].min()) & 
                            (w1DropDf['curTimestamp'] <= jobDf['curTimestamp'].max())]
        w1DropDf['type'] = 'wlan1'

        dropDf = pd.concat([mptcpDropDf, w0DropDf, w1DropDf], ignore_index=True)
        
        dropAx.set_xlim([0, 264])
        dropAx.set_ylim([0, 138])
        try:
            sns.scatterplot(data=dropDf, x='curPosX', y='curPosY', hue='type', ax=dropAx, s=1)
        except:
            pass
        # 2020/12/31:10: 记录任务及关联mptcp连接，停车，掉线，漫游事件
        for _, row in dropDf.iterrows():
            keyDict = {'mptcp':'mptcpDrops', 'wlan0':'w0Drops', 'wlan1':'w1Drops'}
            key = keyDict[row['type']]
            jobMetaDf.loc[jobMetaDf['jobId'] == jobRow['jobId'], key] += '{}|'.format(row['curTimestamp'])
        #####################################################
        #####################################################
        print('画漫游热力图')
        # 添加仓库轮廓背景
        sns.heatmap(data=w1ApCountDf, cbar=False, cmap='Blues', vmax=20, ax=hoAx)

        hoAx.set_title('漫游热力图')
        w0HoDf = pd.read_csv(w0HoCsvFile)
        w0HoDf = w0HoDf[(w0HoDf['start'] / 1e3 >= jobDf['curTimestamp'].min()) & 
                        (w0HoDf['start'] / 1e3 <= jobDf['curTimestamp'].max())]
        w0HoDf['type'] = 'wlan0'
        
        w1HoDf = pd.read_csv(w1HoCsvFile)
        w1HoDf = w1HoDf[(w1HoDf['start'] / 1e3 >= jobDf['curTimestamp'].min()) & 
                        (w1HoDf['start'] / 1e3 <= jobDf['curTimestamp'].max())]
        w1HoDf['type'] = 'wlan1'

        hoDf = pd.concat([w0HoDf, w1HoDf], ignore_index=True)
        hoDf.rename(columns={'posX': 'curPosX', 'posY': 'curPosY'}, inplace=True)

        hoAx.set_xlim([0, 264])
        hoAx.set_ylim([0, 138])
        try:
            sns.scatterplot(data=hoDf, x='curPosX', y='curPosY', hue='type', ax=hoAx, s=1)
        except:
            pass
        # 2020/12/31:10: 记录任务及关联mptcp连接，停车，掉线，漫游事件
        for _, row in hoDf.iterrows():
            keyDict = {'wlan0':'w0Hos', 'wlan1':'w1Hos'}
            key = keyDict[row['type']]
            jobMetaDf.loc[jobMetaDf['jobId'] == jobRow['jobId'], key] += '{}|'.format(row['start'])
        #####################################################
        #####################################################
        print('画有效基站覆盖空白热力图')
        # 添加仓库轮廓背景
        sns.heatmap(data=w1ApCountDf, cbar=False, cmap='Blues', vmax=20, ax=noGoodApCoverAx)

        noGoodApCoverAx.set_title('有效基站覆盖空白热力图')
        w0NoGoodApCoverDf = pd.read_csv(w0NoGoodApCoverCsvFile, header=None)
        w0NoGoodApCoverDf.columns = ['curPosX', 'curPosY']
        w0NoGoodApCoverDf['type'] = 'wlan0'

        w1NoGoodApCoverDf = pd.read_csv(w1NoGoodApCoverCsvFile, header=None)
        w1NoGoodApCoverDf.columns = ['curPosX', 'curPosY']
        w1NoGoodApCoverDf['type'] = 'wlan1'

        noGoodApCoverDf = pd.concat([w0NoGoodApCoverDf, w1NoGoodApCoverDf], ignore_index=True)

        noGoodApCoverAx.set_xlim([0, 264])
        noGoodApCoverAx.set_ylim([0, 138])
        sns.scatterplot(data=noGoodApCoverDf, x='curPosX', y='curPosY', hue='type', ax=noGoodApCoverAx, s=1)
        #####################################################
        #####################################################
        print('画wlan0网络连接基站rssi折线图')
        w0RssiAx.set_title('wlan0网络连接基站rssi折线图')
        w0RssiAx.set_ylabel('rssi (dBm)')
        w0RssiAx.get_yaxis().set_major_locator(MaxNLocator(integer=True))
        # 过滤零值
        w0RssiDf = jobDf[jobDf['W0level'] != 0]

        sns.lineplot(data=w0RssiDf, x='curTimestamp', y='W0level', hue='W0APMac', ax=w0RssiAx, lw=0.5)
        # 添加漫游事件
        for _, row in w0HoDf.iterrows():
            w0RssiAx.axvspan(row['start'] / 1e3, row['end'] / 1e3, alpha=0.3)
        #####################################################
        #####################################################
        print('画wlan1网络连接基站rssi折线图')
        w1RssiAx.set_title('wlan1网络连接基站rssi折线图')
        w1RssiAx.set_ylabel('rssi (dBm)')
        w1RssiAx.get_yaxis().set_major_locator(MaxNLocator(integer=True))
        # 过滤零值
        w1RssiDf = jobDf[jobDf['W1level'] != 0]

        sns.lineplot(data=w1RssiDf, x='curTimestamp', y='W1level', hue='W1APMac', ax=w1RssiAx, lw=0.5)
        # 添加漫游事件
        for _, row in w1HoDf.iterrows():
            w1RssiAx.axvspan(row['start'] / 1e3, row['end'] / 1e3, alpha=0.3)
        #####################################################
        #####################################################
        print('画mptcp时延折线图')
        srttAx.set_title('mptcp时延折线图')
        srttAx.set_ylabel('srtt (ms)')
        # 过滤src==''
        srttDf = jobDf[jobDf['src'] != '']

        srttDf['src'] = srttDf.apply(lambda row : 'wlan0:{}'.format(row['srcPort']) 
                                                  if '151' in row['src'] 
                                                  else 'wlan1:{}'.format(row['srcPort']), axis=1)
        sns.lineplot(data=srttDf, x='curTimestamp', y='srtt', hue='src', style='src', markers=True, ms=2, alpha=0.5, ax=srttAx, lw=0.5)
        # 添加掉线事件
        for _, row in mptcpDropDf.iterrows():
            srttAx.axvspan(row['curTimestamp'], row['curTimestamp']+1, alpha=0.3)
        
        # 添加mptcp连接及subflow存在指示
        srttAx2 = srttAx.twinx()
        jobStart, jobEnd = jobDf['curTimestamp'].min(), jobDf['curTimestamp'].max()
        
        srttAx2.set_xlim([jobStart, jobEnd])
        srttAx2.get_yaxis().set_major_locator(MaxNLocator(integer=True))
        srttAx2.set_yticks(range(4))
        srttAx2.set_yticklabels(['', 'sub-wlan1', 'sub-wlan0', 'mptcp'])
        
        for _, mptcpRow in mptcpDf.iterrows():
            mptcpStart, mptcpEnd = mptcpRow['originMptcpFirstTs'], mptcpRow['originMptcpLastTs']
            if mptcpStart > jobStart and mptcpStart < jobEnd or \
               mptcpEnd > jobStart and mptcpEnd < jobEnd or \
               mptcpStart <= jobStart and mptcpEnd >= jobEnd:
            
                srttAx2.plot([mptcpStart, mptcpEnd], [3, 3], alpha=0.5)
                # 2020/12/31:10: 记录任务及关联mptcp连接，停车，掉线，漫游事件
                jobMetaDf.loc[jobMetaDf['jobId'] == jobRow['jobId'], 'mptcpNums'] += '{}|'.format(mptcpRow['mptcpNum'])
        for _, subRow in subflowDf.iterrows():
            y = [0, 0]
            if '151' in subRow['subStats']:
                y = [2, 2]
            else:
                y = [1, 1]
            srttAx2.plot([subRow['originSubFirstTs'], subRow['originSubLastTs']], y, alpha=0.5)
        #####################################################
        #####################################################
        print('画wlan0网络时延折线图')
        w0PingRttAx.set_title('wlan0网络时延折线图')
        w0PingRttAx.set_ylabel('pingRtt (ms)')
        sns.lineplot(data=jobDf, x='curTimestamp', y='W0pingrtt', ax=w0PingRttAx, lw=0.5)
        # 添加掉线事件
        for _, row in w0DropDf.iterrows():
            w0PingRttAx.axvspan(row['curTimestamp'], row['curTimestamp']+1, alpha=0.3)
        #####################################################
        #####################################################
        print('画wlan1网络时延折线图')
        w1PingRttAx.set_title('wlan1网络时延折线图')
        w1PingRttAx.set_ylabel('pingRtt (ms)')
        sns.lineplot(data=jobDf, x='curTimestamp', y='W1pingrtt', ax=w1PingRttAx, lw=0.5)
        # 添加掉线事件
        for _, row in w1DropDf.iterrows():
            w1PingRttAx.axvspan(row['curTimestamp'], row['curTimestamp']+1, alpha=0.3)
        #####################################################
        #####################################################     
        # 设置标题
        fig.suptitle("AGV跨层分析图")

        # 减小字体
        plt.rcParams.update({'font.size': 4})

        # 调整图像避免截断xlabel
        fig.tight_layout()

        fig.savefig(os.path.join(figDir, '{}.png'.format(jobRow['jobId'])), dpi=200)
        plt.pause(1)
        plt.close()
        plt.pause(1)
        #####################################################     
    #####################################################     
    print('修改后的jobMetaDf写回文件')
    jobMetaDf.to_csv(jobMetaCsvFile)
    #####################################################     




if __name__ == '__main__':
    # 显示中文
    import locale
    locale.setlocale(locale.LC_CTYPE, 'zh_CN.utf8')
    from pylab import *
    mpl.rcParams['font.sans-serif'] = ['SimHei']
    mpl.rcParams['axes.unicode_minus'] = False

    ###############################################################################
    print('**********应用日志分析阶段**********')
    #####################################################
    for i in range(1, 42):
        fileName = '30.113.151.' + str(i)
        print(fileName)
        csvPath = os.path.join(r'/home/cx/Desktop/sdb-dir/tmp', fileName)
        csvFile = os.path.join(csvPath, 'data.csv')
        jobCsvFile = os.path.join(csvPath, 'job.csv')
        if os.path.isdir(csvPath):
            print('应用日志分析')
            appDir = os.path.join(csvPath, 'analysisApp')
            if not os.path.isdir(appDir):
                os.makedirs(appDir)

            print("画分类任务时长与距离直方图，任务轨迹图")
            drawApplication(csvFile, jobCsvFile, appDir)

            print('画AGV跨层分析图')
            topPath = os.path.split(os.path.split(csvPath)[0])[0]
            dataAndJobCsvFile = os.path.join(appDir, 'dfAndJobDf.csv')
            slowMoveJobCsvFile = os.path.join(appDir, 'slowMoveJob.csv')
            slowBucketMoveJobCsvFile = os.path.join(appDir, 'slowBucketMoveJob.csv')
            slowChargeJobCsvFile = os.path.join(appDir, 'slowChargeJob.csv')
            notifyCsvFile = os.path.join(csvPath, 'notification.csv')

            w0HoCsvFile = os.path.join(csvPath, 'analysisHandover/WLAN0漫游时段汇总.csv')
            w0DropCsvFile = os.path.join(csvPath, 'analysisDrop/wlan0单网络掉线时刻.csv')
            w0NoGoodApCoverCsvFile = os.path.join(topPath, 'analysisApCover/w0NoGoodApCover.csv')

            w1HoCsvFile = os.path.join(csvPath, 'analysisHandover/WLAN1漫游时段汇总.csv')
            w1DropCsvFile = os.path.join(csvPath, 'analysisDrop/wlan1单网络掉线时刻.csv')
            w1NoGoodApCoverCsvFile = os.path.join(topPath, 'analysisApCover/w1NoGoodApCover.csv')

            mptcpDropCsvFile = os.path.join(csvPath, 'analysisDrop/双网络+mptcp实际掉线时刻.csv')
            w1ApCountCsvFile = os.path.join(topPath, 'analysisApCover/w1apCount.csv')
            
            mptcpCsvFile = os.path.join(csvPath, 'mptcpData.csv')
            subflowCsvFile = os.path.join(csvPath, 'subflowData.csv')
            drawNine(csvFile, dataAndJobCsvFile, notifyCsvFile,
                     w0HoCsvFile, w0DropCsvFile, w0NoGoodApCoverCsvFile,
                     w1HoCsvFile, w1DropCsvFile, w1NoGoodApCoverCsvFile,
                     mptcpDropCsvFile, w1ApCountCsvFile, 
                     mptcpCsvFile, subflowCsvFile, 
                     appDir)
    #####################################################
    print('**********应用日志分析阶段结束**********')
    ###############################################################################