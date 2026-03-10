# AI-Data-Copilot

一个基于 LangChain + LLM 的 AI 数据分析 Copilot。

## 功能

- 自然语言生成 SQL 并查询数据库
- 自动修复 SQL 错误
- 数据分析报告生成（文字 + 图表）
- 支持多表、多条件、聚合查询

## 技术栈

- Python
- LangChain
- DeepSeek/OpenAI API
- SQLite + Pandas
- Matplotlib 可视化

## 使用方法

1. 克隆项目

```bash
git clone https://github.com/你的用户名/ai-data-copilot.git
cd ai-data-copilot
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3.设置环境变量
```bash
export DEEPSEEK_API_KEY=APIKEY
```

4.运行
```bash
python run.py 
```