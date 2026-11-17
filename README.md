# caoxu-qa-lab

曹旭的个人质量保障（QA）实验室。

这里集中记录我在接口自动化框架、测试平台开发，以及 AI 在软件测试中落地实践方面的学习代码、实验项目与成长路线，目标是为迈向高级测试架构师积累可复用、可运行的实践成果。

## 仓库结构

```text
caoxu-qa-lab/
├── api-automation-testing-learning/  # 接口自动化学习代码
│   └── day1/                         # requests GET / POST 入门示例
├── ecommerce-api-automation/         # 电商接口自动化项目（规划中）
└── insurance-lifecycle-lab/          # 保险业务生命周期 API 测试实验室
    ├── app/                          # FastAPI 服务实现
    ├── tests/                        # pytest + requests 自动化用例
    ├── requirements.txt              # Python 依赖
    ├── pytest.ini                    # pytest 配置
    ├── run_server.bat                # Windows 服务启动脚本
    ├── run_tests.bat                 # Windows 测试执行脚本
    └── README.md                     # 项目详细文档
```

## 当前项目

### insurance-lifecycle-lab

一个用于练习黑盒接口自动化的小型保险 API 服务，覆盖登录鉴权、产品与报价、投保与核保、支付与保单、批改、理赔和退保等完整业务流程。

项目中的支付、核保和审批均为应用内模拟，不依赖真实支付网关或第三方服务，因此测试过程可重复、结果可预期。

详细使用说明请参考：[insurance-lifecycle-lab/README.md](insurance-lifecycle-lab/README.md)

快速开始（Windows PowerShell）：

```powershell
cd d:/Data/caoxu-qa-lab/insurance-lifecycle-lab
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

服务启动后可访问：

- Swagger UI：<http://127.0.0.1:8000/docs>
- OpenAPI JSON：<http://127.0.0.1:8000/openapi.json>
- 健康检查：<http://127.0.0.1:8000/health>

执行自动化测试：

```powershell
cd d:/Data/caoxu-qa-lab/insurance-lifecycle-lab
python -m pytest
```

在 Windows 上也可以直接双击 `run_server.bat` 启动服务，或双击 `run_tests.bat` 执行测试。

### api-automation-testing-learning

用于沉淀接口自动化入门阶段的学习代码，例如使用 `requests` 发送 GET / POST 请求，适合作为基础能力的回顾与对照。

### ecommerce-api-automation

预留的电商接口自动化实践目录，后续用于补充更接近真实业务场景的接口测试框架与案例。

## 学习路线

1. 掌握 `requests` 基础请求构造、参数传递与响应断言。
2. 使用 `pytest` 组织测试用例、夹具、参数化与测试报告。
3. 基于 FastAPI 搭建可测试的模拟服务，理解接口契约与错误处理。
4. 围绕保险生命周期练习状态机、幂等、权限与业务规则测试。
5. 持续探索 AI 在测试用例生成、日志分析和质量洞察中的应用。

## 说明

- 本仓库内容主要用于个人学习与实验。
- 示例项目不涉及真实支付、真实用户数据或生产环境。
- 建议使用 Python 3.10 及以上版本运行实验项目。
