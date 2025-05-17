#!/bin/bash
# 运行测试脚本

# 确保脚本在项目根目录下执行
cd "$(dirname "$0")/.." || exit 1

# 创建必要的目录
mkdir -p logs

# 运行所有单元测试
echo "运行所有单元测试..."
python -m unittest discover -s tests/unit -p "test_*.py"

# 检查是否所有单元测试都通过
UNIT_TESTS_RESULT=$?

# 测试日志功能
echo -e "\n测试日志功能..."
python scripts/test_logger.py

# 检查是否日志功能测试通过
LOGGER_TEST_RESULT=$?

# 如果有集成测试
# echo -e "\n运行所有集成测试..."
# python -m unittest discover -s tests/integration -p "test_*.py"
# INTEGRATION_TESTS_RESULT=$?

# 检查是否所有测试都通过
if [ $UNIT_TESTS_RESULT -eq 0 ] && [ $LOGGER_TEST_RESULT -eq 0 ]; then
    echo -e "\n✅ 所有测试通过!"
    exit 0
else
    echo -e "\n❌ 测试失败，请检查错误信息。"
    exit 1
fi 