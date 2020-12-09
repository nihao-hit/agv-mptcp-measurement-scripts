import pandas as pd
from collections import Counter

# 统计热力图不同热力值包含坐标数
def countHotMap(fileName):
    print('countHotMap() {}'.format(fileName))
    matrix = pd.read_csv(fileName).values.tolist()
    l = []
    for row in matrix:
        l += row
    for k, v in dict(Counter(l)).items():
        print('{} : {}'.format(k, v))


if __name__ == '__main__':
    fileName = '/home/cx/Desktop/sdb-dir/tmp/30.113.151.1/analysisHandover/WLAN1漫游热力图统计数据.csv'
    countHotMap(fileName)