from matplotlib import pyplot as plt 
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np
import pandas as pd 
import time
import os
import math

# 数据文件空洞统计
def drawEmptyCDF(csvFileList, tmpDir, name):
    ###############################################################################
    print('**********第一阶段：准备数据**********')
    #####################################################
    print('读取所有csv文件，合并为一个dataframe')
    dfList = []
    for csvFile in csvFileList:
        df = pd.read_csv(csvFile)
        dfList.append(df)
    dfAll = pd.concat(dfList, ignore_index=True)
    #####################################################
    #####################################################
    print('构造缺失时段CDF数据')
    ratio = np.arange(0, 1.01, 0.01)
    holeRatio = dfAll['duration'].quantile(ratio)
    #####################################################
    print('**********第一阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第二阶段：将关键统计数据写入文件**********')
    #####################################################
    print('将所有车的csv文件空洞CDF信息写入文件')
    cdfFileName = '{}-cdf-{}-{}.csv'.format(name, len(dfAll), dfAll['duration'].sum())
    holeRatio.to_csv(os.path.join(tmpDir, cdfFileName))
    #####################################################
    print('**********第二阶段结束**********')
    ###############################################################################


    ###############################################################################
    print('**********第三阶段：画图**********')
    #####################################################
    print('画CDF图前的初始化：设置标题、坐标轴')
    plt.title('所有车的{}缺失时长CDF'.format(name))

    plt.xlim([1, 50])
    plt.ylim([0, 1])

    plt.xticks([1, 5, 10, 20, 30, 40, 50],
               ['1s', '5s', '10s', '20s', '30s', '40s', '50'])
    plt.yticks(np.arange(0, 1.1, 0.1))

    plt.xlabel('数据空洞时长'.format(name))
    #####################################################
    #####################################################
    print("画所有车的csv文件缺失时长CDF图")
    cdf, = plt.plot(list(holeRatio), list(holeRatio.index), c='red')
    #####################################################
    #####################################################
    print("设置标注")
    plt.legend([cdf],
            [name],
            loc='lower right')
    #####################################################
    #####################################################
    figName = os.path.join(tmpDir, '所有车的{}数据空洞时长CDF.png'.format(name))
    print('保存到：', figName)
    plt.savefig(figName, dpi=200)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################
    print('**********第三阶段结束**********')
    ###############################################################################