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
    


if __name__ == '__main__':
    # fileName = '/home/cx/Desktop/sdb-dir/tmp/30.113.151.1/analysisHandover/WLAN1漫游热力图统计数据.csv'
    # countHotMap(fileName)

    # deleteAnalysisDirList('analysisRtt')