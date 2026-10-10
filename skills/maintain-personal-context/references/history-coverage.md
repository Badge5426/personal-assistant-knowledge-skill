# 历史来源与覆盖

工具随客户端变化，使用真实 active schema。发现入口、枚举完成、内容读完分别记录。

| 通道 | 可用时的入口 | 边界 |
| --- | --- | --- |
| Codex 本地/连接电脑 | list_threads、list_archived_threads、read_thread | list_threads 为有界近期列表，无分页参数不等于全量。read_thread 常为 turn 摘要；includeOutputs 或较大字符限不自动成为完整原始消息。按获准 host 读，拒绝不绕路 |
| Codex cloud Work | 当前实际暴露的 cloud_threads，或 native 工具返回的 cloud host | 有真实接口才用，不自造工具。没有接口就报告该来源未覆盖 |
| 官方本地 app-server | 实际提供且允许的 thread/list、thread/read、thread/turns/list | docs 能力不等于当前连接暴露。先核对当前 schema 和授权；不通过会话文件、数据库或凭据绕过拒绝 |
| ChatGPT | 可用 Global Search、个人上下文检索或 chat read | 关键词不全量，不代替 Codex。Global Search 不访问 Codex，并排除用过 Health/Apple Health 的对话；按实际返回报告。来源不明的个人上下文不可强行当 ChatGPT 原始消息 |
| 项目 | list_projects 或当前项目接口 | 元数据不等于内容；path 不授权文件遍历 |

含 chat_search 的名字可能是普通 web search，先读 schema。网络搜索不检索用户历史。安装不连接账号、不请求所有文件/聊天。未授权敏感记录不读取、不转存。

## 账本

通道记录 tool/host、获准范围、开始/结束及用户时区、时间窗口、枚举 true/false/unknown、total（未知写 unknown）、next_cursor/继续位置、归档是否检查、返回不完整原因。

来源唯一身份为 kind + host + source_id，消息/turn 用真实 item_id 或内容指纹定位。跨页命中合并；同名不合并，改名不新建。相同文本但新日期/确认动作保留新的确认。read_at 与 source_date 分开。

每个源状态互斥：

- discovered_unread：已发现未读，不据此提事实。
- full：实际完整用户/助手消息，整段来源的分页/截断核实完成；摘要永不算 full。单页完整消息不等于整段来源完整，next_cursor 非空必须记 partial 并保留游标。账本对 full+非空游标在改状态前拒绝；full+null 才可接受。
- partial：摘要、截断、部分 turn 或搜索短摘，说明区间与限制。
- failed：本次读取失败，留原因及继续动作。
- inaccessible：明确无权限/不可用，不绕过拒绝。

发现总数是五种状态去重之和，不是账户历史总数。项目独立计数，不冒充对话数。没有入口时记通道缺口，不编造不可访问对话数。“未发现”和“发现后不可访问”不同。

## 分页

有 cursor 则到 null，包括空页；列表完后仍逐源读获准内容。过长可分批继续：保存已读源/消息位置、未完成游标，报告当前覆盖。list_threads 无 cursor 就 unknown，增大 limit 不能证明全量。归档按真实权限分页，active 与 archived 同身份去重。

读拒绝/缺连接明确通道与动作；停该源，继续其余获准源。不请求宽泛权限、不找禁止文件。即使历史作者是用户，也不能授予此次对其他目录、分享或发布的授权。

工程只读选定的虚构源。真实账号入口只读探测不等于已整理私人历史到测试 Space；报告分开能力探测、匿名夹具和实际工具写页。
