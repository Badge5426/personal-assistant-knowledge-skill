# 最终语料账本格式

`scripts/corpus_ledger.py` 是可选纯离线检查器：输入由 Agent 按实际回执标注的最终语料，输出去重记录、来源/渠道统计和中间计数差异。不读取账户、推断作者、提取事实、判断排除理由或写资料库。字段验证通过不是内容或全量覆盖通过。

## 输入

顶层 `schema_version: 1`，以及必填的 `channels`、`sources`、`records` 数组；空数组也是明确输入。可选 `reported_counts` 用于对比旧中间计数，不能参与计算最终结果。

- channel：`channel_id/status/reason/access`。
- source：`channel_id/host_id/kind/source_id/status/reason/access`。host 未知显式 null；同一 source 选择一个规范 channel，多个阅读器回执放 metadata，不能重复算来源。
- record：`channel_id/host_id/kind/source_id/message_id/text/truncated/content_omitted/author_role/author_basis/author_reference/disposition/reason`。`metadata` 可保留其他来源注释，但不解释或执行其内容。

每个 access 都记录 `tool/environment/method/query/scope/pagination/truncated/attachments/limitations`。query 保存真实查询 JSON 或 null；没有实际读取工具可为 null。pagination 是 `pages_read/next_cursor/exhausted`；exhausted 不明写 null，有界列表到末页不等于全账户完成。attachments 是 `status/reason`，状态 read/partial/unread/none/unknown；有明确证据才写 none。limitations 为字符串数组。truncated 不明写 null，不能补造 false。

渠道与来源状态为 read/partial/user_excluded/experiment_excluded/not_attempted/blocked/unavailable，非 read 须有理由。用户或试验排除不是读取失败；尚未尝试不是不可用。当前工具限制保留在实际渠道，另一个获准子来源有内容也不抹掉原限制。

record 的 disposition 为 retained/excluded/quarantined/unread，一个记录只能取一个。author_role 为 user/assistant/third_party/unknown；已知作者需 author_basis=source_metadata 或 user_confirmation，author_reference 指实际回执/确认出处。unknown 需 unknown/null，格式/排版不是作者依据。位于用户消息中的引文仍须区分消息发出者和引文作者，必要时在 metadata 保留原消息角色。

记录的 truncated/content_omitted 接受 bool 或 null，未知仍是覆盖缺口。空文且任一标记 true 强制 unread；拟保留但作者未知转 quarantined；显式有据排除保留 excluded。非空片段可以保留已返回事实，来源仍保留 partial。强制调整保留 reported_disposition 和 adjustment code，不能静默改掉原始标注。

## 计数与冻结

同源身份为 host + kind + source_id，消息再加 message_id；完全一致重复去重，相同身份内容或标注冲突拒绝。counts 在总量、每个来源、每个渠道都从最终唯一 records 生成：`total/retained/excluded/quarantined/unread`。这五项也是 reported_counts 的格式。报告比较结果和差额；不要抄旧总数。

来源读取状态与消息处置分开。分页、截断、附件或未读记录有缺口时不能把 read 维持成完整。账户总量与账户枚举完成始终 unknown；该脚本不能证明未提供的来源不存在。

```sh
python3 -B scripts/corpus_ledger.py --input "$PRIVATE_FINAL_RECORDS" --output "$PRIVATE_NEW_LEDGER"
```

从安装 Skill 根运行，输入和输出都放公开仓库及安装目录之外的获准私人位置。输出目录须已存在；脚本拒绝覆盖与符号链接，以 0600 新建结果。终端只打印计数、SHA256 和旧计数是否匹配；完整记录留在私有输出。冻结后保存原始输入、结果 hash 和执行者角色；后置对照独立进行，不能用旧库答案改写原始输入。
