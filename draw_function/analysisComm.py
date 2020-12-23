# drawApplication : 画分类任务时长与距离直方图
from matplotlib import pyplot as plt 
import seaborn as sns
import numpy as np
import pandas as pd 
import time
import datetime
import os
import sys
import math

# 画分类任务时长与距离直方图
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

            print("画分类任务时长与距离直方图")
            drawApplication(csvFile, jobCsvFile, appDir)
    #####################################################
    print('**********应用日志分析阶段结束**********')
    ###############################################################################