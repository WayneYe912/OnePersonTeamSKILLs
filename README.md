# OnePersonTeamSKILLs

让一个人借助 Agent，把想法推进到可交付的成品。本仓库维护可移植的标准 `SKILL.md` 技能：流程、参考规范、脚本和示例放在同一目录，不绑定特定 Agent 或企业服务。

当前维护 **2 个 SKILL**：[`requirement-analysis`](skills/requirement-analysis/SKILL.md) 把一句话需求转成可评审的图文需求分析；[`technical-design`](skills/technical-design/SKILL.md) 基于需求及系统材料编写可落地的图文技术方案。完整技能链为 **需求分析 → 技术方案 → 核验与文档交付**，不包含实际产品开发、部署或上线。

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
请使用当前打开的 OnePersonTeamSKILLs 仓库，完成一次从一句话需求到图文需求分析、图文技术方案的端到端文档交付。

【技能发现与串联】
先枚举当前仓库 skills/ 下实际存在的所有 SKILL.md，逐个读取入口，按各自要求读取 references、脚本说明和相关素材。按输入输出关系串联所有实际存在且适用于本任务的技能：先 requirement-analysis 生成需求分析，再 technical-design 以该需求的正文或 JSON 为输入生成技术方案，最后统一核验和交付。保留原始需求编号、规则、验收、来源及确认状态。中文表达优化、配图、渲染和检查都是各技能内置环节，不是另几个技能。不要臆造产品开发或部署技能；以后若新增技能与任务无关，说明原因，不为“全部调用”执行越权操作。

【演示输入】
一句话需求：给团队待办加一个到期提醒。
这是一项虚构演示，不是线上业务材料。请先做“探索草稿”。
演示约束：产品是团队待办网页；待办已有负责人、截止时间、完成状态和成员访问权限；本期只考虑现有站内通知渠道，不做短信、电话或管理者升级提醒；通知不能绕过待办当前权限。
提醒时间、时区、重复与重试规则、容许延迟、数据保存期限、指标基线和目标值尚未确定。

【分析与表达】
保留需求原话，区分“已确认”“建议”“待确认”；演示中已给的约束可作为演示来源，不可冒充真实调研结论。缺失规则可以给建议，但必须保持建议状态。若关键缺口妨碍探索草稿成立，一次提出最多三个必要问题；不要为写得具体而编造数据、访谈、负责人、接口、工期或效果。
写清目标用户、使用场景、本期与非本期范围、推荐方案、业务规则、异常恢复、数据权限、质量要求、衡量口径、风险与待确认事项。每个需求使用稳定编号，给出可观察的“给定／当／则”验收标准。
完成分析初稿后，单独执行技能内置的中文表达优化：保留事实、术语、编号、状态、条件、否定和承诺；去掉空话、翻译腔和同义反复，检查句间节奏，不把严谨规则改成含糊口语。

【技术方案】
用 technical-design 完整读取上一步需求结果，建立 REQ → DES → 验证映射，写清候选架构、模块职责、接口与字段契约、事务与并发、失败和未知结果恢复、权限、安全、容量估算方法、测试、实施依赖、迁移、发布停止与回退条件。此演示不提供真实代码、技术栈和规模，保持“探索草稿”；提出设计建议但不冒充已安装依赖、现有接口或实测结果。阻断实施的缺口明确记录，不自行编造工期、QPS 或生产拓扑。
技术方案同样单独优化表达，术语保留并用准确中文解释，不把渠道受理写成用户收到、不把去重写成恰好一次送达。

【图文与文件】
需求分析绘制含取消或失败分支的主流程图与低保真界面示意。技术方案按适用性绘制架构、关键时序、ER 或状态图，并补充数据流、部署、研发依赖、泳道与处理流程；不适用的图种给理由，不为了凑图而编内容。图中状态、接口、字段及需求/设计编号与正文一致，不交未渲染的代码充数。
在仓库 outputs/reminder-demo/ 下分别交付需求分析 JSON、HTML 和技术方案 JSON、HTML；创建目录前检查已有内容，若同名文件不是本次生成的，另选文件名，不覆盖。
有 Python 3.9+ 时，分别按两技能契约组织 JSON，运行各自 scripts/check.py，再运行各自 scripts/render.py。脚本路径相对对应 SKILL.md 所在目录定位。无 Python 时按同一规范直接生成，不安装全局依赖。不要复制仓库示例冒充本次分析。

【验证与交付】
核对正文、规则、来源、需求编号、验收和图形的一致性。实际渲染检查桌面和窄屏；有打印能力时检查打印分页。结构错误修复后再交付，表达提醒结合上下文判断，不为清零而改坏事实。做不到的验证明确说明，不以文件存在代替验证通过。
最后给出产物路径或附件、打开方式、关键待确认项、已完成检查和未验证范围。只交付可用的完整文档，不只给提纲或教程。未经我另行要求，不发布、不上传业务材料、不修改产品代码、不提交或推送 Git。
```

### 交付后应看到什么

- `outputs/reminder-demo/` 下有本次生成的需求分析 JSON、HTML 与技术方案 JSON、HTML，文件名以 Agent 实际交付为准。
- 两份 HTML 用浏览器直接打开即可阅读：需求文档明确规则、异常与验收，技术方案明确实现契约、研发图表、测试和回退，并可追溯到同一需求编号。
- 交付说明区分已经做过的检查和能力受限而未做的检查。探索草稿不等于实施或上线批准。

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

### 仓库不在当前目录时

把技能路径换成实际的绝对路径，例如“读取我已授权的 `/path/to/OnePersonTeamSKILLs/skills/requirement-analysis/SKILL.md`”。`/path/to/` 是示意位置，不能照抄成真实路径。

如果 Agent 没有本地文件访问能力，提供**完整技能目录及必读资源**，或让有仓库读取能力的 Agent 获取对应内容。只贴一个无法访问的 URL、只说技能名，或只上传主文件，都不能保证技能被正确执行。

单技能调用只读取该技能及其要求的资源；不要把机器上安装的其他技能误认成本仓库维护的技能。

<a id="skill-details"></a>
## 每个 SKILL 的详细介绍

本节介绍 `skills/` 下实际维护的两个技能：需求分析与技术方案。参考文件、渲染脚本和检查脚本都是各技能的组成部分，不是独立 SKILL。

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

### 正确解读检查结果

- `check.py`：退出码 `0` 表示结构合格，`1` 表示结构不合格，`2` 表示读取或参数错误。`writing_advice` 是待判断的表达提醒，不自动阻断或改稿。
- `render.py`：退出码 `0` 表示完成生成，`2` 表示参数、读取、结构或写入错误；成功生成不等于视觉与业务验证通过。
- 回归测试验证代码行为；具体需求仍需核对事实、规则、异常、图文一致性及真实阅读效果。

所有最终产物应明确文件路径、打开方式、完成的验证与剩余缺口。文件存在不是交付完成的唯一标准。
