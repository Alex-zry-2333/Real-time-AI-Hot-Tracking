# 🤝 贡献指南

感谢您对「实时AI热点追踪」项目的关注！以下是参与贡献的方式：

## 如何添加新项目

### 方式一：使用脚本（推荐）

```bash
cd scripts
python manual_add.py
```

按提示输入GitHub项目URL并选择分类即可。

### 方式二：手动编辑

1. Fork 本仓库
2. 编辑 `data/active_repos.json`，在数组末尾添加新项目：

```json
{
  "name": "user/repo",
  "category": "agent",
  "description_cn": "中文简介",
  "description_en": "English description",
  "stars": 0,
  "last_updated": null,
  "added_date": "2026-06-10T00:00:00",
  "status": "active"
}
```

3. 提交PR

## 分类说明

| 分类ID | 中文名 | 适用项目 |
|--------|--------|----------|
| llm | 大语言模型 | 开源LLM、模型权重 |
| multimodal | 多模态模型 | 文生图/视频/3D |
| agent | Agent框架 | 智能体、自动化框架 |
| devtools | 开发工具 | 推理引擎、部署工具 |
| coding | 代码助手 | AI编程插件、IDE工具 |
| audio | 语音与音频 | TTS、ASR、语音克隆 |
| dataset | 数据集与评测 | 数据集、评测基准 |
| inference | 推理优化 | 量化、压缩、加速 |
| application | AI应用 | 终端产品、实用工具 |
| safety | 安全与对齐 | RLHF、红队测试 |
| research | 科研工具 | 微调框架、实验平台 |
| rag | 向量与检索 | RAG、向量数据库 |
| edge | 硬件与边缘 | 边缘部署、NPU |
| others | 其他创新 | 难以归类的前沿项目 |

## 项目收录标准

- 必须是**开源项目**（有GitHub仓库）
- 与**AI/机器学习**直接相关
- 优先收录 Stars > 1000 或近期快速增长的项目
- 工具类项目要求有明确的使用场景

## 更新与归档规则

- 每周自动检查所有项目状态
- **归档条件**：超过 **180天** 未更新 **且** Stars < **10,000**
- 归档项目会保留在 `data/archived_repos.json`，但README中标注为已停止更新

## 提交PR前检查

- [ ] 项目URL正确且可访问
- [ ] 选择了合适的分类
- [ ] 提供了中英文简介
- [ ] 没有重复添加已有项目

## 问题反馈

如有问题或建议，欢迎提交 [Issue](../../issues)。
