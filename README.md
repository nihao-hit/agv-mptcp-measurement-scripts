# 网络数据分析

[TOC]

## 一　分析目标

+ 全面分析AGV无线控制网络的性能，着重探究MPTCP协议在移动场景中的协议行为，网络性能．
+ 定位掉线与通信时延大的问题．
+ 六大块内容
  1. 基站覆盖分析：刻画基站覆盖情况，发现基站覆盖空白；统计关联基站的最小RSSI与未关联基站的最大RSSI．
  2. 掉线分析：刻画掉线情况，定位掉线原因．
  3. 漫游分析：刻画漫游情况，探究漫游算法性能，分析漫游对MPTCP协议行为，网络性能的影响．
  4. 时延分析：刻画时延情况，定位时延大原因，探究srtt机制性能．
  5. MPTCP协议分析：分析路径管理模块，拥塞控制模块，流量调度模块在移动场景中，漫游事件下的行为．
  6. 应用特征分析

***

## 二　数据整理

### 2.1 scan文件分析

1. quality与level分析
   1. cfg80211假设RSSI在区间[-110, -40]dBm。quality = (level + 110) / 70 * 100。
   2. wlan1的quality只有0/100与100/100，且一般只有当前关联的基站为100/100、其余基站为0/100，没有参考价值。
   3. wlan0的quality与level之间的关系也只是简单的quality * 70 - 110 = level，也没有参考价值。
   4. 假设wlan1的level是按照quality的计算公式得出，那么将其还原为RSSI。
2. scan文件空洞分析
   1. scan文件交替测量WLAN0与WLAN1，空洞定义为既没有测量WLAN0，也没有测量WLAN1的时段，分为两种情况：两次测量的间隙，以及脚本宕掉。
3. 测量机制的书面化描述：使用`iw scan`工具交替测量附近的WLAN0与WLAN1基站，测量时间一般为几秒，测量间隔一般为几十毫秒．
4. 数据解析
   1. 解析时间戳精度为秒，由于测量时间为数秒，因此一次测量结果用于填充这数秒的数据．
   2. 一次测量结束时也会使用`iwconfig`工具打印当前连接基站信息，提取此数据缓解conn文件测量空洞的问题，填补时刻为测量结束时刻etime。

***

### 2.2 conn文件分析

1. wlan0的quality与level的关系与scan文件的一致，但是wlan1的存在不一致现象。
2. conn文件空洞分析
   1. conn文件也是交替测量WLAN0与WLAN1，但是对WLAN0，几乎每秒都有多个测量数据，对WLAN1，则往往数秒才有一个数据。因此分别统计WLAN0与WLAN1的空洞。
   2. 同样空洞有两种情况：两次测量的间隙，以及脚本宕掉。
3. 测量机制的书面化描述：使用`iwconfig`工具交替测量当前连接的WLAN0与WLAN1基站，测量时间可忽略不计，对WLAN0，测量间隔一般为几百毫秒；对WLAN1，测量间隔达到了数秒．
4. 数据解析
   1. 解析时间戳精度为毫秒，以秒为精度对齐时，选择1s内多次测量结果中RSSI最大的数据．
5. 如何区分未关联基站时刻与数据空洞：只将'Not-Associated'认为未关联基站，并将此作为漫游事件的判定依据．

***

### 2.3 tcpprobe文件分析

1. tcpprobe工具依赖内核jprobe机制在`tcp_rcv_established()`函数入口处插入探测函数，记录当前TCP状态．
2. 由于`tcp_rcv_established()`函数是处理处于established状态的TCP连接收包，因此观察不到TCP连接的建立与关闭。
3. tcpprobe文件只能获得MPTCP连接当前正在使用的TCP子流的状态信息，且由于map_data_len、map_data_seq、map_subseq全为0，不能反推MPTCP连接的状态信息。
4. 数据解析
   1. 解析时间戳精度为毫秒，以秒为精度对齐时，选择1s内多次测量结果中srtt最小的数据．
5. tcpprobe文件字段与TCP状态信息对应关系分析
   1. `u8 mptcp_tcp_sock::path_index`与`unsigned long mptcp_cb::path_index_bits`相对应。path_index_bits是位图，相应位置1表示某条子流标志1 << path_index；meta-sk，master-sk，slave-sk的path_index从0，1，2递增，但是master-sk与slave-sk可能变动。在`mptcp_add_sock()`中给path_index赋新值并记录到path_index_bits，在`mptcp_del_sock()`中清除path_index_bits对应子流的掩码；因此不同时间的不同子流可能有相同path_index。
   2. `u32 mptcp_tcp_sock::snt_isn`与`u32 mptcp_tcp_sock::rcv_isn`等于`u32 tcp_sock::snt_isn`与`u32 tcp_sock::rcv_isn`。
6. 确定tcpprobe工具的启动参数
   1. 目测服务器端口有两个：7070和7001，其中tcpdump文件7001端口的数据包极少，可能一个文件就几十个，而tcpprobe文件中没有7001的数据。
   2. 目测tcpprobe文件1s内有好几个收包。
   3. 因此tcpprobe工具应该是运行在AGV上，通过dport=7070来监听与服务器的连接，通过full=1记录每一个收包。

| tcpprobe字段     | 含义                  | 对应TCP状态信息                                              |
| ---------------- | --------------------- | ------------------------------------------------------------ |
| src              | ip:port，AGV的地址    | inet_sock::inet_saddr + inet_sport                           |
| dst              | ip:port，服务器的地址 | inet_sock::inet_daddr + inet_dport                           |
| length           | tcp包长度：首部+数据  |                                                              |
| snd_nxt          |                       | tcp_sock::snd_nxt                                            |
| snd_una          |                       | tcp_sock::snd_una                                            |
| snd_cwnd         | 字节还是包数          | tcp_sock::snd_cwnd                                           |
| ssthresh         | 字节还是包数          | 可以认为等于tcp_sock::snd_ssthresh                           |
| snd_wnd          |                       | tcp_sock::snd_wnd                                            |
| srtt             | 单位us                | tcp_sock::srtt_us >> 3，/* smoothed round trip time << 3 in usecs */ |
| rcv_wnd          |                       | tcp_sock::rcv_wnd                                            |
| path_index       |                       | mptcp_tcp_sock::path_index                                   |
| ~~map_data_len~~ | 全为0                 | mptcp_tcp_sock::map_data_len                                 |
| ~~map_data_seq~~ | 全为0                 | mptcp_tcp_sock::map_data_seq                                 |
| ~~map_subseq~~   | 全为0                 | mptcp_tcp_sock::subseq                                       |
| snt_isn          |                       | mptcp_tcp_sock::snt_isn, /* isn: needed to translate abs to relative subflow seqnums */ |
| rcv_isn          |                       | mptcp_tcp_sock::rcv_isn                                      |

***

### 2.4 tcpdump文件分析

使用如下工具分析pcap抓包文件：

1. mptcpsplit
   1. `mptcpsplit -l pcap_filename`：读pcap文件列出所有mptcp连接信息。每行格式如下：`four_tuple connection_num first_timestamp last_timestamp duration`
   2. `mptcpsplit -n connection_num -o outfile_filename pcap_filename`：读pcap文件并将connection_num所属的所有数据包写入outfile_filename。

2. mptcpcrunch
   1. `mptcpcrunch filename`：测试是否filename有什么错误
   2. `mptcpcrunch -s filename`：输出subflow信息到stdout，每条子流三行，第一行为subflow number，二三行为单向统计信息。所有数据项格式都为`LABEL: DATA`。
   3. `mptcpcrunch -c filename`：输出connection信息到stdout，三行，第一行为meta信息，第二三行为单向连接信息。所有数据项格式都为`LABEL: DATA`。

3. mptcpplot
   1. `mptcpplot -a -j pcap_file`：根据一个pcap文件生成连接级别的time sequence图表，输出三个文件`connection_0-MAPPING.txt`, `connection_0-ORIGIN.xpl`, `connection_0-REMOTE.xpl`，默认在当前文件夹下且不能控制．
   2. time sequence图有三类主要符号：
      1. data segments : 垂直线段，两端有箭头．从数据包的开始到结束序列号．
      2. data acknowledgments : 小方块．
      3. green acknowledgment line : 绿色横线表明当前累计确认序列号即snd_una．
   3. 两类补充符号：
      1. `-a` : 追踪ADD_ADDRESS与REMOVE_ADDRESS选项．
      2. `-j` : 追踪MP_JOIN选项．

4. xplot.org : `xplot.org time_sequence_graph_name.xpl`渲染时序图

***

### 2.5 comm文件分析

1. messageType = {DATA : 8642/10000, HEART_BEAT : 662/1000}
2. logger = {computer|id:AGV-030113151001 : 15/10000, nioEventLoopGroup-2-1 : 4989/10000, pool-14-thread-1 : 4290/10000, pool-6-thread-1 : 5/10000}
3. jobSn = {0 ：198584/387421，且dspStatus = IDLE, ...}
4. 日志信息很杂乱，log间隔约几百毫秒；logger主要为nioEventLoopGroup-X-X，pool-X-thread-X；jobSn能不能作为任务划分标志不确定．

***

### 2.6 测量文件空洞分析

探究是否有测量脚本单独drop或集体drop（AGV宕机）．

***

### 2.7 数据清洗　

1. 补全
2. 去重：对conn文件和comm文件进行去重处理，1号车connData.csv行数从7775775到5295694，commData.csv行数从6247790到2615033．
3. 去除离群值：使用分位数，具体问题具体分析．
4. 去除异常值：主要是补全值与缺失但未进行补全的值．具体问题具体分析．

***

## 三　描述分析

描述统计分为两大部分：数据描述和指标统计。

1. 数据描述：用来对数据进行基本情况的刻画，包括：数据总数、时间跨度、时间粒度、空间范围、空间粒度等。如果是建模，那么还要看数据的极值、分布、离散度等内容。
2. 指标统计：分析实际情况的数据指标，可粗略分为四大类：变化、分布、对比、预测．
3. 图表：CDF图，柱状图，散点图，折线图，热力图．<u>箱型图</u>，<u>小提琴图</u>

***

### 3.1 基站覆盖分析

刻画基站覆盖情况，发现基站覆盖空白．

统计关联基站的最小RSSI与未关联基站的最大RSSI．

1. 非图表型统计数据：conn数据总数，WLAN0数据总数，WLAN0过滤后数据总数，WLAN1数据总数，WLAN1过滤后数据总数，start，end，duration，时间粒度，WLAN0最小RSSI，WLAN0最大RSSI，WLAN1最小RSSI，WLAN1最大RSSI，WLAN0 Not-Associated数据总数，WLAN1 Not-Associated数据总数，WLAN0未关联基站最大RSSI1，WLAN0未关联基站最大RSSI2，WLAN1未关联基站最大RSSI1，WLAN1未关联基站最大RSSI2．
2. 粗粒度分析
   1. 无线网卡连接基站的RSSI分布CDF，
   2. 无线网卡未连接基站时观测到的基站最大RSSI分布CDF
   3. 基站覆盖热力图
   4. 有效基站覆盖热力图
   5. 基站覆盖空白热力图

***

### 3.2 掉线分析

刻画掉线情况，定位掉线原因．

***

### 3.3 漫游分析

刻画漫游情况，探究漫游算法性能，分析漫游对MPTCP协议行为，网络性能的影响．

根据conn文件分析结论，划分漫游为以下三种情况：

1. AP1->Not-Associated->AP2，统计数据中flag=0
2. AP1->Not-Associated->AP1，统计数据中flag=1
3. AP1->AP2，统计数据中flag=2
4. ~~AP1->' '->AP2~~

1. 非图表型统计数据：WLAN0漫游次数，WLAN0 flag=0漫游次数，WLAN0 flag=1漫游次数，WLAN0 flag=2漫游次数，WLAN1漫游次数，WLAN1 flag=0漫游次数，WLAN1 flag=1漫游次数，WLAN1 flag=2漫游次数，漫游时间戳粒度
2. 粗粒度分析
   1. 漫游热力图
   2. 漫游时长CDF图
   3. 漫游时长分类柱状图：`['<=200ms', '200ms-1s', '1s-5s', '>5s']`
   4. 漫游类型分类柱状图：`flag = {0, 1, 2}`
   5. 漫游RSSI增益CDF：RSSI值可简单使用关联基站时刻的RSSI值。
      + 不同时长分类的RSSI增益没有明显区别，不需要研究
      + 不同类型分类的RSSI增益理论上有明显区别
   6. 在将时间戳精度提高到ms后，1号车WLAN0漫游次数来到了2813次，WLAN1漫游次数来到了3411次。同时网络层时延对比不再有多少意义，因为网络层时延精度为s。
3. 细粒度分析
   1. 漫游事件全景图
   2. 漫游事件RSSI分析图
      1. 漫游事件的时间戳精度为ms，而scan得到的基站数据时间戳精度为s，且往往测量时间长达数秒，综合以上情况将分析图时间戳精度设置为s．
      2. 通常flag=1类型的漫游导致RSSI增益较小或为负，且flag=1的漫游后往往紧接着发生flag=0的漫游，间隔在1s以内．
      3. 如何从1号车WLAN0的2800多次漫游事件中选择**表现力最好**且能**发现问题**的图片
         1. 手动过滤：可保证发现问题
         2. 程序过滤：设置过滤条件例如数据完整性，保证表现力．
4. 802.11漫游协议：802.11x、802.11k、802.11r、802.11v

***

### 3.4 时延分析

刻画时延情况，定位时延大原因，探究srtt机制性能．

***

### 3.5 MPTCP协议分析

分析路径管理模块，拥塞控制模块，流量调度模块在移动场景中，漫游事件下的行为．

tcpprobe文件中为什么map_data_len、map_data_seq、map_subseq都为0，snt_isn与rcv_isn有时候也为0？

注意到某1s内多次切换子流使用，是否需要详细探究流量调度器的行为？

1. 非图表型统计数据：tcpprobe收包总数，start，end，duration，tcpprobe时间粒度．
2. 粗粒度分析
   1. WLAN0与WLAN1使用时长占比饼状图
   2. TCP子流连续使用时长CDF图
   3. TCP子流连续使用时长分类柱状图
3. 细粒度分析：
   1. 提取指定时长的连续使用TCP子流，对TCP子流的snd_nxt, snd_una, snd_cwnd, ssthresh, snd_wnd, rcv_wnd, srtt进行分析，同时提取在此时段的WLAN0漫游事件，WLAN1漫游事件暂时不考虑，提取在此时段的ping时延数据与srtt对比分析.
   2. 提取漫游事件附近指定时长的TCP子流，分析TCP状态.

***

### 3.6 应用特征分析

任务划分方式
1. 以jobSn划分，jobSn=0视为空闲
2. ~~以controlStatus划分，controlStatus=IDLE视为空闲，ACTION_DOING——>ACTION_DONE视为一次任务。~~
3. ~~以dspStatus划分，dspStatus=MOVE_COMPLETED视为一次任务的结束。~~
4. ~~以destPosX，destPosY划分，~~
5. 以上四者存在冲突。例如：一次任务是否存在更换目的地的可能，
6. 问题：
   1. AGV是否一直在执行任务，会不会存在大段的时间AGV处于空闲状态。
   2. AGV一次任务是否存在更换目的地的可能

使用时间戳精度为s的data.csv文件而不是时间戳精度为ms的commData.csv文件，因为涉及到时长等统计．

1. 非图表数据：任务总数，任务总时间，空闲总时间，任务时间粒度
2. 粗粒度分析
   1. 速度CDF图
   2. 任务耗时CDF图
   3. 任务移动距离CDF图
3. 细粒度分析
   1. 一次任务速度散点图，一次任务状态转换
   2. 当前使用WLAN，网络层时延，传输层时延

***

### 3.7 细粒度时段

1. 通过tcpprobe文件提取当前连续使用TCP子流时段
2. 通过tcpdump文件提取MPTCP连接时段
3. 通过comm文件提取任务时段
4. 通过conn文件提取漫游事件时段

***

## 四　洞察结论

## 五　建模分析

## 当前情况

1. 对这批数据的认识比较深了
2. 有很多描述性的图表
3. 缺少发现问题的关键性的结论，以及性能的评估．

***

## TODO

1. 这里只分析了受WLAN0漫游影响的WLAN0的TCP子流，是否需要研究不同网络的漫游事件与TCP子流的交叉影响
2. 这里的conn数据没有写入data.csv文件，目前看来影响不大，有时间再搞吧．

***