# 个人助手上下文 Skill

把“我是谁”和用户选定的日常记录，逐渐变成有来源、能确认、能纠错的长期助手上下文。重点是助手理解个人的经历、资源、目标与项目，不是收集百科资料。

公开包只含原创通用流程、空白模板、虚构成人样例和本地工具。真实资料、计划和备份放在此仓库之外的私人目录。安装不会获得全部聊天、电脑文件或 app 权限。

## 包含什么

`skills/maintain-personal-context/SKILL.md` 是实际安装入口。其 `references/` 包含维护、Space 输出与可选本地工具规则，`assets/templates/` 是空白模板，`examples/` 是虚构样例。
`scripts/install.py` 仅安装/卸载此包；`tests/` 可离线重跑，无需安装第三方依赖。

七类：我是谁 / 经历技能 / 资源协作 / 目标 / 日常项目 / 成果复盘 / 来源纠错。
三个层：稳定档案 / 指定日常日志 / 精选长期结论。
每条重要内容区分事实、推断、建议；来源、事件日期、生效日期、确认日期分别保留。未知不编造，明确纠错后旧说法被替代，不再当当前事实。

## 适用客户端

独立 Skill 适用于支持本地 skills 的 ChatGPT 桌面端、Codex CLI、IDE 扩展；本包的目录安装验收针对 Codex 本地发现路径。桌面产品若界面不同，以其 Skills 入口和实际发现情况为准。
不能声称本包可在 Web/手机“一键通用安装”。Web/手机的插件分发是另外一条产品路径，本版没有构建插件。
目录格式可读取不等于模型已经行为验收；首次安装后还应在实际客户端调用并检查结果。

官方：[Build skills](https://learn.chatgpt.com/docs/build-skills)。Codex 的本地发现位置包括项目 `.agents/skills` 与用户 `~/.agents/skills`。一些旧安装器默认 `~/.codex/skills`，本指南通过显式 `--dest` 使用当前项目路径。

## 本地安装（无需联网）

先取得经审核的完整源码包、检查清单与代码。终端进入包根目录，将 PROJECT 改为你要使用 Skill 的项目绝对目录；PRIVATE 为仓库外的私人资料目录。勿把真实资料放进公开仓库。

```sh
PROJECT="/absolute/path/to/your-project"
python3 scripts/install.py install --dest "$PROJECT/.agents/skills"
```

安装器只复制 `maintain-personal-context`，不改配置、不扫描资料、不安装依赖；已有同名目录会拒绝覆盖。不会自动选择或修改用户全局安装位置。
当前 Codex 会检测技能变化；若未出现，在项目内重启客户端/新建会话，再显式调用 `$maintain-personal-context`。脚本只能验证目录与完整性，不能假报 UI 已加载。

已发布仓库：[Badge5426/personal-assistant-knowledge-skill](https://github.com/Badge5426/personal-assistant-knowledge-skill)。以下安装固定到已审核并完成干净安装与实际调用验证的代码版本 [3fd45cd568f0fefacfeee27daf78f892459d4502](https://github.com/Badge5426/personal-assistant-knowledge-skill/tree/3fd45cd568f0fefacfeee27daf78f892459d4502)；后续 README 文档提交不改变此安装目标。

在支持 skill-installer 的 Codex 中，可复制：

```text
$skill-installer 请从 https://github.com/Badge5426/personal-assistant-knowledge-skill 的 commit 3fd45cd568f0fefacfeee27daf78f892459d4502 安装 skills/maintain-personal-context 到当前项目的 .agents/skills；先核对当前项目绝对路径，不要覆盖已有同名 Skill。
```

使用已有系统 installer 时，先在终端进入你选择的项目目录，再执行：

```sh
PROJECT="$PWD"
INSTALLER="${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py"
python3 "$INSTALLER" \
  --repo "Badge5426/personal-assistant-knowledge-skill" \
  --ref "3fd45cd568f0fefacfeee27daf78f892459d4502" \
  --path "skills/maintain-personal-context" --dest "$PROJECT/.agents/skills" \
  --method download
```

系统 installer 不是本包的一部分；以上路径使用 CODEX_HOME 或其默认目录。若你的客户端未带此脚本或位置不同，使用上面的 Codex 安装指令，或取得完整源码后按本地安装步骤操作。此包不安装依赖，也不改变下载或账号权限。

## 最小起步

“使用 $maintain-personal-context，根据这份自我介绍起草我的个人档案。未知留空，按七类整理，先给我确认，真实文件放到我指定的私人目录。”

开始只要自我介绍、一个私人存放位置、当前希望解决的问题。不要求填满七类、每天打卡或预建大量页面。
明确写入某条或更正某条已是对该项确认，不重复询问；其他长期候选仍待确认。一次情绪不升级为人格，助手建议不变成用户承诺。

可直接维护模板 Markdown；若需要防重、防覆盖工具，用：

```sh
PRIVATE="/absolute/path/outside/public-repo/my-private-context"
SCRIPT="$PROJECT/.agents/skills/maintain-personal-context/scripts/context_store.py"
python3 "$SCRIPT" --root "$PRIVATE" init
```

然后按 [本地工具格式](skills/maintain-personal-context/references/local-helper.md) 生成私有输入与计划，查看具体变化后按已授权项 apply。工具不自己判断什么事实应被确认，必须由实际用户指令支撑。

## Space、权限与数据流

本次已验证的主体是本地 Markdown 个人助手 Skill，包括安装、维护和匿名行为。Space 部分仅提供可选输出规则：须有本次会话可用的读写工具、既有账号与目标页权限，以及明确的目标页或容器。连接状态下的完整流程尚未验收，不能称为“一键自动建立 Space 知识库”。未开通、无连接或缺权限时交付本地草稿，如实报告未建/未更新页面。
外部文件需对应 app 连接与文件权限，不能靠安装 Skill 获得。每个实体只有一个主来源；导出副本记录来源和时间，冲突先比差异，未知创建结果先查证，不能重复建页。
Page 写“每周更新”不会创建定时任务。本版无后台、自动日程、网络请求或 Space API 实现。

数据流：用户选择的材料 → 当前 Agent 会话 → 草稿/候选 → 明确确认的私人 Markdown →（仅另有权限与授权时）选定 Space 输出。
本地脚本不上传任何内容；Agent 会话与第三方 app 的数据处理仍受所用产品/连接政策控制，这不是“资料永远不出本机”的保证。

官方：[Space 开始使用](https://learn.chatgpt.com/docs/space/getting-started) · [Agent 与计划验证](https://learn.chatgpt.com/docs/space/agents)。

## 卸载与迁移

```sh
python3 scripts/install.py uninstall --dest "$PROJECT/.agents/skills"
```

卸载将校验未修改的安装移到 skills 目录之外、上级目录的 `.personal-context-uninstalled` 备份，可恢复；真实私人资料保持原位。已手改的安装拒绝自动移动，应自行检查并移走明确的 Skill 文件夹。
若客户端仍缓存旧技能，重启/刷新。可恢复卸载不等于安全擦除。
迁移时复制完整私人目录（包括 `.context` 格式状态和备份），核对文件后重新指定主来源。只有 Markdown 时，将其作为普通文稿读取/整理并保留来源；当前工具没有 Markdown-only 导入恢复命令，不能对非空目录直接 init。不要把私人数据提交到此 repo。

## 故障与可复现验证

Python 需要 3.9+；不需 pip/npm 安装。只取得纯文本 Skill 的用户可以不运行脚本。
已有目标/计划文件：拒绝覆盖，选新计划名或查看已有副本。
文件哈希变化、管理块手改：拒绝写入，保留原文；重读差异并做新计划。
未完成事务：检查私人备份，按工具说明 recover；恢复不会覆盖后续人工编辑。
权限拒绝：保留可读草稿，指出具体目录/页面动作；不更改权限或索取宽泛授权。
符号/硬链接内容文件不支持。多个文件写入不承诺绝对原子性；有备份、逐文件读回和中断恢复。
未知/无来源/未确认：不进入已确认长期事实；补依据或留为候选。

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_package.py
```

测试覆盖空白构建、首次虚构档案、增量/重复、纠错、未知状态、人工编辑、冲突、权限错误、事务恢复、安装/卸载与公开包规则。规则检查不是完整隐私审计或真实 Space 写页验收。详见 `docs/TEST_REPORT.md` 与 `docs/REVIEW_GUIDE.md`。

## English

A local personal-context skill: selected materials, confirmed profile, daily logs, and curated long-term conclusions with sources and correction history. Python 3.9+, standard library only. Use an explicit project `.agents/skills` destination and keep private output outside this repository. Installation grants no account permissions. The verified scope is local Markdown. Optional Space rules require available tools, existing permissions and an explicit destination; the connected workflow has not been fully validated. Standalone folders are not a web/mobile plugin. See the Chinese guide above for installation, reversible removal, failure handling and reproducible tests.

## 许可

原创文件使用 MIT，见 LICENSE。未复制第三方实现或安装陌生仓库依赖；官方文档只作行为/兼容性依据。参考与范围见 [设计依据](docs/DESIGN.md)。
