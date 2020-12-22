import pandas as pd
from collections import Counter
import os
import shutil

# 统计热力图不同热力值包含坐标数
def countHotMap(fileName):
    print('countHotMap() {}'.format(fileName))
    matrix = pd.read_csv(fileName).values.tolist()
    l = []
    for row in matrix:
        l += row
    for k, v in dict(Counter(l)).items():
        print('{} : {}'.format(k, v))

# 删除某单一分析文件夹
def deleteAnalysisDirList(analysisDirName):
    tmpPath = '/home/cx/Desktop/sdb-dir/tmp'
    for i in range(1, 42):
        fileName = '30.113.151.{}/{}'.format(i, analysisDirName)
        filePath = os.path.join(tmpPath, fileName)
        if os.path.isdir(filePath):
            print(filePath)
            # shutil.rmtree(filePath)

# merge data.csv and job.csv，输出dfAndJobDf.csv文件用于验证任务数据一致性
def checkJob(tmpPath, outputDir):
    #####################################################
    print('读取单台车的data.csv数据')
    df = pd.read_csv(os.path.join(tmpPath, 'data.csv'), 
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
    jobDf = pd.read_csv(os.path.join(tmpPath, 'job.csv'), 
                                usecols=['timestamp', 'status', 'jobId', 'bucketId', 
                                        'jobType', 'wayPointId'],
                                dtype={'timestamp' : int, 'status' : str, 
                                        'jobId' : int, 'bucketId' : int, 
                                        'jobType' : str, 'wayPointId' : int})
    #####################################################
    #####################################################
    print('输出dfAndJobDf.csv文件')
    dfAndJobDf = df.groupby('jobSn').first().reset_index()[['curTimestamp', 'jobSn']].merge(jobDf.groupby('jobId').first().reset_index()[['timestamp', 'jobId']], how='outer', left_on='jobSn', right_on='jobId').sort_values('timestamp')
    dfAndJobDf.to_csv(os.path.join(outputDir, 'dfAndJobDf.csv'))
    #####################################################


if __name__ == '__main__':
    # fileName = '/home/cx/Desktop/sdb-dir/tmp/30.113.151.1/analysisHandover/WLAN1漫游热力图统计数据.csv'
    # countHotMap(fileName)

    # deleteAnalysisDirList('analysisRtt')

    # tmpPath = '/home/cx/Desktop/sdb-dir/tmp/30.113.151.1'
    # outputDir = '/home/cx/Desktop'
    # checkJob(tmpPath, outputDir)