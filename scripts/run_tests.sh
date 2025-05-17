#!/bin/bash
# 运行测试脚本

# 确保脚本在项目根目录下执行
cd "$(dirname "$0")/.." || exit 1

# 运行所有单元测试
echo "运行所有单元测试..."
python -m unittest discover -s tests/unit -p "test_*.py"

# 如果有集成测试
# echo "运行所有集成测试..."
# python -m unittest discover -s tests/integration -p "test_*.py"

# 检查是否所有测试都通过
if [ $? -eq 0 ]; then
    echo "✅ 所有测试通过!"
    exit 0
else
    echo "❌ 测试失败，请检查错误信息。"
    exit 1
fi 