# 时间戳精度为s
class Status:
    #####################################################
    # comm数据
    agvCode = ''            #1
    dspStatus = ''          #2
    destPosX = 0            #3
    destPosY = 0            #4
    curPosX = 0             #5
    curPosY = 0             #6
    curTimestamp = 0        #7
    direction = 0.0         #8
    speed = 0.0             #9
    withBucket = -1         #10
    jobSn = 0               #11
    #####################################################
    #####################################################
    # conn数据
    W0APMac = ''            #12
    W0channel = 0.0         #13
    W0level = 0             #14

    W1APMac = ''            #15
    W1channel = 0.0         #16
    W1level = 0             #17
    #####################################################
    #####################################################
    # ping151
    W0pingrtt = 0           #18
    #####################################################
    #####################################################
    # ping127
    W1pingrtt = 0           #19
    #####################################################
    #####################################################
    # scan数据，用于统计AP覆盖情况
    scanW0APCount = 0       #20
    # SNR高于某个阈值的AP数量
    # scanW0APEff = 0
    scanW0APLevelMin = 0    #21
    # 2020/11/26:11: 为Status添加scanW0APChannelMin, scanW0APChannelMax, scanW1APChannelMin, scanW1APChannelMax字段
    scanW0APChannelMin = 0.0
    scanW0APMacMin = ''     #22
    scanW0APLevelMax = 0    #23
    scanW0APChannelMax = 0.0
    scanW0APMacMax = ''     #24

    scanW1APCount = 0       #25
    # SNR高于某个阈值的AP数量
    # scanW1APEff = 0
    scanW1APLevelMin = 0    #26
    scanW1APChannelMin = 0.0
    scanW1APMacMin = ''     #27
    scanW1APLevelMax = 0    #28
    scanW1APChannelMax = 0.0
    scanW1APMacMax = ''     #29
    #####################################################
    #####################################################
    # tcpprobe数据，用于统计drop
    src = ''                #30
    srcPort = 0             #31
    dst = ''                #32
    dstPort = 0             #33
    length = 0              #34
    snd_nxt = 0             #35
    snd_una = 0             #36
    snd_cwnd = 0            #37
    ssthresh = 0            #38
    snd_wnd = 0             #39
    srtt = 0                #40
    rcv_wnd = 0             #41 
    path_index = 0          #42
    map_data_len = 0        #43
    map_data_seq = 0        #44
    map_subseq = 0          #45
    snt_isn = 0             #46
    rcv_isn = 0             #47
    #####################################################


    def __init__(self):
        #####################################################
        # comm数据
        self.agvCode = ''            #1
        self.dspStatus = ''          #2
        self.destPosX = 0            #3
        self.destPosY = 0            #4
        self.curPosX = 0             #5
        self.curPosY = 0             #6
        self.curTimestamp = 0        #7
        self.direction = 0.0         #8
        self.speed = 0.0             #9
        self.withBucket = -1         #10
        self.jobSn = 0               #11
        #####################################################
        #####################################################
        # conn数据
        self.W0APMac = ''            #12
        self.W0channel = 0.0         #13
        self.W0level = 0             #14

        self.W1APMac = ''            #15
        self.W1channel = 0.0         #16
        self.W1level = 0             #17
        #####################################################
        #####################################################
        # ping151
        self.W0pingrtt = 0           #18
        #####################################################
        #####################################################
        # ping127
        self.W1pingrtt = 0           #19
        #####################################################
        #####################################################
        # scan数据，用于统计AP覆盖情况
        self.scanW0APCount = 0       #20
        # SNR高于某个阈值的AP数量
        # scanW0APEff = 0
        self.scanW0APLevelMin = 0    #21
        self.scanW0APMacMin = ''     #22
        self.scanW0APLevelMax = 0    #23
        self.scanW0APMacMax = ''     #24

        self.scanW1APCount = 0       #25
        # SNR高于某个阈值的AP数量
        # scanW1APEff = 0
        self.scanW1APLevelMin = 0    #26
        self.scanW1APMacMin = ''     #27
        self.scanW1APLevelMax = 0    #28
        self.scanW1APMacMax = ''     #29
        #####################################################
        #####################################################
        # tcpprobe数据，用于统计drop
        self.src = ''                #30
        self.srcPort = 0             #31
        self.dst = ''                #32
        self.dstPort = 0             #33
        self.length = 0              #34
        self.snd_nxt = 0             #35
        self.snd_una = 0             #36
        self.snd_cwnd = 0            #37
        self.ssthresh = 0            #38
        self.snd_wnd = 0             #39
        self.srtt = 0                #40
        self.rcv_wnd = 0             #41 
        self.path_index = 0          #42
        self.map_data_len = 0        #43
        self.map_data_seq = 0        #44
        self.map_subseq = 0          #45
        self.snt_isn = 0             #46
        self.rcv_isn = 0             #47
        #####################################################

    def __setitem__(self, k, v):
        self.k = v

    def __getitem__(self, k):
        return getattr(self, k)

    def __str__(self):
        return str(self.__dict__)

    def keys(self):
        return [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]

# 时间戳精度为ms
class CommStatus:
    agvCode = ''            #1
    dspStatus = ''          #2
    destPosX = 0            #3
    destPosY = 0            #4
    curPosX = 0             #5
    curPosY = 0             #6
    curTimestamp = 0        #7
    direction = 0.0         #8
    speed = 0.0             #9
    withBucket = -1         #10
    jobSn = 0               #11

    def __init__(self):
        self.agvCode = ''            #1
        self.dspStatus = ''          #2
        self.destPosX = 0            #3
        self.destPosY = 0            #4
        self.curPosX = 0             #5
        self.curPosY = 0             #6
        self.curTimestamp = 0        #7
        self.direction = 0.0         #8
        self.speed = 0.0             #9
        self.withBucket = -1         #10
        self.jobSn = 0               #11
    
    def __setitem__(self, k, v):
        self.k = v

    def __getitem__(self, k):
        return getattr(self, k)

    def __str__(self):
        return str(self.__dict__)

    def keys(self):
        return [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]

# 时间戳精度为ms
class ConnStatus:
    timestamp = 0

    W0APMac = ''            #12
    W0channel = 0.0         #13
    W0level = 0             #14

    W1APMac = ''            #15
    W1channel = 0.0         #16
    W1level = 0             #17

    def __init__(self):
        self.timestamp = 0

        self.W0APMac = ''            #12       
        self.W0channel = 0.0         #13       
        self.W0level = 0             #14  

        self.W1APMac = ''            #15
        self.W1channel = 0.0         #16
        self.W1level = 0             #17
    
    def __setitem__(self, k, v):
        self.k = v

    def __getitem__(self, k):
        return getattr(self, k)

    def __str__(self):
        return str(self.__dict__)

    def keys(self):
        return [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]

# 时间戳精度为s
class ScanStatus:
    timestamp = 0
    # 在解析comm文件时赋值
    curPosX = 0
    curPosY = 0

    w0ApMac = []
    w0Channel = []
    w0Level = []

    w1ApMac = []
    w1Channel = []
    w1Level = []

    def __init__(self):
        self.timestamp = 0
        # 在解析comm文件时赋值
        self.posX = 0
        self.posY = 0

        self.w0ApMac = []
        self.w0Channel = []
        self.w0Level = []

        self.w1ApMac = []
        self.w1Channel = []
        self.w1Level = []
    
    def __setitem__(self, k, v):
        self.k = v

    def __getitem__(self, k):
        return getattr(self, k)

    def __str__(self):
        return str(self.__dict__)

    def keys(self):
        return [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]

# 时间戳精度为ms
class TcpprobeStatus:
    timestamp = 0

    src = ''                #30
    srcPort = 0             #31
    dst = ''                #32
    dstPort = 0             #33
    length = 0              #34
    snd_nxt = 0             #35
    snd_una = 0             #36
    snd_cwnd = 0            #37
    ssthresh = 0            #38
    snd_wnd = 0             #39
    srtt = 0                #40
    rcv_wnd = 0             #41 
    path_index = 0          #42
    map_data_len = 0        #43
    map_data_seq = 0        #44
    map_subseq = 0          #45
    snt_isn = 0             #46
    rcv_isn = 0             #47

    def __init__(self):
        self.timestamp = 0

        self.src = ''                #30
        self.srcPort = 0             #31
        self.dst = ''                #32
        self.dstPort = 0             #33
        self.length = 0              #34
        self.snd_nxt = 0             #35
        self.snd_una = 0             #36
        self.snd_cwnd = 0            #37
        self.ssthresh = 0            #38
        self.snd_wnd = 0             #39
        self.srtt = 0                #40
        self.rcv_wnd = 0             #41 
        self.path_index = 0          #42
        self.map_data_len = 0        #43
        self.map_data_seq = 0        #44
        self.map_subseq = 0          #45
        self.snt_isn = 0             #46
        self.rcv_isn = 0             #47
    
    def __setitem__(self, k, v):
        self.k = v

    def __getitem__(self, k):
        return getattr(self, k)

    def __str__(self):
        return str(self.__dict__)

    def keys(self):
        return [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]


# 对每台车提取数据都需要重置以下全局变量
#####################################################
# 时间戳精度为s，预分配大小
sList = [Status() for _ in range(86400*15)]
scanStatusList = [ScanStatus() for _ in range(86400*15)]
#####################################################
#####################################################
# 时间戳精度为ms，不能预分配大小
CommStatusList = []
ConnStatusList = []
TcpprobeStatusList = []
#####################################################