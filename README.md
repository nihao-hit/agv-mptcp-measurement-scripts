## scan文件分析

1. quality与level分析
   1. cfg80211假设接收信号强度在区间[-110, -40]dBm。quality = (level + 110) / 70 * 100。
   2. wlan1的quality只有0/100与100/100，且一般只有当前关联的基站为100/100、其余基站为0/100，没有参考价值。
   3. wlan0的quality与level之间的关系也只是简单的quality * 70 - 110 = level，也没有参考价值。
   4. 假设wlan1的level是按照quality的计算公式得出，那么将其还原为接收信号强度。
2. scan文件空洞分析
   1. scan文件交替测量WLAN0与WLAN1，空洞定义为既没有测量WLAN0，也没有测量WLAN1的时段，分为两种情况：两次测量的间隙，以及脚本宕掉。
3. 测量机制的书面化描述：使用`iw scan`工具交替测量附近的WLAN0与WLAN1基站，测量时间一般为几秒，测量间隔一般为几十毫秒．
4. 数据解析
   1. 解析时间戳精度为秒，由于测量时间为数秒，因此一次测量结果用于填充这数秒的数据．
   2. 使用scan文件中的conn数据进行填补，减轻conn文件测量空洞的问题。填补方法为填充etime时刻。

## conn文件分析

1. wlan0的quality与level的关系与scan文件的一致，但是wlan1的存在不一致。
2. conn文件空洞分析
   1. conn文件也是交替测量WLAN0与WLAN1，但是对WLAN0，几乎每秒都有多个测量数据，对WLAN1，则往往数秒才有一个数据。因此分别统计WLAN0与WLAN1的空洞。
   2. 同样空洞有两种情况：两次测量的间隙，以及脚本宕掉。
3. 测量机制的书面化描述：使用`iw config`工具交替测量当前连接的WLAN0与WLAN1基站，测量时间可忽略不计，对WLAN0，测量间隔一般为几百毫秒；对WLAN1，测量间隔达到了数秒．
4. 数据解析
   1. 解析时间戳精度为毫秒，以秒为精度对齐时，选择1s内多次测量结果中SNR最大的数据．
5. 如何区分未关联基站与空洞：只将'Not-Associated'认为未关联基站。

## 基站覆盖分析

1. 统计关联基站的最小SNR与未关联基站的最大SNR

## 漫游分析

1. 根据conn文件分析结论，划分漫游为以下四种情况：
   1. AP1->Not-Associated->AP2，统计数据中flag=0
   2. AP1->Not-Associated->AP1，统计数据中flag=1
   3. AP1->AP2，统计数据中flag=2
   4. ~~AP1->' '->AP2~~
2. 粗粒度分析
   1. 漫游热力图
   2. 漫游时长CDF,漫游时长分类柱状图,
   3. 漫游类型分类柱状图,
   4. 漫游SNR增益CDF
3. 细粒度分析
   1. 通常flag=1类型的漫游导致SNR增益较小或为负，且flag=1的漫游后往往紧接着发生flag=0的漫游，间隔在1s以内．
   2. 漫游事件全景图
   3. 漫游事件SNR分析图
      1. 漫游事件的时间戳精度为ms，而scan得到的基站数据时间戳精度为s，且往往采样周期长达数秒，ping得到的时延数据采样周期为1s．综合以上情况将分析图时间戳精度设置为s．
      2. 如何从1号车WLAN0的2800多次漫游事件中选择**表现力最好**且能**发现问题**的图片
         1. 手动过滤：可保证发现问题
         2. 程序过滤：设置过滤条件例如数据完整性，保证表现力．
4. 漫游SNR对比可简单使用关联基站时刻的SNR值。
5. 而漫游RTT对比则复杂一些，由于ping时延存在滞后性，
   1. ~~使用关联基站时刻后2s的最大值与最小值分别表征漫游前RTT与漫游后RTT，~~问题：漫游前后RTT都存在很多填充值。
   2. ~~在左闭右开区间`[关联AP1最后时刻, 关联AP2开始时刻)`，`[关联AP2开始时刻, 正无穷)`中搜寻第一个非填充值~~，问题：漫游前RTT还是存在很多填充值，且很多时候漫游前RTT过小，漫游后RTT过大，猜测原因为该值在采样区间偏右部分，不能反应当前网络状态。
   3. 观察data.csv漫游前后RTT数据分布，在1的基础上将滞后时间延长至3s。
6. 在将时间戳精度提高到ms后，1号车WLAN0漫游次数来到了2813次，WLAN1漫游次数来到了3411次。同时R网络层时延对比不再有多少意义，因为网络层时延精度为s。
7. 802.11漫游协议：802.11k、802.11r、802.11v

## tcpprobe文件分析

1. tcpprobe工具依赖内核jprobe机制在`tcp_rcv_established()`函数入口处插入探测函数，记录当前TCP状态；
2. 由于`tcp_rcv_established()`函数是处理处于established状态的TCP连接收包，因此观察不到TCP连接的建立与关闭。
3. tcpprobe文件只能获得MPTCP连接当前正在使用的TCP子流的状态信息，且由于map_data_len、map_data_seq、map_subseq全为0，不能反推MPTCP连接的状态信息。
4. 数据解析
   1. 解析时间戳精度为毫秒，以秒为精度对齐时，选择1s内多次测量结果中srtt最小的数据．
5. tcpprobe文件字段与TCP状态信息对应关系分析
   1. `u8 mptcp_tcp_sock::path_index`与`unsigned long mptcp_cb::path_index_bits`相对应。path_index_bits是位图，相应位置1表示某条子流标志1 << path_index；meta-sk，master-sk，slave-sk的path_index从0，1，2递增，但是master-sk与slave-sk可能变动。在`mptcp_add_sock()`中给path_index赋新值并记录到path_index_bits，在`mptcp_del_sock()`中清除path_index_bits对应子流的掩码；因此不同时间的不同子流可能有相同path_index。
   2. `u32 mptcp_tcp_sock::snt_isn`与`u32 mptcp_tcp_sock::rcv_isn`等于`u32 tcp_sock::snt_isn`与`u32 tcp_sock::rcv_isn`。
6. 确定tcpprobe工具的启动参数
   1. 目测服务器端口有两个：7070和7001，其中根据tcpdump文件7001端口的数据极少，可能一个文件就几十个，而tcpprobe文件中没有7001的数据。
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

## mptcp分析

### 问题：

1. tcpprobe文件中为什么map_data_len、map_data_seq、map_subseq都为0，snt_isn与rcv_isn有时候也为0？
2. 注意到某1s内多次切换子流使用，是否需要详细探究流量调度器的行为？

## comm文件分析

1. messageType = {DATA : 8642/10000, HEART_BEAT : 662/1000}
2. logger= {computer|id:AGV-030113151001 : 15/10000, nioEventLoopGroup-2-1 : 4989/10000, pool-14-thread-1 : 4290/10000, pool-6-thread-1 : 5/10000}
3. jobSn = {0 ：198584/387421，且dspStatus = IDLE, ...}，一天大约200多个任务。
4. comm文件需要去重处理。

## 去重

conn文件和comm文件都需要去重处理

1. 1号车connData.csv去重后从7775775条数据减少到5295694条数据。
2. 1号车commData.csv去重后从

## comm分析

1. 任务划分方式
   1. 以jobSn划分，jobSn=0视为空闲
   2. ~~以controlStatus划分，controlStatus=IDLE视为空闲，ACTION_DOING——>ACTION_DONE视为一次任务。~~
   3. ~~以dspStatus划分，dspStatus=MOVE_COMPLETED视为一次任务的结束。~~
   4. ~~以destPosX，destPosY划分，~~
   5. 以上四者存在冲突。例如：一次任务是否存在更换目的地的可能，
   6. 问题：
      1. AGV是否一直在执行任务，会不会存在大段的时间AGV处于空闲状态。
      2. AGV一次任务是否存在更换目的地的可能
2. 粗粒度分析
   1. 速度CDF，
   2. 平均每天多少次任务，每次任务平均耗时与耗时CDF，每次任务平均移动距离与移动距离CDF
   3. 每天平均做任务与闲置的时间占比
3. 细粒度分析
   1. 一次任务速度散点图，一次任务状态转换
   2. 当前使用WLAN，网络层时延，传输层时延

## 细粒度分析

1. 时段提取
   1. 通过tcpprobe文件提取当前连续使用tcp子流时段
   2. 通过tcpdump文件提取mptcp连接时段
   3. 通过comm文件提取一次任务时段
   4. 通过conn文件提取一次漫游时段
2. 漫游

## tcpdump文件分析

mptcpsplit

1. `mptcpsplit -l pcap_filename`：读pcap文件列出所有mptcp连接信息。每行格式如下：`four_tuple connection_num first_timestamp last_timestamp duration`
2. `mptcpsplit -n connection_num -o outfile_filename pcap_filename`：读pcap文件并将connection_num所属的所有数据包写入outfile_filename。

mptcpcrunch

1. `mptcpcrunch filename`：测试是否filename有什么错误
2. `mptcpcrunch -s filename`：输出subflow信息，每条子流三行，第一行为subflow number，二三行为单向统计信息。
3. `mptcpcrunch -c filename`：输出connection信息，三行，第一行为meta信息，第二三行为单向连接信息。所有数据项格式都为`LABEL: DATA`。

mptcpplot：根据一个pcap文件生成连接级别的time sequence图表。

`xplot.org time_sequence_graph_name.xpl`

## 目标

1. 分析MPTCP在移动场景下的协议行为与性能
2. 分析MPTCP在漫游事件下的协议行为与性能