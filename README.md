# OnePersonTeamSKILLs

让一个人借助 Agent，把想法做成可交付的成果。这个仓库维护标准 `SKILL.md` 技能，把流程、参考规范、脚本和示例放在同一目录，方便不同 Agent 使用，不绑定特定 Agent 或企业服务。

当前维护 **4 个 SKILL**。用 [`requirement-analysis`](skills/requirement-analysis/SKILL.md) 生成图文 PRD，用 [`technical-design`](skills/technical-design/SKILL.md) 编写技术方案，用 [`test-case-design`](skills/test-case-design/SKILL.md) 根据 PRD 设计多类型测试用例，再用 [`product-development`](skills/product-development/SKILL.md) 按文档开发和验证。完整流程为 **PRD →（技术方案 ∥ 测试用例，并行生成）→ 汇合核验 → 开发 → 验证交付**。技能不会自动部署、提交或推送。

四项技能把同一任务的文件保存在同一目录，通过 `pipeline.json` 记录相对路径、文件摘要和 PRD 版本，供后续阶段自动读取。测试用例只需要 PRD，无需等待技术方案；开发可自动读取已登记的用例。单独调用开发或测试用例技能时，缺少前置文档会先询问用户，得到同意后才补写。

## 目录

- [QuickStart：一次端到端交付](#quickstart)
- [一句 Prompt 使用任意 SKILL](#use-any-skill)
- [每个 SKILL 的详细介绍](#skill-details)
- [本地运行与验证](#local-checks)

<a id="quickstart"></a>
## QuickStart：一次端到端交付

### 先让 Agent 读到仓库

建议先把仓库下载到本地，再让 Agent 打开或访问这个目录。还没下载的话，可以运行：

```bash
git clone https://github.com/WayneYe912/OnePersonTeamSKILLs.git
cd OnePersonTeamSKILLs
```

无需先安装到 Agent 的全局技能目录。让 Agent 读取 `skills/<技能名>/SKILL.md`，再按说明读取同目录资源即可。支持原生技能发现的 Agent，可以按自身机制加载完整目录。请保留引用文件，别只复制 `SKILL.md`。

**“任意 Agent”指不绑定品牌，使用时仍需具备相应能力。** 要交付文件，Agent 需要能读取仓库、写文件，并渲染文档或用浏览器检查。运行内置脚本还需要执行命令和 Python 3.9+。没有 Python、但能写文件的 Agent，可以按规范直接生成 HTML。纯聊天 Agent 需要收到完整技能和资源，仅凭仓库名称无法读取内容，也不能声称已生成本地文件。

### 直接复制这份完整提示词

Agent **已经打开本仓库**后，就可以直接运行下面的提示词，无需补参数。提示词用一个明确标注为虚构的需求演示全部技能。处理真实需求时，把“演示输入”换成实际材料。

```text
请使用当前打开的 OnePersonTeamSKILLs 仓库，完成一次从一句话需求、PRD、技术方案到本地演示开发和验证的端到端交付。

【技能发现与串联】
读取当前仓库四个实际技能及必读资源，按 requirement-analysis →（technical-design ∥ test-case-design）→ 汇合核验 → product-development 编排。四项技能共用 outputs/reminder-demo/ 作为任务文档根：
1. 先用 requirement-analysis 生成并核验 prd.json、prd.html，登记权威 PRD 的实际摘要、来源与原文状态。
2. PRD 完成并登记后，同时启用 technical-design 和 test-case-design。两项读取同一版本的 PRD，分别生成 technical-design.json/HTML 和 test-cases.json/MD；测试用例不等待技术方案完成，技术方案仅作为后续可选补充依据。宿主支持并行任务时并行生成；不支持时明确说明执行限制，保留二者都只依赖 PRD 的关系，不新增“技术方案先完成”的前置条件。
3. 两项内容分别生成和校验，写入各自文件，不互相覆盖；共享 pipeline.json 必须由宿主协调串行登记，禁止无协调并发写入。每次登记前核对当前 PRD 摘要仍与生成时读取的版本一致；有变化则暂停并重新评估，不把旧产物绑定到新 PRD。
4. 两项产物都完成后，汇合核对 PRD、技术方案、测试用例的版本、REQ/AC/TC/DES 映射和规则一致性，阻断问题解决后再启动 product-development。开发阶段从本轮交接及 pipeline.json 自动读全 PRD、技术方案和已登记用例，不让我重复发送材料。
不把仓库 assets 示例当真实前置，不按其他任务的修改时间选文件。

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
用 test-case-design 在 PRD 完成后与 technical-design 同时启用，通过同任务 PRD 设计功能、边界、异常、权限、状态、回归和验收等适用用例，逐条关联 REQ 与测试条件 AC；不等待技术方案完成。性能、具体接口等缺标准时列待确认或说明不适用，不编 SLA、API 或错误码。每条 TC 包含前提、数据、操作、每步预期、断言、清理、优先级和自动化建议；生成阶段全部未执行。保存 test-cases.json 和 test-cases.md，校验后由宿主串行登记到 pipeline.json 并绑定实际读取的 PRD 摘要。汇合时如需参考技术方案补充实现相关用例，保留原 PRD 规则与确认状态，不把补充评审变成用例启动前置。若单独调用缺 PRD，先问是否帮我完善，等待回复；本次已明确授权前置生成，不重复问同一许可。

【开发前门禁与实施】
等待技术方案和测试用例两项完成并通过各自校验，由宿主串行完成前置权威 JSON 的登记，再完整读取并核验路径、摘要、两项 PRD 绑定版本及正文一致性；任一分支未完成或有阻断，不抢先进入开发。开发授权只覆盖上述明确的本地演示。新的关键建议、冲突或缺失规则先问，不能把“完善再开发”当成自动批准所有设计。若缺少 PRD/技术方案，先询问是否帮我完善；此提示已明确授权前置生成，无需重复询问已有流程许可。
通过门禁后，在 app/ 实现实际终端入口、领域逻辑与测试。包含设置冲突、无权限、旧版本、已完成、重复时间推进、历史通知权限撤销等异常，不只生成骨架、TODO 或 mock 成功截图。记录 REQ → DES → 文件/符号 → 测试。

【验证与交付】
按两文档技能的脚本检查和渲染；运行产品单元测试，并通过实际启动命令完成至少一条创建—设置—推进时间—查看通知路径。核验文档摘要未变、图文与代码规则一致；能渲染时检查桌面和窄屏，做不了的验证说明缺口。
最后交付 PRD/技术方案的 JSON/HTML、测试用例 JSON/MD、pipeline.json、app/ 完整代码和实际测试，以及 delivery.md（真实命令、结果、启动方式、REQ/AC/TC/DES 映射、演示限制与未覆盖）。生成用例与执行结果分开，未执行用例不能称为通过。未经另行要求不提交或推送 Git、不上传材料、不部署，不把本地模拟测试称为真实生产验证。
```

### 交付后应看到什么

- `outputs/reminder-demo/` 下有 PRD、技术方案的 JSON/HTML、测试用例 JSON/MD、`pipeline.json`、本地演示 `app/` 的代码和测试，以及 `delivery.md`。文件名以实际交付为准。
- 开发阶段自动读取同任务清单中的前置文档，无需用户重复发送。文件变化、存在多个候选或设计绑定旧 PRD 时会停止，不会悄悄选用旧文档。
- 两份文档说明需求规则和技术设计，代码有可运行入口和验证记录。演示限制、待确认事项和未覆盖检查都要写清，不能据此宣称获准生产上线。

想先看文档效果，可以下载仓库中的[团队待办需求分析示例](skills/requirement-analysis/assets/团队待办需求分析示例.html)，用浏览器打开。示例是虚构的，不能代替真实业务需求；GitHub 文件页面可能只显示源码。

<a id="use-any-skill"></a>
## 一句 Prompt 使用任意 SKILL

Agent 能访问本仓库后，就可以用**路径 + 任务 + 交付物**调用技能，无需专属斜杠命令、工具名或技能市场。

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

如果 Agent 无法读取本地文件，请提供**完整技能目录及必读资源**，或让能读取仓库的 Agent 获取内容。无法访问的 URL、技能名称或单独一个主文件，都不足以保证正确执行。

单独使用某个技能时，只读它和它要求的资源。机器上安装的其他技能，不属于本仓库维护范围。

<a id="skill-details"></a>
## 每个 SKILL 的详细介绍

这里介绍 `skills/` 下维护的四个技能：需求分析、技术方案、测试用例和产品开发。参考文件与脚本都属于技能目录，不能当作独立 SKILL 使用。

### requirement-analysis：一句话需求分析

**入口**：[skills/requirement-analysis/SKILL.md](skills/requirement-analysis/SKILL.md)

**目标**：把“想做什么”写成产品、设计、研发和测试能共同评审的需求分析文档。文档要把规则、边界、异常和验收写清，不靠增加字数充实内容。

#### 适合什么任务

- 从一句话需求、粗略想法或功能描述开始拆解。
- 起草 PRD、需求分析探索草稿或待评审文档。
- 补齐现有需求文档中的场景、范围、业务规则、异常和验收。
- 在不改变事实和规则的前提下，改善中文表达和阅读结构。

#### 需要什么输入

至少给出需求原话。目标用户、所在产品、现有流程、权限边界、核心规则、约束、成功条件和参考材料越清楚，分析越准确。

信息缺失会影响方案时，技能会先提问。用户明确要探索草稿时，可以提出**标注为建议的方案**，其余缺失信息保留为待确认，不把猜测写成事实。

#### 内置完整流程

1. **理解与澄清**：读完原话和材料，复述目标，分别记录事实、建议和待确认项。
2. **拆解与定范围**：梳理使用场景、触发条件、输入、操作和结果，明确本期要做、留待后续和不做的内容。
3. **定义需求契约**：保留稳定的需求编号，写清确认状态、优先级及理由、规则、异常，以及“给定／当／则”验收标准。
4. **绘制互补图**：用主流程图搭配界面、状态或角色示意，图文使用同一套已核对的规则。
5. **独立优化表达**：保护事实和专业术语，再处理空话、翻译腔、模糊指代和重复。分别回读，检查原意、表达和节奏。
6. **生成、验证与交付**：写入文件，检查结构和图文是否一致，实际查看渲染效果，说明哪些层面尚未验证。

#### 默认交付物

一份自包含 HTML 需求分析文档，内联样式和图形，浏览器离线可读。主要内容包括：

- 原始需求、需求复述、文档状态和来源。
- 用户与场景、本期范围、推荐方案和取舍。
- 功能需求、业务规则、异常恢复和验收标准。
- 数据与权限、质量要求、发布前提和衡量口径。
- 风险、依赖和阻断实施的待确认事项。
- 流程图和明确标注的低保真界面等互补示意。

使用内置渲染器时，Agent 先分析需求、写成 JSON，再生成 HTML。脚本只负责校验和渲染，不会理解一句话、补业务规则或代替产品判断。

用户指定 Word、PDF、在线文档或 Markdown 时，按指定格式交付，具体要靠 Agent 所在环境提供相应能力。**仓库没有内置这些格式的转换器或在线发布服务**，不能声称开箱即用。

#### 中文表达优化已经是技能的一部分

无需另装或调用文本优化技能。内置规范覆盖：

- 保护原话、数字单位、术语、编号、状态、条件、否定、因果和承诺。
- 先读懂整篇，再改句段；准确清楚的内容保留原样。
- 把名词化表达改成具体动作，统一称谓，去掉套话与同义反复。
- 不编造权威或效果，不自造词语，也不为凑数堆排比。
- 补自然停顿，让句子读起来顺，保留专业书面语和准确术语。
- 正则只提示疑点，不自动改稿，命中多少也不能说明业务是否真实。

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

**目标与输入**：读取需求分析、PRD、用户故事和现有代码/系统材料，写清实现契约、异常处理、验证方式和实施任务的依赖。可单独使用，无需安装需求分析技能；串联时保留上游编号、来源和确认状态。

**核心内容**：先明确目标、非目标和现状证据，再比较备选方案，说明决策理由。方案覆盖组件职责、接口与数据契约、事务与并发、幂等重试、部分成功和未知结果、安全权限、容量估算、测试、兼容迁移、发布停止与回退、实施拆解。不会默认引入队列或微服务，也不会编造真实接口、技术栈、工期和性能。

**图文与表达**：默认交付自包含离线 HTML，内置中文优化。先解释作用，再说明精确机制；保留术语原词，首次出现时准确解释。支持九类确定性图：架构、流程、时序、ER、状态、数据流、部署、研发依赖、泳道。根据需求选图，不为凑九张而增加无关图；图与 `REQ → DES → tests` 保持一致。

**辅助资源**：

- [references/design-contract.md](skills/technical-design/references/design-contract.md)：完整方案与 JSON 契约、来源状态、需求设计测试映射。
- [references/writing.md](skills/technical-design/references/writing.md)：通俗但保真的技术表达，不改变事务、去重、重试与承诺。
- [references/diagrams.md](skills/technical-design/references/diagrams.md)：九类图的细节、布局与核验要求。
- [scripts/contract.py](skills/technical-design/scripts/contract.py)：结构、来源、需求覆盖、图端点和依赖无环校验。
- [scripts/check.py](skills/technical-design/scripts/check.py)：只读结构与表达提醒，不自动改稿。
- [scripts/render.py](skills/technical-design/scripts/render.py)：标准库 HTML/SVG 渲染，默认拒绝覆盖已有文件。
- [assets/example.json](skills/technical-design/assets/example.json) 与 [图文技术方案示例](skills/technical-design/assets/团队待办技术方案示例.html)：虚构提醒设计，展示全部九类图，不代表现有系统。
- [tests/test_skill.py](skills/technical-design/tests/test_skill.py)：图形、映射、来源、异常数据、安全转义、迁移与命令验证。

**限制**：Python 3.9+ 只辅助校验和渲染，无 pip/npm/CDN 依赖；没有 Python 时，Agent 可按规范直接生成文件。复杂图需要拆分或另画准确的 SVG，内置渲染器无法承担无限复杂的 UML 布局。指定其他格式，要由宿主提供相应能力。缺少现状或关键约束时先澄清，只有用户允许探索稿，才保留候选方案。结构检查通过，仍不能证明业务、算法、性能或真实运行正确；技能不会自动实施、迁移、压测、部署或上线。

### product-development：基于 PRD 与技术方案开发

**入口**：[skills/product-development/SKILL.md](skills/product-development/SKILL.md)

**输入与联动**：提供 PRD、技术方案、目标代码项目和允许实施的范围。端到端流程从本轮已验证的交接或同任务 `pipeline.json` 中，自动读取前两项技能的结果，保留来源、状态、REQ/DES 和版本。不会按其他任务的修改时间挑文档，也不会把技能 assets 样例当作真实输入。

**缺文档行为**：单独使用时，缺 PRD 或技术方案会先问“是否要我先帮你完善缺少的 PRD 和技术方案，确认开发范围后再开始开发？”用户同意才补写；选择现有文档就请求可访问材料；拒绝则停止开发。只缺一份时，保留另一份，不重复索要。允许补写文档，并不代表批准所有新设计，关键缺口仍需确认。

**实施流程**：核对文档和现状 → 明确项目与基线 → 建立 REQ/DES 到代码和测试的映射 → 按设计实现最小完整路径 → 单测/构建/集成/实际入口验证 → 交付代码、测试和 delivery.md。保留用户已有改动，沿用项目技术栈；设计变更时同步文档。按范围验证失败、权限、并发和未知结果，mock 不能代替真实集成。

**辅助资源**：

- [references/handoff.md](skills/product-development/references/handoff.md)：同任务清单、选择顺序、版本绑定、缺失询问与结果分流。
- [references/development.md](skills/product-development/references/development.md)：实施边界、基线、真实入口验证和交付报告规范。
- [scripts/pipeline.py](skills/product-development/scripts/pipeline.py)：标准库登记/解析相对前置路径、摘要和 PRD—设计版本；只做文件门禁，不生成文档、代码或批准。
- [tests/test_handoff.py](skills/product-development/tests/test_handoff.py)：缺失、歧义、旧版本、路径越界、符号链接、状态保护、脚本迁移和上游联动测试。

**输出与限制**：交付授权项目的真实代码、相关测试和运行配置，以及验证结果与缺口报告。语言、框架、目标项目和关键验收未知时先澄清，不能替用户默认。Python 只辅助文档交接，实际开发还需要宿主能编辑代码、运行项目。默认不提交、推送、部署或执行生产迁移；任务报告和业务文档不得进入公开提交。

### test-case-design：基于 PRD 的多类型测试用例

**入口**：[skills/test-case-design/SKILL.md](skills/test-case-design/SKILL.md)

**输入与联动**：提供指定 PRD，或使用本次任务已生成的 PRD，技术方案可选。PRD 完成后，用例技能与 technical-design 同时启用，各自生成文件；用例不等待技术方案。两项产物汇合核验后，再进入开发。技能通过同任务 `pipeline.json` 或明确交接自动读取 PRD，支持 `resolve --only-prd`。不会跨任务猜最新版本，也不会用技能样例冒充用户文档。

**缺 PRD 行为**：单独调用时，没有可用 PRD 会先问“是否要我先帮你完善 PRD，再基于它生成测试用例？”得到同意后，才读取 requirement-analysis 补写。选择现有 PRD 就请求有效材料，拒绝则停止。新生成的规则未确认时，用例预期也保持待确认，不能写成确定的验收标准。

**设计内容**：支持功能、边界、异常、权限、安全防护、接口、状态、兼容、可访问性、性能、可靠性、回归和用户验收等类型，测试层级和设计方法另行说明。每条 TC 关联 REQ/AC，写清优先级理由、前提、具体数据、逐步操作与预期、断言、清理和自动化建议。缺少阈值、接口或设备范围时不编造，说明覆盖缺口或不适用的理由。

**输出与工具**：默认交付完整 test-cases.json 和 test-cases.md，所有生成用例均为未执行。用例定义、自动化实现和运行结果分开记录。用例绑定 PRD 摘要后，开发可读取已登记的 test_cases。

- [references/test-design.md](skills/test-case-design/references/test-design.md)：类型、方法、风险与评审。
- [references/case-contract.md](skills/test-case-design/references/case-contract.md)：用例字段、条件映射、覆盖和交接。
- [scripts/cases.py](skills/test-case-design/scripts/cases.py)：标准库只读校验及安全 Markdown 渲染，不执行产品测试。
- [assets/example-prd.json](skills/test-case-design/assets/example-prd.json)、[assets/example-cases.json](skills/test-case-design/assets/example-cases.json) 与 [完整用例示例](skills/test-case-design/assets/测试用例示例.md)：虚构 PRD 和多类型用例示范。
- [tests/test_cases.py](skills/test-case-design/tests/test_cases.py)：契约、未执行状态、覆盖、版本、PRD-only 和开发读取兼容测试。

**边界**：技能只设计用例，不连接真实产品，也不执行压力/破坏性测试或自动运行请求。安全用例只用于合法防护验证。结构检查和条件映射不能证明语义正确、覆盖充分或测试通过；缺少环境或实现依据时，单元测试层级和实际自动化仍需评估。

### 同任务文档交接

端到端流程把 PRD、技术方案和测试用例登记到同任务 `pipeline.json`。PRD 完成后，技术方案与测试用例读取同一 PRD 版本，并行生成各自文件。**内容可以并行，清单登记必须由宿主串行协调**；当前交接脚本不支持无协调并发写。技术方案与 test_cases 都绑定实际读取的 PRD 摘要，登记前先检查 PRD 是否变化。两项产物完成，且版本、规则和映射核验通过后，才开始开发。普通 resolve 供开发读取必需文档和已登记用例，`--only-prd` 供用例技能单独读取 PRD。PRD 更新后，保留旧设计与用例的绑定记录，作为版本失效的证据；重新评估并登记后才能继续。完整协议见[前置交接规范](skills/product-development/references/handoff.md)。文件登记成功、哈希匹配，都不代表业务已确认、开发获批准或测试通过。

<a id="local-checks"></a>
## 本地运行与验证

以下命令在**仓库根目录**运行，用于复现渲染结果或维护技能。日常使用只需上面的 Prompt，让 Agent 完成分析、运行工具并交付文件。

### 用仓库示例验证工具链

下面的命令不修改示例数据。渲染器会新建输出文件，目标已存在时拒绝覆盖。重跑可以换个文件名；确认要更新同一产物时，才使用 `--force`。

```bash
python3 -B skills/requirement-analysis/scripts/check.py skills/requirement-analysis/assets/example.json
python3 -B skills/requirement-analysis/scripts/render.py skills/requirement-analysis/assets/example.json --output requirement-analysis-demo.html
```

用浏览器打开 `requirement-analysis-demo.html` 即可查看。这个演示只验证工具链；处理真实需求时，Agent 必须按[数据契约](skills/requirement-analysis/references/document-contract.md)重新分析、编写 JSON，不能直接复制示例作为结果。

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

这是展示九种研发图的虚构示例。真实技术方案需要重新分析实际需求和系统材料，不能直接照搬样例规则。`technical-design` 的检查、渲染退出码与下方说明一致。

### 开发技能联动测试

```bash
python3 -B skills/product-development/scripts/pipeline.py --help
python3 -B -m unittest discover -s skills/product-development/tests -v
```

登记和解析示例见交接规范。`register` 只更新同任务清单，`resolve` 返回 `ready`/0、`needs_input`/1 或 `invalid`/2。缺文件或存在歧义时，Agent 先询问用户；输入非法或版本过旧时，先修复问题。`ready` 只表示通过文件门禁，开发前仍要读全 PRD/设计，确认目标项目和业务一致性。

### 测试用例示例与回归

```bash
python3 -B skills/test-case-design/scripts/cases.py check skills/test-case-design/assets/example-cases.json
python3 -B -m unittest discover -s skills/test-case-design/tests -v
```

用例技能的 `render` 子命令输出完整 Markdown，格式和字段见用例契约。`check` 的退出码 0/1/2，分别表示结构通过、不合格、读取/参数错误。检查不会执行产品测试，生成用例均为未执行；PRD-only 模式无需技术方案。

### 正确解读检查结果

- `check.py`：退出码 `0` 表示结构合格，`1` 表示结构不合格，`2` 表示读取或参数错误。`writing_advice` 提醒 Agent 检查表达，不自动阻断或修改文档。
- `render.py`：退出码 `0` 表示生成完成，`2` 表示参数、读取、结构或写入错误。生成成功后，还需要检查视觉效果和业务内容。
- 回归测试检查代码行为。处理具体需求时，仍需核对事实、规则、异常、图文一致性和实际阅读效果。

交付文件时，写清路径、打开方式、已完成的验证和剩余缺口。仅有文件，还不能算交付完成。
