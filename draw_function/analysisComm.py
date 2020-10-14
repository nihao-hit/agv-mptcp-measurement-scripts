from matplotlib import pyplot as plt 
import seaborn as sns
import numpy as np
import pandas as pd 
import time
import datetime
import os
import sys
import math

# 画单台车的速度分析，分析任务
def drawComm(csvFile, tmpDir):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读取单台车的data.csv数据')
    commDf = pd.read_csv(csvFile, 
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
    ratio = np.arange(0, 1.01, 0.01)
    #####################################################
    print('准备速度CDF数据')
    speedRatio = commDf['speed'].quantile(ratio)
    #####################################################
    #####################################################
    print('分析任务')
    taskList = list(commDf[commDf['jobSn'] != 0].groupby('jobSn', sort=False))
    startTime = [task[1]['curTimestamp'].iloc[0] for task in taskList]
    endTime = [task[1]['curTimestamp'].iloc[-1] for task in taskList]

    curPosX = [task[1].iloc[0]['curPosX'] for task in taskList]
    curPosY = [task[1].iloc[0]['curPosY'] for task in taskList]

    destPosX = [task[1].iloc[-1]['destPosX'] for task in taskList]
    destPosY = [task[1].iloc[-1]['destPosY'] for task in taskList]
    
    taskDf = pd.DataFrame({'start' : startTime, 'end' : endTime, 
                           'curPosX' : curPosX, 'curPosY' : curPosY,
                           'destPosX' : destPosX, 'destPosY' : destPosY})
    taskDf['duration'] = taskDf['end'] - taskDf['start']
    taskDf['distance'] = taskDf.apply(lambda row : int(math.sqrt(
                                        pow(row['curPosX'] - row['destPosX'], 2) + 
                                        pow(row['curPosY'] - row['destPosY'], 2)
                                                                )),
                                      axis=1)
	
    print('为了方便人眼观察，为UNIX时间戳列添加日期时间列')
    taskDf['startDate'] = taskDf.apply(lambda row : datetime.datetime.fromtimestamp(row['start']), axis=1)
    taskDf['endDate'] = taskDf.apply(lambda row : datetime.datetime.fromtimestamp(row['end']), axis=1)
    #####################################################
    #####################################################
    print('准备任务耗时CDF数据')
    taskDurationRatio = taskDf['duration'].quantile(ratio)
    #####################################################
    #####################################################
    print('准备任务移动距离CDF数据')
    taskDistanceRatio = taskDf['distance'].quantile(ratio)
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将关键统计数据写入文件**********')
    #####################################################
    print('将任务统计信息写入文件')
    taskDf.to_csv(os.path.join(tmpDir, '任务统计信息.csv'))
    #####################################################
    #####################################################
    print('将速度CDF数据写入文件')
    speedRatio.to_csv(os.path.join(tmpDir, '速度CDF数据.csv'))
    #####################################################
    #####################################################
    print('将任务耗时CDF数据写入文件')
    taskDurationRatio.to_csv(os.path.join(tmpDir, '任务耗时CDF数据.csv'))
    #####################################################
    #####################################################
    print('将任务移动距离CDF数据写入文件')
    taskDistanceRatio.to_csv(os.path.join(tmpDir, '任务移动距离CDF数据.csv'))
    #####################################################
    print('**********第二阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第三阶段：画速度CDF图**********')
    #####################################################
    print("设置速度CDF坐标轴")
    plt.title('速度CDF图')
    plt.xlabel('AGV速度(m/s)')

    plt.ylim([0, 1])
    plt.yticks([i for i in np.arange(0.0, 1.1, 0.1)])
    #####################################################
    #####################################################
    plt.plot(list(speedRatio), list(speedRatio.index), c='red')
    
    plt.savefig(os.path.join(tmpDir, '速度CDF图.png'), dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第三阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第四阶段：画任务耗时CDF图**********')
    #####################################################
    print("设置任务耗时CDF坐标轴")
    plt.title('任务耗时CDF图')
    plt.xlabel('任务耗时(s)')

    plt.ylim([0, 1])
    plt.yticks([i for i in np.arange(0.0, 1.1, 0.1)])
    #####################################################
    #####################################################
    plt.plot(list(taskDurationRatio), list(taskDurationRatio.index), c='red')
    
    plt.savefig(os.path.join(tmpDir, '任务耗时CDF图.png'), dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第四阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第五阶段：画任务移动距离CDF图**********')
    #####################################################
    print("设置任务移动距离CDF坐标轴")
    plt.title('任务移动距离CDF图')
    plt.xlabel('任务移动距离(m)')

    plt.ylim([0, 1])
    plt.yticks([i for i in np.arange(0.0, 1.1, 0.1)])
    #####################################################
    #####################################################
    plt.plot(list(taskDistanceRatio), list(taskDistanceRatio.index), c='red')
    
    plt.savefig(os.path.join(tmpDir, '任务移动距离CDF图.png'), dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第五阶段结束**********')
    ###############################################################################