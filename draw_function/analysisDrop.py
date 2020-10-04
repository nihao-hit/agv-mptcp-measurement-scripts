from matplotlib import pyplot as plt 
import seaborn as sns
import numpy as np
import pandas as pd 
import time
import os

# 
def drawDrop(csvFile, tmpDir):
    df = pd.read_csv(csvFile, usecols=['curTimestamp', 'W0pingrtt', 'W1pingrtt', 'srtt',
                                       'curPosX', 'curPosY'],
                              dtype={'curTimestamp' : int, 
                                     'W0pingrtt' : int, 
                                     'W1pingrtt' : int,
                                     'srtt' : int,
                                     'curPosX' : int,
                                     'curPosY' : int})
    curTimestamp = df['curTimestamp']
    curPosX = df['curPosX']
    curPosY = df['curPosY']
    W0pingrtt = df['W0pingrtt']
    W1pingrtt = df['W1pingrtt']
    minW0AndW1 = [min(W0pingrtt[i], W1pingrtt[i]) for i in range(len(W0pingrtt))]
    srtt = df['srtt']

    ###################################################################
    print("统计w0pingrtt超时30s的掉线")
    # curPosX为列下标，curPosY为行下标
    w0DropList = [[0]*265 for _ in range(139)]
    w0DropSeq = []
    i = 0
    while i < len(W0pingrtt):
        if W0pingrtt[i] >= 30000:
            tmp = [curPosX[i], curPosY[i]]
            w0DropSeq.append(i)
            # 只记录超时30s后的第一个坐标
            while i < len(W0pingrtt) and W0pingrtt[i] >= 30000:
                i += 1
            # 删除（0，0）处的统计数据
            if tmp[0] == 0 and tmp[1] == 0:
                pass
            else:
                w0DropList[tmp[1]][tmp[0]] += 1
        i += 1
    
    with open(os.path.join(tmpDir, 'w0-drop.csv'), 'w') as f:
        f.write('{},{},{}\n'.format('curTimestamp', 'curPosX', 'curPosY'))
        for i in range(len(w0DropSeq)):
            f.write('{},{},{}\n'.format(curTimestamp[w0DropSeq[i]], 
                curPosX[w0DropSeq[i]], 
                curPosY[w0DropSeq[i]]))

    plt.xlim([0, 264])
    plt.ylim([0, 138])

    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 6.0)

    ax = sns.heatmap(w0DropList, cmap="Blues")
    
    # 逆置Y轴
    ax.invert_yaxis()

    plt.savefig(os.path.join(tmpDir, 'w0-drop.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################################


    ############################################
    # 不知道为什么画第一个图长宽比总是不起作用，所以只好画两次
    print("抵消第一个图长宽比不起作用的bug，画两次")
    plt.title('w0-drop')
    plt.xlim([0, 264])
    plt.ylim([0, 138])

    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 6.0)

    # w0掉线次数就几个，颜色条刻度直接按1递增就行
    cbarMaxTick = max(map(max,w0DropList))
    ax = sns.heatmap(w0DropList, cmap="Blues", vmin=0,
                     cbar_kws={'ticks':range(0, cbarMaxTick+1)})

    # # 设置颜色条
    # cbar = ax.collections[0].colorbar
    # cbar.set_ticks([0, .2, .75, 1])
    # cbar.set_ticklabels(['low', '20%', '75%', '100%'])

    # 逆置Y轴
    ax.invert_yaxis()

    plt.savefig(os.path.join(tmpDir, 'w0-drop.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    ############################################


    ###################################################################
    print("统计w1pingrtt超时30s的掉线")
    # curPosX为列下标，curPosY为行下标
    w1DropList = [[0]*265 for _ in range(139)]
    w1DropSeq = []
    i = 0
    while i < len(W1pingrtt):
        if W1pingrtt[i] >= 30000:
            tmp = [curPosX[i], curPosY[i]]
            w1DropSeq.append(i)
            # 只记录超时30s后的第一个坐标
            while i < len(W1pingrtt) and W1pingrtt[i] >= 30000:
                i += 1
            # 删除（0，0）处的统计数据
            if tmp[0] == 0 and tmp[1] == 0:
                pass
            else:
                w1DropList[tmp[1]][tmp[0]] += 1
        i += 1
    
    with open(os.path.join(tmpDir, 'w1-drop.csv'), 'w') as f:
        f.write('{},{},{}\n'.format('curTimestamp', 'curPosX', 'curPosY'))
        for i in range(len(w1DropSeq)):
            f.write('{},{},{}\n'.format(curTimestamp[w1DropSeq[i]], 
                curPosX[w1DropSeq[i]], 
                curPosY[w1DropSeq[i]]))

    plt.title('w1-drop')
    plt.xlim([0, 264])
    plt.ylim([0, 138])

    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 6.0)

    # w1掉线比较多，均匀生成5个刻度
    cbarMaxTick = max(map(max,w1DropList))
    ax = sns.heatmap(w1DropList, cmap="Blues", vmin=0,
                    #  cbar_kws={'ticks':map(int, np.linspace(0, cbarMaxTick, 5))})
                    cbar_kws={'ticks':range(0, cbarMaxTick+1)})

    # 逆置Y轴
    ax.invert_yaxis()

    plt.savefig(os.path.join(tmpDir, 'w1-drop.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    #####################################################################
    

    ###################################################################
    print("统计w0pingrtt与w1pingrtt最小值超时30s的掉线")
    minW0AndW1DropList = [[0]*265 for _ in range(139)]
    minW0AndW1DropSeq = []
    i = 0
    while i < len(minW0AndW1):
        if minW0AndW1[i] >= 30000:
            tmp = [curPosX[i], curPosY[i]]
            minW0AndW1DropSeq.append(i)
            # 只记录超时30s后的第一个坐标
            while i < len(minW0AndW1) and minW0AndW1[i] >= 30000:
                i += 1
            # 删除（0，0）处的统计数据
            if tmp[0] == 0 and tmp[1] == 0:
                pass
            else:
                minW0AndW1DropList[tmp[1]][tmp[0]] += 1
        i += 1
    
    with open(os.path.join(tmpDir, 'min-w0-w1-drops.csv'), 'w') as f:
        f.write('{},{},{}\n'.format('curTimestamp', 'curPosX', 'curPosY'))
        for i in range(len(minW0AndW1DropSeq)):
            f.write('{},{},{}\n'.format(curTimestamp[minW0AndW1DropSeq[i]], 
                curPosX[minW0AndW1DropSeq[i]], 
                curPosY[minW0AndW1DropSeq[i]]))

    plt.title('min-w0-w1-drop')
    plt.xlim([0, 264])
    plt.ylim([0, 138])
    
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 6.0)

    # minw0Andw1掉线次数大约就几个，颜色条刻度直接间隔1就行
    cbarMaxTick = max(map(max,minW0AndW1DropList))
    ax = sns.heatmap(minW0AndW1DropList, cmap="Blues", vmin=0,
                     cbar_kws={'ticks':range(0, cbarMaxTick+1)})
    
    # 逆置Y轴
    ax.invert_yaxis()

    plt.savefig(os.path.join(tmpDir, 'min-w0-w1-drop.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    ###################################################################

    
    ###################################################################
    print("统计srtt超时30s的掉线")
    srttDropList = [[0]*265 for _ in range(139)]
    srttDropSeq = []
    i = 0
    while i < len(srtt):
        if srtt[i] >= 30000:
            tmp = [curPosX[i], curPosY[i]]
            srttDropSeq.append(i)
            # 只记录超时30s后的第一个坐标
            while i < len(srtt) and srtt[i] >= 30000:
                i += 1
            # 删除（0，0）处的统计数据
            if tmp[0] == 0 and tmp[1] == 0:
                pass
            else:
                srttDropList[tmp[1]][tmp[0]] += 1
        i += 1
    
    with open(os.path.join(tmpDir, 'srtt-drops.csv'), 'w') as f:
        f.write('{},{},{}\n'.format('curTimestamp', 'curPosX', 'curPosY'))
        for i in range(len(srttDropSeq)):
            f.write('{},{},{}\n'.format(curTimestamp[srttDropSeq[i]], 
                curPosX[srttDropSeq[i]], 
                curPosY[srttDropSeq[i]]))

    plt.title('srtt-drop')
    plt.xlim([0, 264])
    plt.ylim([0, 138])
    
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 6.0)

    # srtt掉线次数大约就几个，颜色条刻度直接间隔1就行
    cbarMaxTick = max(map(max,srttDropList))
    ax = sns.heatmap(srttDropList, cmap="Blues", vmin=0,
                     cbar_kws={'ticks':range(0, cbarMaxTick+1)})

    # 逆置Y轴
    ax.invert_yaxis()

    plt.savefig(os.path.join(tmpDir, 'srtt-drop.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    ###################################################################


    ###################################################################
    print("统计车跑过的热力图")
    agvWalk = [[0]*265 for _ in range(139)]
    for i in range(len(curPosX)):
        agvWalk[curPosY[i]][curPosX[i]] += 1

    plt.title('agv-walk')
    plt.xlim([0, 264])
    plt.ylim([0, 138])
    
    # 设置图片长宽比，结合dpi确定图片大小
    plt.rcParams['figure.figsize'] = (11.0, 6.0)

    ax = sns.heatmap(agvWalk, cmap="Blues", vmin=0)

    # 逆置Y轴
    ax.invert_yaxis()

    plt.savefig(os.path.join(tmpDir, 'agvWalk.png'), dpi=150)
    plt.pause(1)
    plt.close()
    plt.pause(1)
    ###################################################################