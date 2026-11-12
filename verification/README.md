本目录是冻结产物的独立验收原件。实际环境：Windows，Python 3.14.3，未容器化，不依赖运行期外部服务。完整依赖及真实模块路径见 environment-reviewed.json。

先安装记录中的同版 Python，检出冻结产物提交并建立虚拟环境；根据实际依赖记录安装测试依赖，按 verification/reproduction-notes.md 的本题步骤配置。需要插件入口的项目（如 Bandit）在检出目录用 python -m pip install -e . 注册；纯 Python 源码入口直接按已记录 PYTHONPATH 加载。PYTHONPATH 指向检出目录、src 和 lib。各 verification 子目录保留实际 argv、原始输出、JUnit、退出码和用例。命令 JSON 中的原机绝对路径需替换为本次检出位置及相应子目录；测试断言不改。

模型原轨中的测试与本目录独立验收分开记录。原生 JSONL 和75秒连续运行录像各自只有一个，保存在对应飞书附件字段，此处不另放轨迹。工程/夹具问题按 evidence-map.json 限定归因；测试通过不等于一般性安全证明。

冻结产物提交：https://github.com/9873199/pyyaml-strict-keys/commit/42ab4d14072972f5e0e4859b0985c4e38e0a0b39
这些独立验收文件在模型首轮结束后生成，不是模型原轨中的测试。
