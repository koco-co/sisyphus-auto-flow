# 自定义测试运行器规范

> 当 fingerprint.test_runner.type == "custom" 时加载

## 规则

1. 不生成裸 pytest 命令作为验收命令
2. 使用项目已有的测试运行器（run_demo.py 等）来运行测试
3. 按模块入口组织验收命令

## 示例

```bash
# 运行全部测试
python run_demo.py

# 运行特定模块
python run_demo.py --module batch
python run_demo.py --module dataapi
```
