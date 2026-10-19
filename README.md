# OnePersonTeamSKILLs

让一个人借助 Agent，把想法推进到可交付的成品。本仓库维护可移植的标准 `SKILL.md` 技能：流程、参考规范、脚本和示例放在同一目录，不绑定特定 Agent 或企业服务。

当前维护 **4 个 SKILL**：[`requirement-analysis`](skills/requirement-analysis/SKILL.md) 生成图文 PRD；[`technical-design`](skills/technical-design/SKILL.md) 编写技术方案；[`test-case-design`](skills/test-case-design/SKILL.md) 基于 PRD 设计多类型测试用例；[`product-development`](skills/product-development/SKILL.md) 按前置文档实施开发与验证。完整技能链为 **PRD → 技术方案与测试用例 → 开发 → 验证交付**，不自动部署、提交或推送。

四项技能共用同一任务目录和 `pipeline.json`，用相对路径、文件摘要及 PRD 版本绑定交接。测试用例设计只要求 PRD，不强制需要技术方案；开发可自动读取已登记用例。开发或测试用例技能单独调用缺前置时，先询问是否帮助完善，用户同意才补写。

## 目录

- [QuickStart：一次端到端交付](#quickstart)
- [一句 Prompt 使用任意 SKILL](#use-any-skill)
- [每个 SKILL 的详细介绍](#skill-details)
- [本地运行与验证](#local-checks)

<a id="quickstart"></a>
## QuickStart：一次端到端交付

### 先让 Agent 读到仓库

推荐把仓库下载到本地，在 Agent 中打开或授权该目录。如果尚未下载，可以自行运行：

```bash
git clone https://github.com/WayneYe912/OnePersonTeamSKILLs.git
cd OnePersonTeamSKILLs
```

不需要先安装到某款 Agent 的全局技能目录：让 Agent 显式读取 `skills/<技能名>/SKILL.md`，并按其中说明读取同目录资源即可。支持原生技能发现的 Agent 也可以按自己的机制加载完整目录；不要只复制 `SKILL.md` 而漏掉引用文件。

**“任意 Agent”指不绑定品牌，不代表没有能力要求。** 端到端文件交付需要 Agent 能读取仓库、写文件，并有渲染或浏览器检查能力；使用内置脚本还需执行命令和 Python 3.9+。没有 Python 但能写文件的 Agent 可以按规范直接生成 HTML。纯聊天 Agent 需要先收到完整技能及资源，不能只凭仓库名称获得它们，也不能声称生成了本地文件。

### 直接复制这份完整提示词

以下提示词无需补参数即可在**已经打开本仓库**的 Agent 中运行。它使用一项明确标为虚构的演示需求，贯穿仓库当前全部技能；换成真实需求时，替换“演示输入”即可。

```text
请使用当前打开的 OnePersonTeamSKILLs 仓库，完成一次从一句话需求、PRD、技术方案到本地演示开发和验证的端到端交付。

【技能发现与串联】
读取当前仓库四个实际技能及必读资源，依次执行 requirement-analysis → technical-design → test-case-design → product-development。四个阶段共用 outputs/reminder-demo/ 作为任务文档根：需求阶段生成 prd.json、prd.html 并登记；设计阶段读取 PRD 生成 technical-design.json/HTML 并绑定摘要；用例阶段自动读取同任务 PRD（技术方案可选，不强制），生成 test-cases.json/MD 并绑定 PRD；开发阶段从本轮交接及 pipeline.json 自动读全 PRD、技术方案和已登记用例，不让我重复发送材料。不把仓库 assets 示例当真实前置，不按其他任务的修改时间选文件。

【明确的虚构演示范围】
一句话需求：给团队待办加一个到期提醒。
仅开发本地模拟，不连接线上账户、真实通知、生产数据库，不宣称生产就绪。在 outputs/reminder-demo/app/ 新建演示项目，不修改技能本身和其他项目；目录已有未知内容时停止并询问。
演示技术栈指定 Python 3.9+ 标准库，使用内存模型和内置 unittest，不安装依赖。本地演示通过 python app.py 进入终端交互，支持创建待办、设置提醒、模拟时间推进、查看模拟站内通知；图文文档由前两个技能生成。
演示规则由本提示明确给定：待办有负责人、带时区截止时间、完成状态、成员访问权限和版本；提醒时间由用户指定且不得晚于截止时间；所有时间转 UTC 比较；设置须有编辑权限并校验期望版本；到期时再次检查任务版本、完成/删除状态和接收者权限，不满足则取消；同一待办提醒版本最多生成一条模拟通知；打开历史通知时检查当前权限。
模拟渠道能确定本次本地消息是否写入，不做网络重试、跨进程持久化、短信、电话、多渠道、管理者升级或真实部署。内存数据退出即清空，这是演示限制而非真实产品数据保存策略。未给的生产容量、延迟、工期等保持待确认，不能扩展到本次模拟实施范围。

【需求和技术方案】
保留原话、稳定 REQ 与 DES 编号，区分本提示确认的演示约束、设计建议、生产待确认项。写清场景、范围、契约、异常、权限、数据、验收与风险。技术方案映射 REQ → DES → 验证，明确内存模拟的保证范围，不把模拟去重表述为外部消息恰好一次送达。
成稿后分别执行内置中文表达优化，保留术语、字段、状态、条件、否定和承诺。需求文档含主流程和低保真界面/操作示意；技术方案按适用性绘制架构、时序、状态、数据流及研发依赖，不为凑图种添加无关组件。

【测试用例】
用 test-case-design 通过同任务 PRD 设计功能、边界、异常、权限、状态、回归和验收等适用用例，逐条关联 REQ 与测试条件 AC；性能、具体接口等缺标准时列待确认或说明不适用，不编 SLA、API 或错误码。每条 TC 包含前提、数据、操作、每步预期、断言、清理、优先级和自动化建议；生成阶段全部未执行。保存 test-cases.json 和 test-cases.md，校验后登记到 pipeline.json 并绑定 PRD 摘要。若单独调用缺 PRD，先问是否帮我完善，等待回复；本次已明确授权前置生成，不重复问同一许可。

【开发前门禁与实施】
将前置权威 JSON 登记到 pipeline.json，完整读取并核验路径、摘要、设计绑定版本及正文一致性。开发授权只覆盖上述明确的本地演示。新的关键建议、冲突或缺失规则先问，不能把“完善再开发”当成自动批准所有设计。若缺少 PRD/技术方案，先询问是否帮我完善；此提示已明确授权前置生成，无需重复询问已有流程许可。
通过门禁后，在 app/ 实现实际终端入口、领域逻辑与测试。包含设置冲突、无权限、旧版本、已完成、重复时间推进、历史通知权限撤销等异常，不只生成骨架、TODO 或 mock 成功截图。记录 REQ → DES → 文件/符号 → 测试。

【验证与交付】
按两文档技能的脚本检查和渲染；运行产品单元测试，并通过实际启动命令完成至少一条创建—设置—推进时间—查看通知路径。核验文档摘要未变、图文与代码规则一致；能渲染时检查桌面和窄屏，做不了的验证说明缺口。
最后交付 PRD/技术方案的 JSON/HTML、测试用例 JSON/MD、pipeline.json、app/ 完整代码和实际测试，以及 delivery.md（真实命令、结果、启动方式、REQ/AC/TC/DES 映射、演示限制与未覆盖）。生成用例与执行结果分开，未执行用例不能称为通过。未经另行要求不提交或推送 Git、不上传材料、不部署，不把本地模拟测试称为真实生产验证。
```

### 交付后应看到什么

- `outputs/reminder-demo/` 下有 PRD、技术方案的 JSON/HTML、测试用例 JSON/MD、`pipeline.json`、本地演示 `app/` 代码及测试、`delivery.md`，文件名以实际交付为准。
- 开发阶段从同任务清单读前置，不重复要求用户发送；文件变更、多个候选和旧设计绑定会阻断，不静默选旧文档。
- 两份文档说明规则与设计，代码有真实启动入口和验证；演示限制、未确认事项与未覆盖检查明确披露，不等于生产上线批准。

想先看阅读效果，可以下载并用浏览器打开仓库中的[团队待办需求分析示例](skills/requirement-analysis/assets/团队待办需求分析示例.html)。这是虚构样例，不是自动生成真实业务需求的替代品；GitHub 文件页面可能只展示源码。

<a id="use-any-skill"></a>
## 一句 Prompt 使用任意 SKILL

在 Agent 已能访问本仓库的前提下，用**路径 + 任务 + 交付物**调用，不依赖斜杠命令、专属工具名或技能市场。

### 通用一句话模板

把尖括号内容换成实际值；`<技能名>` 必须是 `skills/` 下存在的目录名。

```text
请读取当前 OnePersonTeamSKILLs 仓库的 skills/<技能名>/SKILL.md 及它要求的同目录资源，严格按该技能完成“<具体任务>”，将完整的<交付物>写入 outputs/<任务目录>/，验证后提供文件、路径和检查结果；关键缺口先问我，不编造事实，不覆盖无关文件。
```

### 当前技能可直接用的一句话

**需求分析**

```text
请读取本仓库 skills/requirement-analysis/SKILL.md 及必读资源，把“给团队待办加一个到期提醒”写成图文并茂的需求分析探索草稿，区分事实、建议和待确认项，输出到 outputs/reminder-analysis/ 的自包含 HTML，验证后交付。
```

**技术方案**（需求材料须已提供或可访问）

```text
请读取本仓库 skills/technical-design/SKILL.md 及必读资源，基于我提供的需求文档和系统材料编写可落地的图文技术方案，保留需求编号和确认状态，覆盖实现契约、异常、研发图表、测试与发布回退，输出到 outputs/technical-design/，关键缺口先问我，验证后交付。
```

**产品开发**

```text
请读取本仓库 skills/product-development/SKILL.md 及必读资源，在我授权的目标项目中按指定 PRD 和技术方案开发；端到端时从同任务 pipeline.json 自动读取前置，缺任一文档时先询问是否帮我完善，确认范围后再实施、测试并交付代码与验证报告，不自动提交、推送或部署。
```

**测试用例设计**

```text
请读取本仓库 skills/test-case-design/SKILL.md 及必读资源，基于指定或同任务 pipeline.json 中的 PRD 生成不同类型测试用例，包含具体数据、步骤、预期、断言与覆盖缺口；没有 PRD 时先询问是否帮我完善，等待回复，不强制要求技术方案，输出未执行的用例 JSON 和易读文档。
```

### 仓库不在当前目录时

把技能路径换成实际的绝对路径，例如“读取我已授权的 `/path/to/OnePersonTeamSKILLs/skills/requirement-analysis/SKILL.md`”。`/path/to/` 是示意位置，不能照抄成真实路径。

如果 Agent 没有本地文件访问能力，提供**完整技能目录及必读资源**，或让有仓库读取能力的 Agent 获取对应内容。只贴一个无法访问的 URL、只说技能名，或只上传主文件，都不能保证技能被正确执行。

单技能调用只读取该技能及其要求的资源；不要把机器上安装的其他技能误认成本仓库维护的技能。

<a id="skill-details"></a>
## 每个 SKILL 的详细介绍

本节介绍 `skills/` 下实际维护的四个技能：需求分析、技术方案、测试用例和产品开发。参考文件与脚本是各技能的组成部分，不是独立 SKILL。

### requirement-analysis：一句话需求分析

**入口**：[skills/requirement-analysis/SKILL.md](skills/requirement-analysis/SKILL.md)

**目标**：把“想做什么”写成产品、设计、研发和测试能共同评审的需求分析文档。详细体现在规则、边界、异常和验收明确，而非单纯增加字数。

#### 适合什么任务

- 从一句话需求、粗略想法或功能描述开始拆解。
- 起草 PRD、需求分析探索草稿或待评审文档。
- 补齐现有需求文档中的场景、范围、业务规则、异常和验收。
- 在不改变事实和规则的前提下，改善中文表达和阅读结构。

#### 需要什么输入

至少给出需求原话。能提供目标用户、所在产品、现有流程、权限边界、核心规则、约束、成功条件和参考材料，分析就更准确。

关键缺口会影响方案时，技能要求先提出必要问题。用户明确要探索草稿时，可以形成**有标记的建议**，未提供的信息留为待确认；不会把猜测写成已确认事实。

#### 内置完整流程

1. **理解与澄清**：读取原话和材料，复述目标，建立事实、建议与待确认台账。
2. **拆解与定范围**：梳理用户场景、触发条件、输入、操作和结果，明确本期、后续与不做事项。
3. **定义需求契约**：稳定需求编号、确认状态、优先级及理由、规则、异常与“给定／当／则”验收。
4. **绘制互补图**：主流程加界面、状态或角色示意，图文共同使用已核对的规则。
5. **独立优化表达**：先保护事实和专业术语，再去空话、翻译腔、模糊指代和重复，分开回读保真、阅读与节奏。
6. **生成、验证与交付**：输出真实文件，核查结构和图文一致性，实际查看渲染效果，如实披露未验证层。

#### 默认交付物

一份自包含 HTML 需求分析文档，内联样式和图形，浏览器离线可读。主要内容包括：

- 原始需求、需求复述、文档状态和来源。
- 用户与场景、本期范围、推荐方案和取舍。
- 功能需求、业务规则、异常恢复和验收标准。
- 数据与权限、质量要求、发布前提和衡量口径。
- 风险、依赖和阻断实施的待确认事项。
- 流程图和明确标注的低保真界面等互补示意。

使用内置渲染器时，先由 Agent 完成分析并写成 JSON，再生成 HTML。脚本不会理解一句话、补业务规则或代替产品判断。

用户明确指定 Word、PDF、在线文档或 Markdown 时，技能要求尊重指定格式，借助 Agent 所在环境的能力完成；**仓库没有内置这些格式的转换器或在线发布服务**，不能把它们描述为开箱即用能力。

#### 中文表达优化已经是技能的一部分

无需另装或调用文本优化技能。内置规范覆盖：

- 原话、数字单位、术语、编号、状态、条件、否定、因果和承诺保护。
- 先读整篇含义，再处理句段；清楚准确的内容不为改而改。
- 把名词化空架子还原为动作，统一称谓，删除套话与同义反复。
- 避免没有来源的权威、效果宣称、造词和凑数式排比。
- 检查自然停顿与句间节奏，保持专业书面语，不把术语换成含糊大白话。
- 正则只提示疑点，不自动改稿，也不以命中数评价业务真实性。

#### 文件和工具各自负责什么

- [references/document-contract.md](skills/requirement-analysis/references/document-contract.md)：文档结构、JSON 数据契约、来源和状态标记、需求及图形结构。
- [references/writing.md](skills/requirement-analysis/references/writing.md)：内置中文优化规范及需求文本前后对照。
- [references/visuals.md](skills/requirement-analysis/references/visuals.md)：图形选型、图文一致性、窄屏与打印检查。
- [scripts/render.py](skills/requirement-analysis/scripts/render.py)：先校验 JSON，再生成内联 CSS/SVG 的离线 HTML；支持 `flow` 和 `wireframe`，默认拒绝覆盖已有文件。
- [scripts/check.py](skills/requirement-analysis/scripts/check.py)：只读检查结构、引用和状态，输出字段级表达提醒，不修改输入。
- [assets/example.json](skills/requirement-analysis/assets/example.json)：完整的虚构分析样例，演示数据粒度和标注方式。
- [assets/团队待办需求分析示例.html](skills/requirement-analysis/assets/团队待办需求分析示例.html)：由示例数据生成的可阅读成品。
- [tests/test_skill.py](skills/requirement-analysis/tests/test_skill.py)：回归测试，覆盖契约、链接、转义、异常数据、状态与来源、覆盖保护、迁移和脚本退出码。

#### 能力与边界

- 核心流程不依赖指定 Agent、MCP、账号或外部 Skill；辅助脚本只用 Python 标准库，要求 Python 3.9+。
- 内置图形支持流程和低保真界面；状态或角色关系可用流程数据表达。复杂泳道或稠密关系须拆图，或由 Agent 生成更合适的确定性图形，不能硬塞默认布局。
- 输出有打印样式，但每次生成文档的打印分页仍需实际检查，不能只因存在样式就宣称通过。
- 不虚构用户研究、数字、接口、成本、排期或优先级共识，不把建议当团队批准。
- 不自动开发、上线、上传、创建云文档、安装全局依赖或修改产品代码。
- 结构校验不证明业务事实正确、来源支持结论、验收充分或图形好读，仍需 Agent 逐层复核。

### technical-design：可落地技术方案

**入口**：[skills/technical-design/SKILL.md](skills/technical-design/SKILL.md)

**目标与输入**：接收需求分析、PRD、用户故事及现有代码/系统材料，把需求映射到实现契约、异常处理、验证和实施依赖。可直接单独使用，不依赖安装需求分析技能；串联时保留上游编号、来源和确认状态。

**核心内容**：目标与非目标、现状证据、真实备选与决策理由、组件职责、接口与数据契约、事务与并发、幂等重试、部分成功和未知结果、安全权限、容量估算、测试、兼容迁移、发布停止与回退、实施拆解。不会默认引入队列或微服务，也不会编造真实接口、技术栈、工期和性能。

**图文与表达**：默认自包含离线 HTML，内置中文优化，先说清作用再给精确机制，术语保留原词、首次准确解释。支持九类确定性图：架构、流程、时序、ER、状态、数据流、部署、研发依赖、泳道。按需求适用性选图，不强行凑九张；图与 `REQ → DES → tests` 保持一致。

**辅助资源**：

- [references/design-contract.md](skills/technical-design/references/design-contract.md)：完整方案与 JSON 契约、来源状态、需求设计测试映射。
- [references/writing.md](skills/technical-design/references/writing.md)：通俗但保真的技术表达，不改变事务、去重、重试与承诺。
- [references/diagrams.md](skills/technical-design/references/diagrams.md)：九类图的细节、布局与核验要求。
- [scripts/contract.py](skills/technical-design/scripts/contract.py)：结构、来源、需求覆盖、图端点和依赖无环校验。
- [scripts/check.py](skills/technical-design/scripts/check.py)：只读结构与表达提醒，不自动改稿。
- [scripts/render.py](skills/technical-design/scripts/render.py)：标准库 HTML/SVG 渲染，默认拒绝覆盖已有文件。
- [assets/example.json](skills/technical-design/assets/example.json) 与 [图文技术方案示例](skills/technical-design/assets/团队待办技术方案示例.html)：虚构提醒设计，展示全部九类图，不代表现有系统。
- [tests/test_skill.py](skills/technical-design/tests/test_skill.py)：图形、映射、来源、异常数据、安全转义、迁移与命令验证。

**限制**：Python 3.9+ 仅辅助校验和渲染，无 pip/npm/CDN 依赖；无 Python 时 Agent 可按规范直接生成。复杂图需拆分或自绘准确 SVG，不是无限布局 UML 引擎。特定格式依赖宿主能力，未提供现状或关键约束时先澄清，允许探索稿才保留候选方案。结构通过不证明业务、算法、性能或真实运行正确；不自动实施、迁移、压测、部署或上线。

### product-development：基于 PRD 与技术方案开发

**入口**：[skills/product-development/SKILL.md](skills/product-development/SKILL.md)

**输入与联动**：指定 PRD、技术方案、目标代码项目及实施范围。端到端从本轮已验证交接或同任务 `pipeline.json` 自动读取前两技能结果，保留来源、状态、REQ/DES 和版本。不会在其他任务按时间挑最新文档，也不会把技能 assets 样例当真实输入。

**缺文档行为**：单独使用缺 PRD 或设计时，先问“是否要我先帮你完善缺少的 PRD 和技术方案，确认开发范围后再开始开发？”用户同意才进入前置技能；使用已有文档则请求可访问材料；拒绝则不开发。只缺一份时保留另一份，不重复索要。“补写许可”不是自动批准所有新设计，关键缺口仍需确认。

**实施流程**：核对文档和现状 → 明确项目与基线 → REQ/DES 到代码测试映射 → 按设计实现最小完整路径 → 单测/构建/集成/实际入口验证 → 交付代码、测试和 delivery.md。保持用户已有改动和项目栈，设计变更同步文档；失败、权限、并发、未知结果必须按范围验证，mock 不冒充真实集成。

**辅助资源**：

- [references/handoff.md](skills/product-development/references/handoff.md)：同任务清单、选择顺序、版本绑定、缺失询问与结果分流。
- [references/development.md](skills/product-development/references/development.md)：实施边界、基线、真实入口验证和交付报告规范。
- [scripts/pipeline.py](skills/product-development/scripts/pipeline.py)：标准库登记/解析相对前置路径、摘要和 PRD—设计版本；只做文件门禁，不生成文档、代码或批准。
- [tests/test_handoff.py](skills/product-development/tests/test_handoff.py)：缺失、歧义、旧版本、路径越界、符号链接、状态保护、脚本迁移和上游联动测试。

**输出与限制**：授权项目的真实代码、相关测试和运行配置、验证与缺口报告。具体语言、框架、目标项目和关键验收未知时先澄清，不偷偷默认。Python 仅辅助文件交接；实际开发需要宿主代码编辑与项目运行能力。默认不提交、推送、部署或执行生产迁移，任务报告与业务文档不进公开提交。

### test-case-design：基于 PRD 的多类型测试用例

**入口**：[skills/test-case-design/SKILL.md](skills/test-case-design/SKILL.md)

**输入与联动**：指定 PRD 或本次任务前置 PRD，技术方案可选。使用同任务 `pipeline.json` 或明确交接自动读取，支持 `resolve --only-prd`，不强制需要技术方案，不跨任务猜最新，也不读技能样例冒充用户文档。

**缺 PRD 行为**：单独调用没有可用 PRD 时，先问“是否要我先帮你完善 PRD，再基于它生成测试用例？”用户同意才读取 requirement-analysis 补写；选择已有则请求有效材料；拒绝就停止。新生成规则未确认时预期保持待确认，不升级为确定验收。

**设计内容**：支持功能、边界、异常、权限、安全防护、接口、状态、兼容、可访问性、性能、可靠性、回归和用户验收等类型；另行区分层级和设计方法。每条 TC 关联 REQ/AC，包含优先级理由、前提、具体数据、逐步操作与预期、断言、清理和自动化建议。缺阈值、接口或设备范围不编造，列覆盖缺口或不适用理由。

**输出与工具**：默认完整 test-cases.json 和 test-cases.md。所有生成用例未执行；用例定义、自动化实现与运行结果分开。绑定 PRD 摘要后开发可读取已登记 test_cases。

- [references/test-design.md](skills/test-case-design/references/test-design.md)：类型、方法、风险与评审。
- [references/case-contract.md](skills/test-case-design/references/case-contract.md)：用例字段、条件映射、覆盖和交接。
- [scripts/cases.py](skills/test-case-design/scripts/cases.py)：标准库只读校验及安全 Markdown 渲染，不执行产品测试。
- [assets/example-prd.json](skills/test-case-design/assets/example-prd.json)、[assets/example-cases.json](skills/test-case-design/assets/example-cases.json) 与 [完整用例示例](skills/test-case-design/assets/测试用例示例.md)：虚构 PRD 和多类型用例示范。
- [tests/test_cases.py](skills/test-case-design/tests/test_cases.py)：契约、未执行状态、覆盖、版本、PRD-only 和开发读取兼容测试。

**边界**：只设计用例，不连接真实产品、执行压力/破坏性测试或自动运行请求；安全仅用于合法防护验证。结构校验与条件映射不代表语义正确、覆盖充分或测试通过。缺环境/实现依据时单元层和实际自动化仍待评估。

### 同任务文档交接

前置 PRD、技术方案和测试用例在端到端时登记到同任务 `pipeline.json`。技术方案与 test_cases 都绑定 PRD 摘要；普通 resolve 供开发读取必需文档和已登记用例，`--only-prd` 供用例设计单独读取 PRD。更新 PRD 后旧设计与用例绑定保留为失效证据，重新评估登记才继续。完整协议见[前置交接规范](skills/product-development/references/handoff.md)。登记和哈希匹配不等于业务确认、开发批准或测试通过。

<a id="local-checks"></a>
## 本地运行与验证

以下命令在**仓库根目录**运行。日常使用只需上面的 Prompt，Agent 应自行完成分析、调用和交付；这里的命令用于复现渲染或维护技能。

### 用仓库示例验证工具链

下面两个调用不会修改示例数据。渲染器新建输出文件，若目标已存在会拒绝覆盖；需要重跑时换一个文件名。仅在确认要更新同一产物时使用 `--force`。

```bash
python3 -B skills/requirement-analysis/scripts/check.py skills/requirement-analysis/assets/example.json
python3 -B skills/requirement-analysis/scripts/render.py skills/requirement-analysis/assets/example.json --output requirement-analysis-demo.html
```

直接用浏览器打开 `requirement-analysis-demo.html`。这只是工具链演示；真实需求的分析 JSON 必须由 Agent 按[数据契约](skills/requirement-analysis/references/document-contract.md)重新编写，不能直接复制示例当成结果。

Windows 中若命令名为 `python`，将 `python3` 替换为 `python`，参数不变。无需 `pip install`、`npm install` 或联网加载图表库。

### 运行回归测试

```bash
python3 -B -m unittest discover -s skills/requirement-analysis/tests -v
```

### 技术方案示例与回归

同样从仓库根目录执行：

```bash
python3 -B skills/technical-design/scripts/check.py skills/technical-design/assets/example.json
python3 -B skills/technical-design/scripts/render.py skills/technical-design/assets/example.json --output technical-design-demo.html
python3 -B -m unittest discover -s skills/technical-design/tests -v
```

这是九种研发图的虚构示例。真实技术方案须以实际需求和系统材料重新分析，不能直接复制样例规则。`technical-design` 的检查、渲染退出码与下方说明一致。

### 开发技能联动测试

```bash
python3 -B skills/product-development/scripts/pipeline.py --help
python3 -B -m unittest discover -s skills/product-development/tests -v
```

登记与解析示例见交接规范：`register` 只更新同任务清单；`resolve` 返回 `ready`/0、`needs_input`/1 或 `invalid`/2。缺文件或歧义由 Agent 询问用户；非法/旧版本先修复。`ready` 只通过文件门禁，仍须读全 PRD/设计、确认目标项目及业务一致性后开发。

### 测试用例示例与回归

```bash
python3 -B skills/test-case-design/scripts/cases.py check skills/test-case-design/assets/example-cases.json
python3 -B -m unittest discover -s skills/test-case-design/tests -v
```

用例技能的 `render` 子命令可输出完整 Markdown；格式和字段见用例契约。`check` 的 0/1/2 分别为结构通过、不合格、读取/参数错误。检查不执行产品测试，生成用例全部未执行；技术方案不是 PRD-only 模式的必需输入。

### 正确解读检查结果

- `check.py`：退出码 `0` 表示结构合格，`1` 表示结构不合格，`2` 表示读取或参数错误。`writing_advice` 是待判断的表达提醒，不自动阻断或改稿。
- `render.py`：退出码 `0` 表示完成生成，`2` 表示参数、读取、结构或写入错误；成功生成不等于视觉与业务验证通过。
- 回归测试验证代码行为；具体需求仍需核对事实、规则、异常、图文一致性及真实阅读效果。

所有最终产物应明确文件路径、打开方式、完成的验证与剩余缺口。文件存在不是交付完成的唯一标准。
