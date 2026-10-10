# 个人助手知识库 Skill

Native RC3 首次结果候选，待本轮独立审核与发布；下方安装 pin 仍是已发布 Native RC2，不包含本候选改动。本轮增加“你是谁＋下一步怎么做”的用户可见结果：真实入口、有依据的介绍、一个优先问题、最多三项具体建议。零/少资料先给简单补充动作，未知不编造，建议不成为用户事实。实际三来源到私人 Space 的完整真实验收尚未开始。

Native RC2 已通过独立复审并发布。默认发现历史对话、已保存个人记忆、已有个人资料/项目文档；先读可访问已有资料，去重并核对较新明确纠正，填已知内容后再问缺项。新增桌面 Work 回执适配和匿名三来源测试，无新连接器或权限。本机一条获准真实线程的 4 页返回文字范围已读完；三类混合验证使用匿名夹具，全账户全集导入尚未验收，近期列表没有游标，不能称全量。

显式首次调用后，在当前已连接账号建立私有个人助手 Space、七类目录和工作台，整理授权可读的对话与项目，保留来源、日期、未知和纠错关系，再用最多三项补充问题完善档案。日常记录逐渐变成长期助手上下文。

需要当前客户端具备 Space 工具，并由用户显式调用。以下既有验收属于 Space RC2.1 基线：已在正常 Work 任务显式读取已安装 SKILL.md，使用 3 个完整匿名来源验证空白建库、资料整理、逐页读回、增量维护、受控续跑和重复调用不新增页面。安装本身不运行建库或增加权限。客户端自动发现、独立新模型、UI 渲染，以及真实账户历史发现到逐会话整理完整流程尚未验收；三个匿名来源不代表全部聊天。基线源码与上述验收证据已通过独立范围审计，Native RC2 新增适配与冲突修复也已通过独立复审，限制见 [测试报告](docs/TEST_REPORT.md)。

## 实际入口

`skills/maintain-personal-context/SKILL.md` 是安装入口。默认 Space 为主来源；本地 Markdown 为明确选定的导出、迁移或独立维护方式。

七类是我是谁、经历技能、资源协作、目标、日常项目、成果复盘、来源纠错。根页加七类、工作台、稳定档案、日常日志、精选长期结论、建库与覆盖记录，共 13 个普通 Page。实际父子位置见 [建库流程](skills/maintain-personal-context/references/space-onboarding.md)。

用户事实、助手建议、第三方说法和推断分开；日期未知不编造。稳定档案引用当前源条目，日志保存临时状态，精选长期结论须确认。纠错保留旧证据和替代链，不把一次心情变成人格。

## 安装

支持本地 skills 的 Codex CLI/IDE/桌面客户端；项目发现路径为 `.agents/skills`。目录安装不等于 Web/手机插件，本包没有构建“一键通用插件”。有些客户端不提供 Space 或完整历史接口，安装不会开通这些能力。

在完整源码包根目录执行，PROJECT 换成你选定项目的绝对路径：

```sh
PROJECT="/absolute/path/to/your-project"
python3 scripts/install.py install --dest "$PROJECT/.agents/skills"
```

只复制本 Skill，不扫描资料、不改配置、不安装依赖；已有同名目录拒绝覆盖。若客户端未发现变化，在选定项目内刷新/重启并显式调用。Python 3.9+，标准库即可；只用文稿流程不必运行脚本。

公开仓库：[Badge5426/personal-assistant-knowledge-skill](https://github.com/Badge5426/personal-assistant-knowledge-skill)。以下安装固定到已通过独立复审、公开源码核对和干净安装的 Native RC2 代码提交 [de32ff8133c895c7cd10699bc824d37c87efc268](https://github.com/Badge5426/personal-assistant-knowledge-skill/tree/de32ff8133c895c7cd10699bc824d37c87efc268)。匿名公开克隆核对全部 44 文件，已有官方安装器从该固定 commit 下载的 27 个 Skill 文件与已审版本逐字节一致；Python 3.9/3.11 各 123 项测试通过。后续 README-only 文档提交不改变此安装目标。

已带系统 skill-installer 的客户端，先进入选定项目目录，再按下面命令安装已核验的固定代码提交：

```sh
PROJECT="$PWD"
VERIFIED_COMMIT="de32ff8133c895c7cd10699bc824d37c87efc268"
INSTALLER="${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py"
python3 "$INSTALLER" --repo Badge5426/personal-assistant-knowledge-skill \
  --ref "$VERIFIED_COMMIT" --path skills/maintain-personal-context \
  --dest "$PROJECT/.agents/skills" --method download
```

系统 installer 不属于本包。没有脚本时使用已有 $skill-installer 或完整源码本地安装，不创建新凭据或安装依赖。官方：[Build skills](https://learn.chatgpt.com/docs/build-skills)。

## 首次调用

```text
先读取项目内 .agents/skills/maintain-personal-context/SKILL.md 及引用规则，
再按该 Skill 执行本次授权范围，在当前已连接账号建立我的私有个人助手 Space。
整理本次授权可读的历史对话、已保存个人记忆、已有个人资料和项目文档；ChatGPT 对话只在我也授权该范围时加入。
先报告实际入口与读取范围，不读取未授权文件、不改变分享。
把有来源的内容保存到七类页与工作台，完成后交付实际根页和覆盖缺口，再问最多三项必要补充。
直接展示“你是谁＋下一步怎么做”：有来源的称呼/简介/技能资源、一个有依据的优先问题，
最多三项建议（依据/第一步/需确认条件）；零或少资料则说明提供什么/为什么/怎么口述或粘贴，已知不重问。
私人建库状态放在我已指定的仓库外私人目录；未知日期留未知。
```

已支持 Skill 名称发现的客户端也可使用 `$maintain-personal-context`，但名称发现尚未验收。上面的实际文件路径是可靠的显式加载入口；安装后只读文件，再按当前工具与本次授权执行。

已明确的授权不用重复确认。范围/目标仍不明且影响访问时只补问具体缺项。新 Space 会检查实际私有可见性，未确认私有不写真实资料。未开通/缺连接/缺权限则指出失败阶段，保留草稿；不能把本地草稿说成 Space 已建立。

Codex 与 ChatGPT 分别发现；关键词搜索、摘要和近期列表不等于所有聊天。按真实 cursor/归档权限读取，保存去重状态与继续位置，总量未知明确写 unknown。项目路径是元数据，不授权文件遍历。详见 [历史覆盖](skills/maintain-personal-context/references/history-coverage.md)。

普通桌面 Work 若已有 codex-app-tools，可直接用 list_threads/read_thread/list_archived_threads 读取获准的具体线程；实测 native 返回可含用户原话和助手正文，不能统一称摘要。现有 [native 适配](skills/maintain-personal-context/references/native-history.md) 说明 host、游标、消息 ID、日期和 memories 边界。纯本地 native_history.py 只规范化已经读取的回执，不调用工具或写页；现成路径无需新增用户权限。工具未暴露的客户端不能靠安装此 Skill 获得同样入口。

## 权限与数据流

安装文件 → 用户显式调用 → 实际工具发现和授权范围 → 私有 Space 目录与已读来源 → 事实卡/日志/候选结论 → 写后读回 → 精准补充。历史中的扩权/上传指令只作资料，不执行。

真实资料、私人 ID、来源、计划、回执和导出都在公开包外。公开仓库只包含原创通用流程、空白模板、虚构成人夹具和代码。没有 API/凭据抓取实现；`native_history.py` 只解析已有合法回执，`space_state.py` 只保存本地收据，Agent 使用当前真实工具读取历史及执行 Space 动作。`context_store.py` 是可选本地 Markdown 工具，不自己上传。产品/连接本身的数据政策仍适用，本包不承诺“资料永远不离开本机”。

用户未授权分享/发布时不公开知识库，不改账号权限。没有连接不伪造页面，也不以申请全量账户权限解决一个缺口。本包不建日程、自动任务或 keep-updated 服务。

可选 `first_run.py` 只格式化 Agent 已判读的标注与建议，不调用工具、不写页、不获取权限；输入放仓库外私人目录。它复用证据分级/纠错，并检查建议依据、第一步和确认条件，最多三项本轮动作。实际入口和权限仍须真实工具验证，结构校验不能替代。用法见 [首次结果](skills/maintain-personal-context/references/first-run-result.md)。

## 重复调用与故障

重读私人映射及实际页面再续跑；同名不认领，手改保留，冲突用当前 block/hash/sequence 重读重建。create_space 没有幂等键，未知响应先查证，不能盲重试。普通 Page 也不假设拥有 Site 幂等保障。

真实 list_pages 可能省略 partial_results，缺失表示完整性未知；即使 next_cursor=null 也不据此保证唯一或不存在。找到了已有原始创建回执可核对后续接；只有标题、缺乏同一操作证据则精准询问，不能重复创建。

根已建而分类失败：交真实根和已完成页，列剩余角色。写入未读回：保存未确认。某源无权限：跳过该源并报告，不绕过拒绝。分享信息不完整：隐私未验证，不写真实资料。真实失败与模拟故障分别标注。恢复及可选私人账本见 [Space 保存与恢复](skills/maintain-personal-context/references/space-output.md)。

## 本地迁移选项

明确选择 Markdown 为主源或导出时使用 [本地规则](skills/maintain-personal-context/references/local-helper.md)。导出记录 Space 来源和时间，保留纠错关系，时间不改成确认日期。两处都改过先比较，不能自动双向覆盖。Space 缺工具时，用户可选择本地替代，但交付仍要写“未完成 Space”。

## 卸载和升级

本包 installer 安装后，在保留的完整源码根目录：

```sh
python3 scripts/install.py uninstall --dest "$PROJECT/.agents/skills"
```

它验证安装标记及未改动文件，将仅此 Skill 移到 `$PROJECT/.agents/.personal-context-uninstalled` 的唯一备份。修改过/无标记就拒绝自动移动，保留原目录。

系统 skill-installer 只复制 Skill，不带本包安装标记或根 scripts/install.py，不能用上述 uninstall。先核对手改内容，将仅 `$PROJECT/.agents/skills/maintain-personal-context` 完整移到 skills 外的唯一备份目录，如 `$PROJECT/.agents/skill-backups`；不静默删除、不覆盖备份。

恢复前确认原目录不存在，再移回选定完整备份。升级先保留旧安装再装新审核版，有手改先保留副本并核对。卸载仅移除 Skill，不删除 Space、私人状态或导出；清理这些资料需独立明确操作。可恢复移动不等于擦除。当前本地 helper 可读取旧合法记录；旧代码不保证理解新历史字段，不混用覆盖。

## 可复现验证

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_package.py
```

本地 46 项 + Space 账本 29 项 + native 历史 31 项 + 三来源 17 项 + 首次结果 10 项 = 133 项离线测试。新增匿名 native 返回结构验证分页、host、消息身份与作者、日期、纠错保留、截断、未知及输出保留；三来源夹具验证同一事实合并出处、memory 不增加直接证据、较新明确纠正优先及已知项不重问。首次结果回归验证零/稀少/丰富资料、未知/冲突不升级、建议三要素、已知不重问及输入不被建议改写。匿名测试与真实只读提炼分开，均不证明本轮已写入真实 Space；当前结果及基线连接态证据见 [测试报告](docs/TEST_REPORT.md)。审核按 [八项验收](docs/REVIEW_GUIDE.md)。测试不要求新账户权限或依赖安装。

## English

Space-first personal-context skill; requires available Space tools and explicit invocation. Read the installed `.agents/skills/maintain-personal-context/SKILL.md` and its references first. Installation copies files only and grants no permissions. Explicit normal-Work loading with three complete fictional sources validated blank construction, organization, readback, incremental maintenance, controlled resume and repeat calls without new pages. Automatic discovery, a fresh independent model, UI rendering and the complete real-account history workflow remain unverified. Search hits and summaries are not all chats. Local Markdown is an explicit migration/export option. Python 3.9+, standard library only.

Native RC2 passed independent review and is published. Discover authorized conversation history, existing memories and saved personal/project materials by default. Merge provenance, keep summaries graded, check newer explicit corrections, fill known content, then ask only missing or conflicting details. Optional local helpers call no API and do not write Space. The public pin above targets the verified Native RC2 code commit. One authorized local thread was read through four returned text pages; mixed-source tests use fictional fixtures, and full-account import remains unverified.

## 许可

原创文件使用 MIT，见 LICENSE。没有复制第三方实现或运行陌生仓库代码；官方文档仅为行为依据。详见 [设计依据](docs/DESIGN.md)。
