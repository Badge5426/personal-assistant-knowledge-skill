# Space 保存与恢复

## 私人状态

保存 Space.id/root、各角色 Page.id/parent/URL、run_id、完整读回与 hash、权限证据、源身份、覆盖/继续游标、操作意图/回执/未知状态。真实 ID 只在私人状态或私人 Page，不进公开包。无状态先读相关页和标记，不按标题认领。

可选标准库 `scripts/space_state.py` 不调用 API，只验证调用者提交的回执并保存本地账本；不验证网络真实性、不代替事实判断、不创建 Space。先创建明确的仓库外私人目录：

```sh
STATE="/absolute/path/to/private-context/setup-state.json"
SCRIPT="$PROJECT/.agents/skills/maintain-personal-context/scripts/space_state.py"
python3 "$SCRIPT" --state "$STATE" init --name "个人助手知识库" \
  --as-of "YYYY-MM-DD" --authorized-scope "本次用户明确允许的范围"
python3 "$SCRIPT" --state "$STATE" show
```

init 不覆盖已有状态，不创建目录/页面/权限。Agent 可导入助手，begin_create 后先 save_state，再调用真实工具；返回后 accept_created、verify_page、record_privacy 并保存。受限分享结果未返回 Page ID 时，传入该次真实请求的 requested_page_id，不能伪造返回字段。加载后的保存传 expected_revision；锁/版本冲突先核对，不删锁绕过正在运行者。断电残锁需核对没有活跃写者，保留副本后处理。

## 写入

- 编辑前读完整相关页面和 guidance，核对权限及主来源。用当前 canonical block_id/hash，只有读取提供 sequence 才传。部分读取不得整体替换。
- 区分管理块和用户新块。手改管理内容先看差异，未经明确裁定不能用旧模板覆盖；其他块、链接、checkbox、元数据原样保留。其他任务唯一维护页不抢写。
- 按实际 schema 区分原子结构编辑和允许部分成功的 literal patch。检查 commit_status、所有 receipts、ignored_reason。hash/sequence 冲突重读，只重建未应用项；applied 不重放。block_deleted 不自动复建。
- unknown 先在同一 stream 读回对账；读回失败记“写入未确认”，不新建替代页。新增/宽改/保留敏感编辑读回正文、parent 和来源。无 UI 预览只称保存正文验证。
- 每页直接/继承权限核验；所有页完成才能称私有结构。缺权限信息不写真实资料，也不改分享。

## 恢复

创建前保存 pending；真实返回 identity 后记 created，正文/parent/标记读回才 verified。created 未读回，下次先 read。pending/unknown 先查证。create_space 无幂等键；未标记根只有同名不够，需本次回执或可靠同一操作证据，无法唯一确定就给精准选择，不再建。

Page 未知结果在获准实际 parent 列表中按角色名/run_id 标记找，读回唯一匹配才映射；列表不完整/多个匹配均停止创建。没有证据不推断失败，不改名重复建。Site 幂等规则不能移植给普通 Page。

部分页后中断保留已完成项，从首个未验证角色续跑；父验证后建子。第二次调用先 get/read/list，对账一致零创建。不重置 journal 规避 pending。

缺 create_space：未建 Space，可准备草稿。根已建而建页失败：交实际入口和已读回页，列未完成角色。历史读拒绝：不整理该源。写失败：保留草稿/状态。读回失败：保存未确认。权限信息缺失：隐私未验证。unknown 既不是成功也非确定失败。

继续其他已授权独立工作；需授权时只说明具体源/动作，不索取整个账户或电脑。不给新凭据、不更改分享、不建后台任务。

## 导出

默认 Space 为主源；Markdown 导出注明 canonical 链接、导出时间和读取范围，映射留私人目录。只读源、只写获准新目标；目标已改先比较差异。迁回保留来源身份/替代链/原日期，导出时间不变成确认日期。明确选本地为主源才改变，不自动双向同步。

依据：[Space Pages](https://learn.chatgpt.com/docs/space/pages) · [继承访问](https://learn.chatgpt.com/docs/space/collaboration#understand-inherited-access)。docs 不替代真实 schema，mock 不证明连接态。

## 受影响投影的完成门槛

可选 begin_change_set 保存主条目及受影响角色、具体读回检查、确认来源/date/basis；verify_change_role 只核机械一致性，全部角色验证才转 verified。漏页、旧值、读回失败或缺确认依据时保持 pending。函数不判断确认真实性、不授权访问；Agent 仍须读当前用户指令与实际 source。确认 basis 只能为 current_user_authorization 或 explicit_save_message，record_date/message_date 不能代替。
