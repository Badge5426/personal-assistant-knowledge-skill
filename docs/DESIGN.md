# 设计依据和范围

Space-first：显式调用在授权范围下建立真实 Space、七类目录和工作台；安装只复制文件。用户稳定档案、事件日志、精选结论分层，证据和纠错关系保留。每实体一个主来源，Markdown 可选迁移。

工具由执行环境提供，本包没有 Space API 实现。标准库助手只是私人回执账本，不借文档声称接口已暴露。Codex/ChatGPT/项目分开，摘要和搜索不全量，不读取禁止目录或绕过拒绝。

官方依据：

- [Build skills](https://learn.chatgpt.com/docs/build-skills)：实际 Skill 文件和客户端发现。
- [Space Pages](https://learn.chatgpt.com/docs/space/pages)：块编辑、实际 child Pages、来源引用。
- [继承访问](https://learn.chatgpt.com/docs/space/collaboration#understand-inherited-access)：Space/父页共享可继承，单页位置不证明私有。
- [Codex app-server](https://developers.openai.com/codex/app-server#threads)：官方 thread/list/read/turns 等能力，当前连接没有该接口时不自造。
- 当前工具 schema：create_space 无幂等键；普通 Page 不假定 Site 幂等行为；list_pages 缺 partial_results 表示未知；修改使用实际块/hash/可用 sequence。

仅阅读官方文档，没有复制第三方源码或执行陌生依赖。所有新流程、脚本和匿名夹具为原创 MIT。真实工具测试在独立虚构 Space，私人回执和账号身份留在公开包之外。
