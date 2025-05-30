# XpertEval - 开发记录文档 (DEV_RECORDS.md)

## 1. 概述
本开发记录文档用于追踪 XpertEval 项目的详细开发进展。所有任务均从 `DEV_PLAN.md` 分解而来，并关联到 `STRUCTURE.md` 中定义的具体模块和文件。

**状态标记**:
- `[待执行]`：任务尚未开始。
- `[执行中]`：任务正在开发中。
- `[已完成 - YYYY-MM-DD HH:MM]`：任务已完成，并标记完成时间。

## 2. 开发阶段与任务记录

### 阶段一：核心框架搭建

#### **任务1.1：项目初始化与环境配置** `[已完成 - 2025-05-18 00:18]`
- **涉及文件/目录**：
    - `/` (根目录): `.gitignore`, `VERSION`, `requirements.txt`, `LICENSE`
    - `STRUCTURE.md` 中定义的基础目录结构 (例如 `xperteval/`, `data/`, `docs/`, `tests/`, `scripts/` 等及其子目录)
- **具体功能点**：
    - `[已完成 - 2025-05-18 00:18]` 创建 `.gitignore` 文件：包含 Python 缓存 (`__pycache__/`, `*.pyc`), IDE 配置文件, 测试覆盖率报告, 本地数据 (`data/custom/local_data/`, `results/`, `*.log`) 等。
    - `[已完成 - 2025-05-18 00:18]` 创建 `VERSION` 文件：写入初始版本号，例如 `0.1.0-alpha`。
    - `[已完成 - 2025-05-18 00:18]` 创建 `requirements.txt` 文件：初步添加核心依赖 `PyYAML`, `requests`, `gradio`。
    - `[已完成 - 2025-05-18 00:18]` 创建 `LICENSE` 文件：内容为 Apache 2.0 许可证文本。
    - `[已完成 - 2025-05-18 00:18]` 根据 `STRUCTURE.md` 创建项目的基础目录结构，包括所有规划的空文件夹和 `__init__.py` 文件以构成 Python 包。

#### **任务1.2：模型配置模块 (`xperteval/config/`)** `[已完成 - 2025-05-18 00:22]`
- **涉及文件**： `xperteval/config/config_loader.py`, `xperteval/config/__init__.py`
- **`xperteval/config/config_loader.py` 功能点**：
    - `[已完成 - 2025-05-18 00:22]` 定义 `load_model_configs(config_path: str) -> dict` 函数 (或类)。
        - `[已完成 - 2025-05-18 00:22]` 支持从 YAML 文件 (`*.yaml` 或 `*.yml`) 加载配置。
        - `[已完成 - 2025-05-18 00:22]` 支持从 JSON 文件 (`*.json`) 加载配置。
        - `[已完成 - 2025-05-18 00:22]` 解析顶层的 `default_params` 全局默认参数字典。
        - `[已完成 - 2025-05-18 00:22]` 解析 `models` 列表，每个模型配置为一个字典。
        - `[已完成 - 2025-05-18 00:22]` 对每个模型配置，合并 `default_params` 和模型特定参数（模型特定参数优先）。
        - `[已完成 - 2025-05-18 00:22]` **配置项校验**：
            - `[已完成 - 2025-05-18 00:22]` 检查 `models` 列表是否存在且至少包含两个模型配置。
            - `[已完成 - 2025-05-18 00:22]` 处理 `MAIN_API` 字段：
                - 若多个模型设置 `MAIN_API: true`，则以第一个出现的为准，其余置为 `false`。
                - 若无模型设置 `MAIN_API: true`，则默认列表中的第一个模型为 `MAIN_API: true`。
            - `[已完成 - 2025-05-18 00:22]` 校验每个模型配置是否包含必需字段：`OPENAI_API_BASE`, `OPENAI_API_KEY`, `MODEL_NAME`, `MODEL_TYPE`。
            - `[已完成 - 2025-05-18 00:22]` 校验 `MODEL_TYPE` 是否为预定义枚举值之一 (`text`, `vision`, `audio`, `mllm`)。
            - `[已完成 - 2025-05-18 00:22]` 校验可选参数 (如 `MAX_TOKENS`, `TEMPERATURE`) 的数据类型和合理范围 (如适用)。
        - `[已完成 - 2025-05-18 00:22]` 当配置加载失败或校验不通过时，抛出带有清晰中文错误提示的自定义异常 (如 `ValueError` 或自定义的 `ConfigError`)。
    - `[已完成 - 2025-05-18 00:22]` 添加详细的中文注释，说明每个函数、参数和主要逻辑块的功能。
- **`xperteval/config/__init__.py` 功能点**：
    - `[已完成 - 2025-05-18 00:22]` 确保 `config_loader` 中的主要功能可以被外部调用，例如 `from xperteval.config import load_model_configs`。

#### **任务1.3：API 调用模块 (`xperteval/core/api_caller.py`)** `[已完成 - 2025-05-18 00:40]`
- **涉及文件**：`xperteval/core/api_caller.py`, `xperteval/core/__init__.py`
- **`xperteval/core/api_caller.py` 功能点**：
    - `[已完成 - 2025-05-18 00:40]` 定义 `invoke_model_api(model_config: dict, request_payload: dict) -> dict` 函数 (或类方法)。
        - `model_config`: 单个模型的完整配置（包含 `OPENAI_API_BASE`, `OPENAI_API_KEY`, `REQUEST_TIMEOUT` 等）。
        - `request_payload`: 构造好的符合 OpenAI API 规范的请求体（例如包含 `model`, `messages`, `max_tokens` 等）。
    - `[已完成 - 2025-05-18 00:40]` 使用 `requests`库实现 HTTP POST 请求发送。
        - `[已完成 - 2025-05-18 00:40]` 设置请求 URL (来自 `model_config['OPENAI_API_BASE']` 并拼接适当的端点，如 `/chat/completions`)。
        - `[已完成 - 2025-05-18 00:40]` 设置请求头部 (Headers)，包括 `Content-Type: application/json` 和 `Authorization: Bearer <API_KEY>`。
        - `[已完成 - 2025-05-18 00:40]` 发送 JSON 格式的 `request_payload`。
        - `[已完成 - 2025-05-18 00:40]` 使用 `model_config['REQUEST_TIMEOUT']` 或全局默认值设置请求超时。
    - `[已完成 - 2025-05-18 00:40]` 实现响应处理：
        - `[已完成 - 2025-05-18 00:40]` 检查 HTTP 响应状态码。
        - `[已完成 - 2025-05-18 00:40]` 成功时 (如 200 OK)，解析响应的 JSON 内容。
        - `[已完成 - 2025-05-18 00:40]` 失败时 (如 4xx, 5xx)，记录错误信息并可能抛出自定义异常 (如 `ApiError`)。
    - `[已完成 - 2025-05-18 00:40]` 实现基本的错误重试机制 (可选，初期可简化)。
    - `[已完成 - 2025-05-18 00:40]` 添加详细的中文注释。
- **`xperteval/core/__init__.py` 功能点**：
    - `[已完成 - 2025-05-18 00:40]` 使 `invoke_model_api` 可供其他模块调用。

#### **任务1.4：日志记录模块 (`xperteval/utils/log_utils.py`)** `[已完成 - 2025-05-18 01:12]`
- **涉及文件**：`xperteval/utils/log_utils.py`, `xperteval/utils/__init__.py`
- **`xperteval/utils/log_utils.py` 功能点**：
    - `[已完成 - 2025-05-18 01:12]` 开发完整的日志记录模块，包括：
        - `[已完成 - 2025-05-18 01:12]` 实现 `ColoredFormatter` 类，为不同日志级别提供不同颜色的控制台输出。
        - `[已完成 - 2025-05-18 01:12]` 实现 `setup_logger` 函数，配置日志器。
        - `[已完成 - 2025-05-18 01:12]` 实现 `get_logger` 函数，便于其他模块获取已配置的日志器。
        - `[已完成 - 2025-05-18 01:12]` 支持日志文件的每日自动轮转和备份功能。
        - `[已完成 - 2025-05-18 01:12]` 根据环境变量设置日志级别。
    - `[已完成 - 2025-05-18 01:12]` 为已有模块集成日志功能：
        - `[已完成 - 2025-05-18 01:12]` 更新配置加载模块，使用日志记录功能。
        - `[已完成 - 2025-05-18 01:12]` 更新API调用模块，使用日志记录功能。
        - `[已完成 - 2025-05-18 01:12]` 更新测试脚本，增加日志记录。
        - `[已完成 - 2025-05-18 01:12]` 开发日志功能测试脚本 (`scripts/test_logger.py`)。

### 阶段二：自动化评测流程

#### **任务2.1：数据集处理模块 (`xperteval/datasets/`)** `[已完成]`
- **涉及文件**：`xperteval/datasets/base_dataset.py`, `xperteval/datasets/xpert_format.py`, `xperteval/datasets/registered_datasets.py`, `xperteval/datasets/__init__.py`, `xperteval/datasets/README.md`
- **`xperteval/datasets/base_dataset.py` 功能点**：
    - `[已完成 - 2025-05-18 12:56]` 定义抽象基类 `BaseDataset` (可使用 `abc.ABC`)。
    - `[已完成 - 2025-05-18 12:56]` 定义抽象方法 `__init__(self, dataset_path: str, **kwargs)`。
    - `[已完成 - 2025-05-18 12:56]` 定义抽象方法 `__len__(self) -> int` 返回数据集样本数量。
    - `[已完成 - 2025-05-18 12:56]` 定义抽象方法 `__getitem__(self, idx: int) -> dict` 返回单个数据样本。
    - `[已完成 - 2025-05-18 12:56]` 定义 `load_data(self)` 抽象方法，用于加载和预处理数据。
- **`xperteval/datasets/xpert_format.py` 功能点**：
    - `[已完成 - 2025-05-19 10:49]` 定义 `XpertFormatDataset` 类，继承自 `BaseDataset`。
    - `[已完成 - 2025-05-19 10:49]` 实现 `__init__`，接收数据集文件路径 (通常是 JSONL 文件)。
    - `[已完成 - 2025-05-19 10:49]` 实现 `load_data` 方法：
        - `[已完成 - 2025-05-19 10:49]` 读取并解析 `XpertFormat` 格式的 JSONL 文件。
        - `[已完成 - 2025-05-19 10:49]` 处理单轮问答 (如包含 `query` 和 `response` 字段)。
        - `[已完成 - 2025-05-19 10:49]` 处理多轮问答 (如包含 `history` 列表, `query`, `response`)。
        - `[已完成 - 2025-05-19 10:49]` 处理数据中对多模态文件（图像、音频、视频）的引用 (如文件路径或URL)，将其作为样本信息的一部分。
        - `[已完成 - 2025-05-19 10:49]` 处理选择题格式 (如包含 `choices` 列表)。
        - `[已完成 - 2025-05-19 10:49]` 处理统一的答案格式 (如包含 `answer.type`, `answer.value`, `answer.explanation`)。
        - `[已完成 - 2025-05-19 10:49]` 处理元数据 (如包含 `meta.task_type`, `meta.category`, `meta.difficulty` 等)。
    - `[已完成 - 2025-05-19 10:49]` 实现 `__len__` 和 `__getitem__`。
    - `[已完成 - 2025-05-19 10:49]` 实现 `validate_format` 方法，用于验证数据是否符合XpertFormat规范。
- **`xperteval/datasets/registered_datasets.py` 功能点**:
    - `[已完成 - 2025-05-18 12:56]` 定义一个字典或注册表，映射数据集名称到其实例化逻辑或路径。
    - `[已完成 - 2025-05-18 12:56]` 提供函数 `get_dataset(name: str, **kwargs) -> BaseDataset`。
    - `[已完成 - 2025-05-19 10:49]` 更新 `DATASET_REGISTRY` 字典，将 `ms-swift` 替换为 `xpert-format`。
    - `[已完成 - 2025-05-19 10:49]` 更新数据集扫描和加载逻辑，支持 XpertFormat。
- **`xperteval/datasets/__init__.py` 功能点**：
    - `[已完成 - 2025-05-18 12:56]` 导出 `BaseDataset`。
    - `[已完成 - 2025-05-19 10:49]` 导出 `XpertFormatDataset` (替代 `MsSwiftDataset`)。
    - `[已完成 - 2025-05-18 12:56]` 导出 `get_dataset` 等函数。
- **`xperteval/datasets/README.md` 功能点**：
    - `[已完成 - 2025-05-19 10:30]` 详细分析各评测数据集的格式特点。
    - `[已完成 - 2025-05-19 10:30]` 提出 XpertFormat 统一格式方案。
    - `[已完成 - 2025-05-19 10:30]` 定义各类数据集到 XpertFormat 的转换策略。
    - `[已完成 - 2025-05-19 10:30]` 描述不同任务类型的评分策略。
- **示例数据集和测试**:
    - `[已完成 - 2025-05-19 10:49]` 创建选择题格式的示例数据集 (`data/examples/choice_example.jsonl`)。
    - `[已完成 - 2025-05-19 10:49]` 创建数学问题格式的示例数据集 (`data/examples/math_example.jsonl`)。
    - `[已完成 - 2025-05-19 10:49]` 创建代码生成任务格式的示例数据集 (`data/examples/code_example.jsonl`)。
    - `[已完成 - 2025-05-19 10:49]` 创建多模态任务格式的示例数据集 (`data/examples/multimodal_example.jsonl`)。
    - `[已完成 - 2025-05-19 10:49]` 实现测试脚本 (`scripts/test_xpert_format.py`) 并验证功能正常。
- **架构调整**:
    - `[已完成 - 2025-05-19 11:10]` 删除不再需要的 `ms_swift_parser.py` 文件，完全由 `xpert_format.py` 替代。
    - `[已完成 - 2025-05-19 11:10]` 创建 `datasets_config.json` 配置文件，用于管理开源评测数据集的下载和转换。
    - `[已完成 - 2025-05-19 11:10]` 实现 `dataset_manager.py`，提供数据集下载、转换和管理功能。
    - `[已完成 - 2025-05-19 11:10]` 更新项目架构文档 (`STRUCTURE.md`)，反映当前的项目架构变化。

#### **任务2.1.1：扩展数据集处理模块以支持更多开源评测数据集** `[已完成 - 2025-05-19 11:31]`
- **涉及文件**：`xperteval/datasets/common_benchmarks/`
- **功能点**：
    - `[已完成 - 2025-05-19 11:31]` 创建 `common_benchmarks` 子目录，用于存放各种通用评测数据集的解析器
    - `[已完成 - 2025-05-19 11:31]` 实现 `mmlu_dataset.py`: 
        - `[已完成 - 2025-05-19 11:31]` 定义 `MMLUDataset` 类，继承 `BaseDataset`
        - `[已完成 - 2025-05-19 11:31]` 实现从原始 MMLU 格式到 XpertFormat 的转换
        - `[已完成 - 2025-05-19 11:31]` 支持多选题特有的评分逻辑
    - `[已完成 - 2025-05-19 11:31]` 实现 `cmmlu_dataset.py`: 
        - `[已完成 - 2025-05-19 11:31]` 定义 `CMMLUDataset` 类，继承 `BaseDataset`
        - `[已完成 - 2025-05-19 11:31]` 实现从原始 CMMLU 格式到 XpertFormat 的转换
        - `[已完成 - 2025-05-19 11:31]` 处理中文特有的字符和编码问题
    - `[已完成 - 2025-05-19 11:31]` 实现 `gsm8k_dataset.py`: 
        - `[已完成 - 2025-05-19 11:31]` 定义 `GSM8KDataset` 类，继承 `BaseDataset`
        - `[已完成 - 2025-05-19 11:31]` 实现从原始 GSM8K 格式到 XpertFormat 的转换
        - `[已完成 - 2025-05-19 11:31]` 支持数学解题步骤和最终答案的提取
    - `[已完成 - 2025-05-19 11:31]` 实现 `math_dataset.py`: 
        - `[已完成 - 2025-05-19 11:31]` 定义 `MATHDataset` 类，继承 `BaseDataset`
        - `[已完成 - 2025-05-19 11:31]` 实现从原始 MATH 格式到 XpertFormat 的转换
        - `[已完成 - 2025-05-19 11:31]` 处理 LaTeX 公式的正确解析和呈现
    - `[已完成 - 2025-05-19 11:31]` 实现 `human_eval_dataset.py`: 
        - `[已完成 - 2025-05-19 11:31]` 定义 `HumanEvalDataset` 类，继承 `BaseDataset`
        - `[已完成 - 2025-05-19 11:31]` 实现从原始 HumanEval 格式到 XpertFormat 的转换
        - `[已完成 - 2025-05-19 11:31]` 支持代码生成任务的特殊处理
    - `[已完成 - 2025-05-19 11:31]` 实现 `ceval_dataset.py`: 
        - `[已完成 - 2025-05-19 11:31]` 定义 `CEvalDataset` 类，继承 `BaseDataset`
        - `[已完成 - 2025-05-19 11:31]` 实现从原始 C-Eval 格式到 XpertFormat 的转换
        - `[已完成 - 2025-05-19 11:31]` 处理中文特有的字符和编码问题
- **注意事项**：
    - `[已完成 - 2025-05-19 11:31]` 每个解析器都应继承 `BaseDataset` 并实现其抽象方法
    - `[已完成 - 2025-05-19 11:31]` 需处理各数据集特有的格式和结构，转换为统一的 XpertFormat 内部表示
    - `[已完成 - 2025-05-19 11:31]` 添加适当的中文注释和文档字符串

#### **任务2.1.2：扩展数据集处理模块以支持多模态评测数据集** `[已完成 - 2025-05-19 11:54]`
- **涉及文件**：`xperteval/datasets/multimodal_benchmarks/`
- **功能点**：
    - `[已完成 - 2025-05-19 11:54]` 创建 `multimodal_benchmarks` 子目录，用于存放多模态评测数据集的解析器
    - `[已完成 - 2025-05-19 11:54]` 实现 `mmbench_dataset.py`: 
        - `[已完成 - 2025-05-19 11:54]` 定义 `MMBenchDataset` 类，继承 `BaseDataset`
        - `[已完成 - 2025-05-19 11:54]` 实现从原始 MMBench 格式到 XpertFormat 的转换
        - `[已完成 - 2025-05-19 11:54]` 处理图像文件路径的解析和验证
    - `[已完成 - 2025-05-19 11:54]` 实现 `llava_bench_dataset.py`: 
        - `[已完成 - 2025-05-19 11:54]` 定义 `LLaVABenchDataset` 类，继承 `BaseDataset`
        - `[已完成 - 2025-05-19 11:54]` 实现从原始 LLaVA-Bench 格式到 XpertFormat 的转换
        - `[已完成 - 2025-05-19 11:54]` 处理对话式视觉问答的特殊结构
    - `[已完成 - 2025-05-19 11:54]` 实现 `seed_bench_dataset.py`: 
        - `[已完成 - 2025-05-19 11:54]` 定义 `SEEDBenchDataset` 类，继承 `BaseDataset`
        - `[已完成 - 2025-05-19 11:54]` 实现从原始 SEED-Bench 格式到 XpertFormat 的转换
        - `[已完成 - 2025-05-19 11:54]` 处理多图像和视频文件的引用
    - `[已完成 - 2025-05-19 11:54]` 实现 `mm_vet_dataset.py`: 
        - `[已完成 - 2025-05-19 11:54]` 定义 `MMVetDataset` 类，继承 `BaseDataset`
        - `[已完成 - 2025-05-19 11:54]` 实现从原始 MM-Vet 格式到 XpertFormat 的转换
        - `[已完成 - 2025-05-19 11:54]` 处理复杂视觉推理任务的特殊要求
- **注意事项**：
    - `[已完成 - 2025-05-19 11:54]` 特别关注多模态数据的处理，包括图像、视频、音频等资源的路径解析和加载
    - `[已完成 - 2025-05-19 11:54]` 确保资源文件的存在性检查和错误处理
    - `[已完成 - 2025-05-19 11:54]` 实现多模态数据的预处理功能（如需要）

#### **任务2.1.3：实现数据集格式转换工具** `[已完成 - 2025-05-19 12:01]`
- **涉及文件**：`xperteval/datasets/converters/`, `scripts/convert_dataset.py`
- **功能点**：
    - `[已完成 - 2025-05-19 12:01]` 创建 `converters` 子目录，用于存放各种数据集格式转换工具
    - `[已完成 - 2025-05-19 12:01]` 实现 `to_xpert_format.py`: 
        - `[已完成 - 2025-05-19 12:01]` 定义通用的转换接口 `convert_to_xpert_format(input_path, output_path, dataset_type)`
        - `[已完成 - 2025-05-19 12:01]` 实现各种格式到 XpertFormat 的转换函数
        - `[已完成 - 2025-05-19 12:01]` 支持批量转换功能
    - `[已完成 - 2025-05-19 12:01]` 实现 `convert_dataset.py` 脚本:
        - `[已完成 - 2025-05-19 12:01]` 提供命令行接口进行数据集转换
        - `[已完成 - 2025-05-19 12:01]` 支持各种转换选项和参数
        - `[已完成 - 2025-05-19 12:01]` 提供详细的转换日志和报告
    - `[已完成 - 2025-05-19 12:01]` 实现 `format_validator.py`:
        - `[已完成 - 2025-05-19 12:01]` 定义 `validate_xpert_format(data)` 函数，验证数据是否符合 XpertFormat 规范
        - `[已完成 - 2025-05-19 12:01]` 提供详细的错误信息和修复建议
- **注意事项**：
    - `[已完成 - 2025-05-19 12:01]` 转换工具应保留原始数据集的所有关键信息
    - `[已完成 - 2025-05-19 12:01]` 提供详细的使用说明和示例
    - `[已完成 - 2025-05-19 12:01]` 确保转换过程的可重现性和稳定性

#### **任务2.1.4：增强数据集注册和管理机制** `[已完成 - 2025-05-19 13:50]`
- **涉及文件**：`xperteval/datasets/registered_datasets.py`, `xperteval/datasets/dataset_manager.py`
- **功能点**：
    - `[已完成 - 2025-05-19 13:50]` 扩展 `DATASET_REGISTRY` 以包含所有新增的数据集类型
    - `[已完成 - 2025-05-19 13:50]` 增强 `scan_integrated_datasets` 函数:
        - `[已完成 - 2025-05-19 13:50]` 支持自动识别数据集类型和格式
        - `[已完成 - 2025-05-19 13:50]` 处理多文件数据集的特殊情况
        - `[已完成 - 2025-05-19 13:50]` 提供更详细的数据集元信息
    - `[已完成 - 2025-05-19 11:10]` 创建 `dataset_manager.py`:
        - `[已完成 - 2025-05-19 11:10]` 实现 `DatasetManager` 类，提供统一的数据集管理接口
        - `[已完成 - 2025-05-19 11:10]` 实现数据集版本管理和元数据存储
        - `[已完成 - 2025-05-19 11:10]` 添加数据集预览和统计信息功能
        - `[已完成 - 2025-05-19 13:50]` 支持数据集分割（训练/验证/测试）
        - `[已完成 - 2025-05-19 13:50]` 支持数据集采样和过滤
    - `[已完成 - 2025-05-19 11:10]` 实现数据集缓存机制:
        - `[已完成 - 2025-05-19 11:10]` 优化频繁访问的数据集加载性能
        - `[已完成 - 2025-05-19 11:10]` 管理缓存大小和生命周期
- **注意事项**：
    - `[已完成 - 2025-05-19 13:50]` 确保向后兼容性，不破坏现有功能
    - `[已完成 - 2025-05-19 13:50]` 提供清晰的错误信息和日志记录
    - `[已完成 - 2025-05-19 13:50]` 设计灵活的接口，便于未来扩展

#### **任务2.1.5：开发数据集文档和示例** `[已完成 - 2025-05-19 14:02]`
- **涉及文件**：`docs/datasets/`, `data/examples/`
- **功能点**：
    - `[已完成 - 2025-05-19 14:02]` 创建详细的数据集文档:
        - `[已完成 - 2025-05-19 14:02]` 编写 `docs/datasets/xpert_format_spec.md`，详细说明 XpertFormat 规范
        - `[已完成 - 2025-05-19 14:02]` 编写 `docs/datasets/dataset_conversion.md`，说明数据集转换工具
        - `[已完成 - 2025-05-19 14:02]` 编写 `docs/datasets/dataset_usage.md`，说明数据集使用方法
        - `[已完成 - 2025-05-19 14:02]` 编写 `docs/datasets/index.md`，提供数据集文档索引
    - `[已完成 - 2025-05-19 10:49]` 提供示例数据集:
        - `[已完成 - 2025-05-19 10:49]` 创建 `data/examples/choice_example.jsonl`，展示选择题格式
        - `[已完成 - 2025-05-19 10:49]` 创建 `data/examples/math_example.jsonl`，展示数学问题格式
        - `[已完成 - 2025-05-19 10:49]` 创建 `data/examples/code_example.jsonl`，展示代码生成任务格式
        - `[已完成 - 2025-05-19 10:49]` 创建 `data/examples/multimodal_example.jsonl`，展示多模态任务格式
    - `[已完成 - 2025-05-19 14:02]` 开发数据集可视化工具:
        - `[已完成 - 2025-05-19 14:02]` 实现 `scripts/preview_dataset.py`，用于预览和检查数据集内容
        - `[已完成 - 2025-05-19 14:02]` 支持不同类型数据的适当展示（文本、代码、图像等）
    - `[已完成 - 2025-05-19 14:02]` 配置 GitHub Pages 文档部署:
        - `[已完成 - 2025-05-19 14:02]` 创建 `docs/_config.yml`，使用 Ant Design 风格
        - `[已完成 - 2025-05-19 14:02]` 创建 `docs/index.md`，作为文档首页
        - `[已完成 - 2025-05-19 14:02]` 创建 `.github/workflows/docs_deploy.yml`，配置自动部署

#### **任务2.2：评测器基类与初步实现 (`xperteval/core/base_evaluator.py`, `xperteval/evaluators/`)** `[已完成 - 2025-05-27 14:35]`
- **涉及文件**：`xperteval/core/base_evaluator.py`, `xperteval/evaluators/__init__.py`, `xperteval/evaluators/common/__init__.py`, `xperteval/evaluators/common/accuracy.py` (示例)
- **`xperteval/core/base_evaluator.py` 功能点**：
    - `[已完成 - 2025-05-27 14:35]` 定义抽象基类 `BaseEvaluator` (可使用 `abc.ABC`)。
    - `[已完成 - 2025-05-27 14:35]` 定义抽象方法 `evaluate(self, predictions: list, references: list) -> dict`。
        - `predictions`: 模型生成的结果列表。
        - `references`: 数据集中的标准答案/参考列表。
        - 返回一个包含评测指标名称和分数的字典，例如 `{"accuracy": 0.85}`。
- **`xperteval/evaluators/common/accuracy.py` 功能点** (示例):
    - `[已完成 - 2025-05-27 14:35]` 定义 `AccuracyEvaluator` 类，继承自 `BaseEvaluator`。
    - `[已完成 - 2025-05-27 14:35]` 实现 `evaluate` 方法，计算简单分类任务的准确率 (精确匹配)。
- **`xperteval/evaluators/__init__.py` 和 `xperteval/evaluators/common/__init__.py` 功能点**：
    - `[已完成 - 2025-05-27 14:35]` 确保评测器类可被导入。
- **其他实现的评测器**：
    - `[已完成 - 2025-05-27 14:35]` 实现 `BLEUEvaluator` 用于文本生成任务评估。
    - `[已完成 - 2025-05-27 14:35]` 实现 `MathEvaluator` 用于数学问题评估。
    - `[已完成 - 2025-05-27 14:35]` 实现 `TcmDiagnosisEvaluator` 用于中医诊断评估。
- **评测器注册机制**：
    - `[已完成 - 2025-05-27 14:35]` 实现评测器注册表 `EVALUATOR_REGISTRY`。
    - `[已完成 - 2025-05-27 14:35]` 实现 `get_evaluator` 和 `get_evaluators` 函数。
    - `[已完成 - 2025-05-27 14:35]` 实现 `list_evaluators` 和 `register_evaluator` 函数。

#### **任务2.3：自动化评测引擎 (`xperteval/core/auto_eval_engine.py`)** `[已完成 - 2025-05-29 18:40]`
- **涉及文件**：`xperteval/core/auto_eval_engine.py`
- **`xperteval/core/auto_eval_engine.py` 功能点**：
    - `[已完成 - 2025-05-29 18:40]` 定义 `AutoEvalEngine` 类或相关函数。
    - `[已完成 - 2025-05-29 18:40]` `__init__` 或主函数接收：模型配置列表 (`list[dict]`)，数据集实例 (`BaseDataset`)，评测器实例列表 (`list[BaseEvaluator]`)。
    - `[已完成 - 2025-05-29 18:40]` 实现 `run_evaluation()` 方法：
        - `[已完成 - 2025-05-29 18:40]` 遍历数据集中的每一个样本 (`sample = dataset[i]`)。
        - `[已完成 - 2025-05-29 18:40]` 对每个样本，为每个配置的模型调用 `xperteval.core.api_caller.invoke_model_api` 获取预测结果。
            - `[已完成 - 2025-05-29 18:40]` 根据样本内容和模型类型构造 `request_payload`。
            - `[已完成 - 2025-05-29 18:40]` 处理 API 调用可能发生的错误，记录失败信息，允许部分失败不中断全局评测（标记该样本该模型评测失败）。
        - `[已完成 - 2025-05-29 18:40]` 收集所有模型的预测结果和样本的参考答案。
        - `[已完成 - 2025-05-29 18:40]` 对每个注册的评测器，调用其 `evaluate` 方法计算分数。
        - `[已完成 - 2025-05-29 18:40]` 汇总结果：按模型、按评测指标组织所有样本的平均分数和详细结果。
    - `[已完成 - 2025-05-29 18:40]` 结果结构应清晰，便于后续报告生成。
    - `[已完成 - 2025-05-29 18:40]` 实现评测过程中的日志记录 (当前样本、进度等)。

### 阶段三：报告生成与命令行工具

#### **任务3.1：报告生成模块 (`xperteval/reporters/report_generator.py`)** `[待执行]`
- **涉及文件**：`xperteval/reporters/report_generator.py`, `xperteval/reporters/__init__.py`, (可选) `templates/report_template.html`
- **`xperteval/reporters/report_generator.py` 功能点**：
    - `[待执行]` 定义 `ReportGenerator` 类或相关函数。
    - `[待执行]` 接收 `AutoEvalEngine` 输出的汇总评测结果作为输入。
    - `[待执行]` 实现 `generate_report(output_formats: list[str], output_dir: str, main_api_name: str)` 方法。
        - `output_formats`: 希望生成的报告格式列表 (如 `['markdown', 'json', 'html']`)。
        - `output_dir`: 报告输出目录。
        - `main_api_name`: 主评测 API 的模型名称，用于报告中突出对比。
    - `[待执行]` 实现 Markdown 格式报告生成：
        - `[待执行]` 包含评测概述 (参与模型、数据集、时间)。
        - `[待执行]` 表格形式展示各模型在各评测指标上的得分，突出主API模型。
    - `[待执行]` 实现 JSON 格式报告生成：原始结果的结构化输出。
    - `[待执行]` (可选) 实现 HTML 格式报告生成，可使用模板引擎 (如 Jinja2) 和 `templates/report_template.html`，包含图表 (如柱状图对比)。
- **`xperteval/reporters/__init__.py` 功能点**：
    - `[待执行]` 导出 `ReportGenerator`。

#### **任务3.2：命令行入口 (`main.py`)** `[待执行]`
- **涉及文件**：`main.py` (在项目根目录)
- **`main.py` 功能点**：
    - `[待执行]` 使用 `argparse` 模块处理命令行参数。
        - `[待执行]` `--config` (必需): 模型配置文件路径 (`models.yaml` 或 `models.json`)。
        - `[待执行]` `--dataset_path` (必需): 评测数据集文件路径。
        - `[待执行]` `--dataset_type` (可选, 默认 `ms_swift`): 数据集类型，用于选择解析器。
        - `[待执行]` `--evaluators` (可选): 指定使用的评测器名称列表 (如 `accuracy`, `bleu`)，默认为全部可用或一组核心指标。
        - `[待执行]` `--output_dir` (可选, 默认 `results/<timestamp>/`): 评测结果和报告的输出目录。
        - `[待执行]` `--report_formats` (可选, 默认 `markdown,json`): 报告输出格式。
    - `[待执行]` 主逻辑：
        - `[待执行]` 加载模型配置 (`xperteval.config.load_model_configs`)。
        - `[待执行]` 加载数据集 (根据 `dataset_type` 和 `dataset_path` 实例化 `MsSwiftDataset` 等)。
        - `[待执行]` 实例化所选的评测器。
        - `[待执行]` 创建并运行 `AutoEvalEngine`。
        - `[待执行]` 创建 `ReportGenerator` 并生成报告。
    - `[待执行]` 提供清晰的帮助信息 (`python main.py --help`)。
    - `[待执行]` 实现优雅的错误处理和用户反馈。

### 阶段四：人工评测功能

#### **任务4.1：人工评测引擎 (`xperteval/core/manual_eval_engine.py`)** `[待执行]`
- **涉及文件**：`xperteval/core/manual_eval_engine.py`
- **`xperteval/core/manual_eval_engine.py` 功能点**：
    - `[待执行]` 定义 `ManualEvalEngine` 类。
    - `[待执行]` `__init__` 接收模型配置列表和数据集实例。
    - `[待执行]` `get_sample_for_evaluation(sample_idx: int) -> dict`:
        - `[待执行]` 获取数据集中的指定样本。
        - `[待执行]` 为该样本调用所有已配置模型的 API 获取答案。
        - `[待执行]` **关键：确保返回给评分前端的答案是匿名的** (例如，用 Model A, Model B 标识，并打乱顺序)。
        - `[待执行]` 返回包含问题和各模型匿名答案的字典。
    - `[待执行]` `submit_ratings(sample_idx: int, ratings: dict)`:
        - `ratings`: 包含对每个匿名模型在不同维度上的评分，例如 `{'Model A': {'fluency': 8, 'relevance': 7}, 'Model B': ...}`。
        - `[待执行]` 存储这些评分（初期可存于内存，后续考虑持久化）。
    - `[待执行]` `finalize_manual_evaluation() -> dict`:
        - `[待执行]` 检查是否满足人工评测有效性要求（如已评测样本数 >= 20）。
        - `[待执行]` 汇总所有已提交的评分，计算平均分等统计数据。
        - `[待执行]` 返回汇总后的人工评测结果。

#### **任务4.2：人工评测结果整合** `[待执行]`
- **涉及模块**：`xperteval/reporters/report_generator.py`
- **功能点**：
    - `[待执行]` 修改 `ReportGenerator` 以接收和处理来自 `ManualEvalEngine` 的人工评测结果。
    - `[待执行]` 在生成的报告中（Markdown, HTML等）增加人工评测结果部分，清晰展示各模型的人工评分对比。

### 阶段五：WebUI 开发 (`gradio`)

#### **任务5.1：Gradio 基础界面 (`xperteval/webui/app_gradio.py`, `app.py`)** `[待执行]`
- **涉及文件**：`xperteval/webui/app_gradio.py`, `xperteval/webui/__init__.py`, `app.py` (根目录)
- **`xperteval/webui/app_gradio.py` 功能点**：
    - `[待执行]` 定义 `create_gradio_app()` 函数，返回 `gr.Blocks` 实例。
    - `[待执行]` **模型配置界面 (Tab 1)**:
        - `[待执行]` 使用 `gr.Textbox` 等组件让用户输入或加载模型 API 配置 (OPENAI_API_BASE, KEY, MODEL_NAME, MODEL_TYPE, MAIN_API, etc.)。
        - `[待执行]` 支持动态添加/删除多个模型配置条目。
        - `[待执行]` (可选) 支持从 YAML/JSON 文件导入/导出模型配置。
        - `[待执行]` "保存配置"按钮，将界面上的配置传递给后端逻辑。
    - `[待执行]` **数据集选择与上传界面 (Tab 2 - 自动化评测)**:
        - `[待执行]` `gr.Dropdown` 选择已集成的评测集 (需与 `registered_datasets.py` 联动或从 `data/integrated` 扫描)。
        - `[待执行]` `gr.File` 组件允许用户上传自定义评测集 (JSONL 格式)。
- **`app.py` (根目录) 功能点**：
    - `[待执行]` 导入 `create_gradio_app`。
    - `[待执行]` 调用 `app.launch()` 启动 Gradio 服务。

#### **任务5.2：集成自动化评测到 WebUI** `[待执行]`
- **涉及文件**：`xperteval/webui/app_gradio.py`
- **功能点 (在自动化评测Tab内)**：
    - `[待执行]` "开始自动化评测"按钮。
    - `[待执行]` 按钮回调函数：
        - `[待执行]` 获取界面上的模型配置和选定/上传的数据集。
        - `[待执行]` 调用后端 `AutoEvalEngine` 执行评测 (可能需要异步处理以防界面阻塞)。
        - `[待执行]` `gr.Textbox`或 `gr.Markdown` 显示实时评测进度/日志。
        - `[待执行]` 评测完成后，在界面上使用 `gr.Markdown`, `gr.DataFrame`, `gr.Plot` 等展示评测报告的关键内容。
        - `[待执行]` 提供下载完整报告的链接/按钮。

#### **任务5.3：集成人工评测到 WebUI** `[待执行]`
- **涉及文件**：`xperteval/webui/app_gradio.py`
- **功能点 (Tab 3 - 人工评测)**：
    - `[待执行]` 选择数据集 (与自动化评测类似)。
    - `[待执行]` "开始/下一题"按钮，调用 `ManualEvalEngine.get_sample_for_evaluation()`。
    - `[待执行]` 界面显示当前问题。
    - `[待执行]` 并排或分页显示各模型的匿名答案 (如 `gr.Textbox(label="模型A答案", interactive=False)`)。
    - `[待执行]` 为每个匿名答案提供评分控件 (如 `gr.Slider(label="流畅性", minimum=1, maximum=10, step=1)`)，支持多维度评分。
    - `[待执行]` "提交本题评分"按钮，调用 `ManualEvalEngine.submit_ratings()`。
    - `[待执行]` 显示已评测题目数量，提示是否达到20题要求。
    - `[待执行]` "完成并查看报告"按钮，调用 `ManualEvalEngine.finalize_manual_evaluation()` 并展示结果。

### 阶段六：中医药领域特定功能

#### **任务6.1：集成中医药评测数据集 (`data/integrated/tcm_*`)** `[待执行]`
- **涉及目录**：`data/integrated/`
- **功能点**：
    - `[待执行]` 整理/创建至少一个中医药相关评测数据集 (例如，舌诊图片分类、简单医案问答)。
    - `[待执行]` 将数据集转换为 `ms-swift` 兼容的 JSONL 格式。
    - `[待执行]` 将数据集文件放入 `data/integrated/tcm_some_task/` 目录。
    - `[待执行]` (可选) 在 `registered_datasets.py` 中注册此数据集。
    - `[待执行]` 编写简短的 `README.md` 在该数据集目录下说明数据格式和内容。

#### **任务6.2：开发中医药特定评测指标 (`xperteval/evaluators/tcm/`)** `[待执行]`
- **涉及文件**：`xperteval/evaluators/tcm/__init__.py`, `xperteval/evaluators/tcm/diagnosis_eval.py` (示例)
- **`xperteval/evaluators/tcm/diagnosis_eval.py` 功能点** (示例 - 中医辨证准确率):
    - `[待执行]` 定义 `TcmDiagnosisAccuracyEvaluator` 类，继承 `BaseEvaluator`。
    - `[待执行]` 实现 `evaluate` 方法，比较模型输出的证候诊断与参考答案的匹配度 (可能需要定义证候的标准化表示和相似度计算方法)。
- **功能点** (其他可能的TCM评测指标，按需实现)：
    - `[待执行]` 方剂推荐相关性/准确性评测器。
    - `[待执行]` 舌象/面象识别准确率评测器 (若模型输出结构化结果)。

### 阶段七：文档、测试、部署与完善

#### **任务7.1：完善项目文档 (`docs/`)** `[待执行]`
- **涉及目录**：`docs/` 和 `.github/workflows/docs_deploy.yml`
- **功能点**：
    - `[待执行]` 撰写 `docs/index.md` (文档首页)。
    - `[待执行]` 撰写 `docs/quick_start.md` (快速开始指南)。
    - `[待执行]` 撰写用户手册 (`docs/user_manual/`)：`configuration.md` (API和数据集配置), `web_ui.md` (WebUI使用)。
    - `[待执行]` 撰写开发者指南 (`docs/developer_guide/`)：`architecture.md` (引用 `STRUCTURE.md`), `extending.md` (如何添加评测集、评测指标)。
    - `[待执行]` (可选) 配置 Jekyll 和 Ant Design 风格的主题，或寻找合适的 GitHub Pages 主题/工具。
    - `[待执行]` 创建 `.github/workflows/docs_deploy.yml` 用于将 `docs/` 目录内容自动部署到 GitHub Pages。

#### **任务7.2：强化测试 (`tests/`)** `[待执行]`
- **涉及目录**：`tests/unit/`, `tests/integration/`
- **功能点**：
    - `[待执行]` 为 `xperteval/config/config_loader.py` 编写单元测试 (`tests/unit/test_config_loader.py`)。
    - `[待执行]` 为 `xperteval/core/api_caller.py` 编写单元测试 (mock HTTP请求)。
    - `[待执行]` 为 `xperteval/datasets/xpert_format.py` 编写单元测试。
    - `[待执行]` 为已实现的评测器 (`AccuracyEvaluator`等) 编写单元测试。
    - `[待执行]` 编写集成测试 (`tests/integration/test_full_eval_flow.py`)：覆盖从配置加载到报告生成的完整自动化评测流程 (可使用 mock API 或少量真实调用)。
    - `[待执行]` 编写 `scripts/run_tests.sh` 脚本，用于方便地执行所有测试。

#### **任务7.3：Docker 化部署 (`Dockerfile`, `scripts/build_docker.sh`)** `[待执行]`
- **涉及文件**：`Dockerfile`, `scripts/build_docker.sh`
- **`Dockerfile` 功能点**：
    - `[待执行]`选择合适的基础 Python 镜像。
    - `[待执行]`复制 `requirements.txt` 并安装依赖。
    - `[待执行]`复制项目源代码到镜像中。
    - `[待执行]`设置工作目录。
    - `[待执行]`暴露 Gradio WebUI 端口 (如 7860)。
    - `[待执行]`设置默认启动命令 (如 `CMD ["python", "app.py"]` 或 `CMD ["python", "main.py", "--help"]`)。
- **`scripts/build_docker.sh` 功能点**：
    - `[待执行]`包含 `docker build` 命令，使用项目根目录的 `Dockerfile` 构建镜像，并打上合适的标签 (如 `xperteval:latest` 和 `xperteval:<VERSION>`)。

#### **任务7.4：性能评测指标的实现** `[待执行]`
- **涉及模块**：`xperteval/core/api_caller.py`, `xperteval/core/auto_eval_engine.py`, `xperteval/reporters/report_generator.py`
- **功能点**：
    - `[待执行]` 在 `api_caller.py` 中记录每次 API 调用的耗时。
    - `[待执行]` `AutoEvalEngine` 在汇总结果时包含平均响应时间、Token使用信息 (如果API返回)。
    - `[待执行]` `ReportGenerator` 在报告中展示这些性能指标。

#### **任务7.5：代码审查与重构** `[待执行]`
- **涉及范围**：整个代码库
- **功能点**：
    - `[待执行]` 回顾所有模块，检查代码风格一致性、可读性、模块间的耦合度。
    - `[待执行]` 确保所有函数、类、重要逻辑块都有清晰的中文注释。
    - `[待执行]` 移除冗余代码，优化性能瓶颈 (如有发现)。

## 3. 开发过程要求

- **持续维护本文档**：在开发过程中，根据实际进展，及时更新各任务的状态（待执行 -> 执行中 -> 已完成 - YYYY-MM-DD HH:MM）。
- **严格遵循计划**：在完成每个主要开发步骤或模块后，务必重新审阅以下文档，以确保开发方向与总体目标保持一致：
    1.  项目需求文档 (`REQUIREMENTS.md`)
    2.  项目架构设计文档 (`STRUCTURE.md`)
    3.  项目开发计划文档 (`DEV_PLAN.md`)
    4.  本开发记录文档 (`DEV_RECORDS.md`)

---
*本文档将随着项目进展持续更新。* 