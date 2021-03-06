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

# 一辆车的与发生停车事件任务相关的停车，掉线，漫游事件次数计算
def countSuspendAndDropAndHo(dfAndJobCsvFile):
    dfAndJobDf = pd.read_csv(dfAndJobCsvFile, na_filter=False)
    print('suspends={}'.format(len(list(filter(lambda e : e is not '', ''.join(dfAndJobDf['suspends'].values).split('|'))))))
    print('mptcpDrops={}'.format(len(list(filter(lambda e : e is not '', ''.join(dfAndJobDf['mptcpDrops'].values).split('|'))))))
    print('w0Drops={}'.format(len(list(filter(lambda e : e is not '', ''.join(dfAndJobDf['w0Drops'].values).split('|'))))))
    print('w1Drops={}'.format(len(list(filter(lambda e : e is not '', ''.join(dfAndJobDf['w1Drops'].values).split('|'))))))
    print('w0Hos={}'.format(len(list(filter(lambda e : e is not '', ''.join(dfAndJobDf['w0Hos'].values).split('|'))))))
    print('w1Hos={}'.format(len(list(filter(lambda e : e is not '', ''.join(dfAndJobDf['w1Hos'].values).split('|'))))))

# 提取data.csv数据看看左边通道处wlan0覆盖问题
def checkCorner(tmpPath):
    for i in range(1, 42):
        fileName = '30.113.151.' + str(i)
        print(fileName)
        csvPath = os.path.join(tmpPath, fileName)
        csvFile = os.path.join(csvPath, 'data.csv')
        if os.path.isdir(csvPath):
            df = pd.read_csv(csvFile)
            df[(df['curPosX'] >= 110) & (df['curPosX'] <= 126) \
             & (df['curPosY'] >= 49) & (df['curPosY'] <= 50)] \
                 .to_csv(os.path.join(os.path.join(csvPath, 'analysisApCover'), 'corner.csv'))


if __name__ == '__main__':
    # fileName = '/home/cx/Desktop/sdb-dir/tmp/30.113.151.1/analysisHandover/WLAN1漫游热力图统计数据.csv'
    # countHotMap(fileName)

    # deleteAnalysisDirList('analysisRtt')

    # tmpPath = '/home/cx/Desktop/sdb-dir/tmp/30.113.151.1'
    # outputDir = '/home/cx/Desktop'
    # checkJob(tmpPath, outputDir)

    # dfAndJobCsvFile = '/home/cx/Desktop/sdb-dir/tmp/30.113.151.1/analysisApp/dfAndJobDf.csv'
    # countSuspendAndDropAndHo(dfAndJobCsvFile)

    # tmpPath = '/home/cx/Desktop/sdb-dir/tmp'
    # checkCorner(tmpPath)