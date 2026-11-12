# 严格配置加载器复现

冻结产物提交：42ab4d14072972f5e0e4859b0985c4e38e0a0b39。Windows，实际Python 3.14.3，纯Python加载路径，未用容器，无运行期服务或网络。完整依赖与import路径在environment-reviewed.json；libyaml扩展未构建，也不在本题范围。

检出冻结提交，以同版Python建环境并安装记录中的测试依赖，PYTHONPATH指向检出目录/lib。各verification子目录命令JSON保留实际argv，按新检出位置替换原机绝对路径，用例断言不改。完整回归命令为python -m pytest -q tests；相关merge/dump_load子集7通过，完整套件1319通过。两者范围不同。

acceptance-r1独立22通过/1失败的那条误将context_mark当作唯一允许的首次位置存放处，实际error.problem文本已经给出首次行列；该假设超出题面约定，不计模型缺陷。fixture-provenance-r1保留原夹具和修订理由。acceptance-r2为修订后23通过。alias-marks-r1是独立有效位置反例：普通/嵌套与普通业务键3通过，两种别名键第二次位置2失败。位置缺陷同根因，不重复计分。

原轨自带32例通过、完整1319通过；自带alias测试发现锚点复用后改成接受锚点位置，最终回答已披露此限制。独立反例要求的第3行alias位置仍未提供。

初始正式尝试在第一次请求即HTTP400，无有效模型答复，无工具动作，未评分，原件留在cache。相同配置非题目工具探测恢复后，仅工程重试一次；有效会话首轮完整输入与原题逐字一致，三处显式high不变。run-provenance-r1是元数据说明，不含第二个轨迹。

product-demo-r1/demo_yaml.py与录屏控制台是独立验证工具，真实调用冻结库，不冒充模型产品界面。recorded-runtime-r1保留75秒连续录屏的实际命令、输出及退出码[0,0,1]。原生JSONL只有一个有效会话附件，不放入公开验收目录。
