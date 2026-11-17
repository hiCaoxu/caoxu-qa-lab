# InsureLab - 保险生命周期 API 实验室

这是一个刻意保持精简但贴近真实的保险 API 服务，用于通过 `pytest + requests` 练习黑盒接口自动化。

项目不接入真实支付网关或第三方服务。支付、核保和审批均在应用内部模拟，因此每个测试都是确定且可重复的。

## 1. 快速开始

```bash
cd D:/Data/caoxu-qa-lab/insurance-lifecycle-lab
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

打开以下地址：

- Swagger UI：<http://127.0.0.1:8000/docs>
- OpenAPI JSON：<http://127.0.0.1:8000/openapi.json>
- 健康检查：<http://127.0.0.1:8000/health>

在 Windows 上也可以直接双击 `run_server.bat` 启动服务。

## 2. 初始化账号

数据库会在服务启动时自动初始化。

| 用户名 | 密码 | 角色 | 说明 |
|---|---|---|---|
| `admin` | `Admin@123` | `ADMIN` | 审核核保、批改、理赔和退保 |
| `demo` | `Demo@123` | `USER` | 普通用户 |
| `demo2` | `Demo2@123` | `USER` | 用于跨用户权限测试 |

初始化产品：

| 编码 | 名称 | 类型 | 保障期限 | 自动核保限额 |
|---|---|---|---|---|
| `ACC001` | 安心意外险 | `ACCIDENT` | 12 个月 | 200000 |
| `HLTH001` | 健康守护医疗险 | `HEALTH` | 12 / 36 个月 | 300000 |
| `CI001` | 岁月安康重疾险 | `CRITICAL_ILLNESS` | 60 / 120 个月 | 200000 |

## 3. 运行自动化测试

```bash
python -m pytest
```

如果全局安装的 pytest 插件与当前环境冲突，可以禁用插件自动加载：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest
```

PowerShell：

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest
```

生成 HTML 报告：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -p pytest_metadata.plugin -p pytest_html.plugin --html=reports/report.html --self-contained-html
```

PowerShell：

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest -p pytest_metadata.plugin -p pytest_html.plugin --html=reports/report.html --self-contained-html
```

在 Windows 上也可以直接双击 `run_tests.bat` 执行测试。

测试套件会在随机空闲端口启动独立的 uvicorn 进程，并使用临时 SQLite 数据库。它**不会**修改本地的 `data/insurelab.db`。

## 4. API 路由

所有业务接口都在 `/api/v1` 下。

### 认证

| 方法 | 路径 |
|---|---|
| POST | `/auth/register` |
| POST | `/auth/login` |
| GET | `/auth/me` |

### 产品与报价

| 方法 | 路径 |
|---|---|
| GET | `/products` |
| GET | `/products/{product_id}` |
| POST | `/quotes` |
| GET | `/quotes/{quote_id}` |

### 投保与核保

| 方法 | 路径 |
|---|---|
| POST | `/applications` |
| POST | `/applications/{app_id}/submit` |
| GET | `/applications/{app_id}` |
| GET | `/applications` |
| POST | `/admin/applications/{app_id}/underwrite` |

### 支付与保单

| 方法 | 路径 |
|---|---|
| POST | `/payments/orders` |
| POST | `/payments/orders/{order_id}/pay` |
| GET | `/payments/orders/{order_id}` |
| POST | `/payments/callback` |
| GET | `/policies` |
| GET | `/policies/{policy_id}` |
| GET | `/policies/{policy_id}/timeline` |

回调接口需要请求头 `X-Callback-Token`。默认值为 `callback-secret`，可通过环境变量 `CALLBACK_TOKEN` 配置。

### 批改、理赔与退保

| 方法 | 路径 |
|---|---|
| POST | `/policies/{policy_id}/endorsements` |
| GET | `/policies/{policy_id}/endorsements` |
| GET | `/endorsements/{endorsement_id}` |
| POST | `/admin/endorsements/{id}/review` |
| POST | `/claims` |
| GET | `/claims/{claim_id}` |
| GET | `/claims` |
| POST | `/admin/claims/{id}/decide` |
| POST | `/admin/claims/{id}/pay` |
| POST | `/policies/{policy_id}/surrender` |
| GET | `/surrenders/{surrender_id}` |
| GET | `/policies/{policy_id}/surrenders` |
| POST | `/admin/surrenders/{id}/review` |

## 5. 状态机

投保单：

```text
DRAFT -> SUBMITTED -> UNDERWRITING -> APPROVED -> PAYING -> POLICY_ISSUED
                                  \-> REJECTED
```

支付订单：

```text
INIT -> SUCCESS
INIT -> FAILED -> SUCCESS
```

保单：

```text
ACTIVE -> SURRENDER_PENDING -> SURRENDERED
                           \-> ACTIVE
```

理赔：

```text
SUBMITTED -> REVIEWING -> APPROVED -> PAID
                       \-> REJECTED
```

批改 / 退保：

```text
PENDING -> APPROVED
PENDING -> REJECTED
```

非法状态流转会返回 HTTP `409`，错误码为 `INVALID_STATE_TRANSITION`。

## 6. 值得测试的业务规则

- 保费公式：`base_rate * (sum_insured / 10000) * (term_months / 12) * age_factor`
  - `age_factor`：`<=30 -> 1.0`、`31-40 -> 1.1`、`41-50 -> 1.25`、`>50 -> 1.5`
- 自动核保：
  - 被保险人证件号以 `0000` 结尾时进入黑名单并拒保
  - 保额超过 `auto_approve_limit` 时需要人工审核
- 支付订单创建支持 `idempotency_key`
- 理赔申请支持 `idempotency_key`
- 出险日期必须落在保单保障期间内
- 理赔金额必须大于 0，且不能超过保额
- 退保金额：`premium * remaining_months / total_months * 0.9`
- 只有 `ACTIVE` 状态的保单支持批改、理赔和退保

## 7. 统一错误格式

```json
{
  "code": "RULE_AGE_OUT_OF_RANGE",
  "message": "Age must be between 18 and 60",
  "details": {}
}
```

常见错误码：

| 错误码 | HTTP |
|---|---|
| `UNAUTHENTICATED` / `INVALID_TOKEN` | 401 |
| `FORBIDDEN` | 403 |
| `VALIDATION_ERROR` | 422 |
| `INVALID_STATE_TRANSITION` | 409 |
| `IDEMPOTENCY_CONFLICT` | 409 |
| `POLICY_NOT_ACTIVE` | 422 / 409 |

## 8. 项目结构

```text
insurance-lifecycle-lab/
  app/
    api/          HTTP 路由
    services/     定价、核保、状态机
    main.py       FastAPI 应用入口
    models.py     SQLAlchemy 模型
    schemas.py    Pydantic 请求/响应模型
    seed.py       产品与用户初始化数据
  tests/
    conftest.py   测试服务与登录夹具
    client.py     requests 封装
    helpers.py    流程构造器
    test_*.py     接口自动化用例
  requirements.txt
  pytest.ini
  README.md
```
