---
layout: default
title: 用户手册
nav_order: 4
has_children: true
permalink: /user_manual
toc: true
---

# XpertEval 用户手册
{: .no_toc }

欢迎使用 XpertEval 用户手册！本手册提供了 XpertEval 框架的详细使用说明，帮助您快速上手并充分利用框架的各项功能。

## 手册内容

本用户手册包含以下内容：

- [配置指南](./configuration.html)：详细说明如何配置模型 API 和评测参数
- [WebUI 使用说明](./web_ui.html)：介绍 Gradio WebUI 的使用方法

## 快速参考

### 命令行使用

```bash
# 基本评测命令
python main.py --config models.yaml --dataset_path data/examples/choice_example.jsonl

# 指定输出目录
python main.py --config models.yaml --dataset_path data/examples/choice_example.jsonl --output_dir results/my_test

# 使用内置数据集
python main.py --config models.yaml --dataset_id mmlu

# 人工评测模式
python main.py --config models.yaml --dataset_id mmlu --mode manual
```

### WebUI 使用

```bash
# 启动 WebUI
python app.py

# 指定端口
python app.py --port 8080

# 指定主机（允许远程访问）
python app.py --host 0.0.0.0
```

## 常见问题解答

### 如何添加新的评测数据集？

请参考[数据集使用指南](../datasets/dataset_usage.html)中的"创建自定义数据集"部分。

### 如何自定义评测指标？

请参考[开发者指南](../developer_guide/extending.html)中的"添加自定义评测指标"部分。

### 如何解决 API 连接问题？

请检查：
1. API 地址是否正确
2. API 密钥是否有效
3. 网络连接是否正常
4. 是否有防火墙或代理限制

### 如何处理大型数据集？

对于大型数据集，可以使用批处理模式：

```bash
python main.py --config models.yaml --dataset_path large_dataset.jsonl --batch_size 10
```

## 获取帮助

如果您遇到任何问题或需要进一步的帮助，请：

1. 查阅本文档的相关章节
2. 检查[项目 GitHub 仓库](https://github.com/XpertMedAI/XpertEval)的 Issues 部分
3. 提交新的 Issue 描述您的问题
4. 联系项目维护者获取支持