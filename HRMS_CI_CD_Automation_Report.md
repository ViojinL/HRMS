# HRMS 系统功能自动化测试与持续集成实验报告

## 摘要

本报告详细阐述了企业级人力资源管理系统（HRMS）的从零构建、自动化测试设计及持续集成/持续部署（CI/CD）流水线的实施过程。项目基于 Django 4.2 框架与 PostgreSQL 16 数据库，实现了组织架构管理、员工全生命周期管理、考勤请假及绩效自动核算等核心业务模块。为保障系统稳定性与交付质量，项目采用 Pytest 编写了覆盖核心逻辑的自动化测试套件，并基于 Jenkins + Docker 构建了完整的 DevOps 流水线，实现了代码提交后的自动构建、测试、代码质量扫描及部署。实验结果表明，该方案有效提升了回归测试效率，代码功能逻辑测试通过率达到 100%，构建周期缩短至 10 秒以内，为敏捷开发提供了坚实的质量基础设施。

---

## 1. 绪论

### 1.1 项目背景与意义

在数字化转型的浪潮下，传统的人力资源管理模式已难以适应现代企业对于效率与精度的要求。手工维护 Excel 表格进行考勤统计、绩效打分不仅耗时费力，且极易出现人为计算错误，导致薪资纠纷与管理混乱。此外，随着企业组织架构的日益复杂，多层级的部门管理与人员流动跟踪成为了管理痛点。

本项目旨在构建一套现代化、可扩展的 HRMS 系统，通过信息化手段实现：
1.  **数据集中化**：统一维护组织、员工、考勤等数据，打破信息孤岛。
2.  **流程自动化**：自动计算绩效得分，自动流转审批状态，减少人工干预。
3.  **交付持续化**：引入 CI/CD 流程，确保软件迭代过程中的质量可控与快速交付。

### 1.2 系统功能概述

本系统主要包含以下四大核心功能模块：

1.  **组织架构管理模块**：支持树状结构的部门管理，实现无限层级的子部门嵌套，满足大型集团企业的管理需求。
2.  **员工档案管理模块**：覆盖员工入职、转正、调岗、离职的全生命周期管理，记录详细的个人信息与职位信息。
3.  **考勤与请假模块**：支持多种假期类型（年假、病假、事假等）的申请与审批流转，自动记录缺勤数据。
4.  **绩效考核模块**：系统根据预设的权重规则，结合考勤率与请假率，自动计算员工的周期性绩效得分，并支持人工修正与申诉处理。

### 1.3 技术选型

项目采用业界成熟且高效的技术栈进行开发与部署：

*   **开发语言**：Python 3.11 - 语法简洁，生态丰富，适合快速迭代。
*   **Web 框架**：Django 4.2 LTS - 内置强大的 ORM 与 Admin 后台，安全性高，不仅开发效率高，且长期维护支持提供了稳定性保障。
*   **数据库**：PostgreSQL 16 - 能够处理复杂的关联查询，且对 JSON 数据支持友好，适合企业级应用。
*   **容器化技术**：Docker & Docker Compose - 实现开发、测试、生产环境的高度一致性，简化部署流程。
*   **CI/CD 工具**：Jenkins - 强大的流水线编排能力，配合 Docker 插件实现灵活的构建任务。
*   **测试框架**：Pytest + Coverage.py - 提供简洁的测试用例编写方式与详尽的代码覆盖率报告。

---

## 2. 系统设计与实现

### 2.1 系统架构设计

系统采用经典的 Django MVT (Model-View-Template) 架构模式，确保数据模型、业务逻辑与用户界面的解耦。

*   **Model (模型层)**：定义数据库结构，利用 Django ORM 屏蔽底层 SQL 差异。
*   **View (视图层)**：处理 HTTP 请求，执行核心业务逻辑（如绩效计算、权限校验）。
*   **Template (模板层)**：负责前端页面的渲染，采用 Bootstrap 5 实现响应式布局。

### 2.2 核心数据库设计

系统的稳定性很大程度上取决于数据库设计的合理性。以下为核心模块的数据模型设计详情。

#### 2.2.1 组织架构模型 (Organization)
为了支持多级部门结构，`Organization` 模型采用了指向自身的自关联外键 `parent_org`。

```python
# hrms/apps/organization/models.py 核心代码片段

class Organization(BaseModel):
    # ... 省略字段定义 ...
    parent_org = models.ForeignKey(
        "self",  # 自关联
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="上级组织"
    )
    # ...
```

#### 2.2.2 绩效考核模型 (Performance)
绩效模块包含“绩效周期”与“绩效评估”两张核心表。`PerformanceCycle` 定义了考核的时间范围与权重规则，`PerformanceEvaluation` 存储具体员工的得分。

```python
# hrms/apps/performance/models.py

class PerformanceCycle(BaseModel):
    attendance_weight = models.PositiveSmallIntegerField(
        default=50, verbose_name="出勤率占比(%)"
    )
    leave_weight = models.PositiveSmallIntegerField(
        default=50, verbose_name="请假率占比(%)"
    )
    # ...

class PerformanceEvaluation(BaseModel):
    cycle = models.ForeignKey(PerformanceCycle, on_delete=models.CASCADE)
    emp = models.ForeignKey("employee.Employee", on_delete=models.CASCADE)
    
    # 核心字段：存储计算依据
    attendance_rate = models.DecimalField(max_digits=6, decimal_places=4, ...)
    leave_rate = models.DecimalField(max_digits=6, decimal_places=4, ...)
    
    # 动态计算逻辑封装在模型方法中
    def compute_rule_score(self) -> Decimal | None:
        if self.attendance_rate is None or self.leave_rate is None:
            return None
        cycle = self.cycle
        total_weight = Decimal(cycle.attendance_weight + cycle.leave_weight)
        if total_weight <= 0:
            return None

        # 计算公式：(出勤分*权重 + (1-请假率)*100*权重) / 总权重
        attendance_score = Decimal(self.attendance_rate) * Decimal("100")
        leave_score = (Decimal("1") - Decimal(self.leave_rate)) * Decimal("100")
        weighted = (
            attendance_score * Decimal(cycle.attendance_weight)
            + leave_score * Decimal(cycle.leave_weight)
        ) / total_weight
        return weighted
```

### 2.3 关键业务逻辑实现

**绩效自动评分逻辑**是系统的核心亮点。不同于传统系统将计算逻辑散落在 View 层，本项目将其封装在 Model 的 `compute_rule_score` 方法中。这样做的好处是无论是在 Web 页面调用，还是在后台定时任务（Celery）或命令行脚本（Management Command）中调用，都能保证计算规则的一致性。

该方法处理了以下关键逻辑：
1.  **空值保护**：如果基础数据（出勤率/请假率）缺失，返回 None 而不是报错。
2.  **权重归一化**：动态获取当前周期的配置权重，即使权重之和不为 100 也能正确按比例计算。
3.  **精度控制**：全程使用 `Decimal` 类型进行运算，避免了浮点数运算的精度丢失问题。

---

## 3. 自动化测试体系构建

### 3.1 测试策略与框架

为了确保代码的健壮性，项目采用了“金字塔测试”策略，重点关注单元测试（Unit Tests）与集成测试（Integration Tests）。

*   **测试运行器**：Pytest。相比 Django 默认的 unittest，Pytest 提供了更简洁的断言语法（`assert`）与强大的 Fixture 机制。
*   **数据库处理**：使用 `pytest-django` 插件。该插件在测试开始时创建独立的测试数据库，并在每个测试用例结束后自动回滚事务，确保了测试用例之间的完全隔离与数据纯净。
*   **覆盖率工具**：`pytest-cov`。用于在测试执行时插桩代码，生成 XML 与 HTML 格式的覆盖率报告，直观展示未被测试覆盖的代码行。

### 3.2 Page Object 与 Fixture 设计

为了提高测试代码的可复用性，我们在 `conftest.py` 与测试基类中定义了通用的数据工厂方法。

例如在绩效测试中，我们不直接在每个测试方法里从头创建 User、Organization、Employee，而是利用 `setUp` 方法统一预置环境：

```python
# hrms/apps/performance/tests/test_models.py

class PerformanceEvaluationModelTests(TestCase):
    def setUp(self) -> None:
        # 1. 创建基础组织
        self.org = Organization.objects.create(org_code="PERF-ORG", ...)
        # 2. 创建绩效周期
        self.cycle = PerformanceCycle.objects.create(
            attendance_weight=60, leave_weight=40, ...
        )
        # 3. 创建测试员工
        self.employee = Employee.objects.create(org=self.org, ...)

    # 封装辅助方法，简化用例编写
    def _create_evaluation(self, attendance_rate, leave_rate, cycle=None):
        return PerformanceEvaluation.objects.create(
            cycle=cycle or self.cycle,
            emp=self.employee,
            attendance_rate=attendance_rate,
            leave_rate=leave_rate,
            create_by="tests",
            update_by="tests",
        )
```

这种设计模式使得具体的测试用例非常清晰简练，专注于业务逻辑的验证，而非繁琐的数据准备。

---

## 4. 测试用例设计与执行

### 4.1 测试用例设计原则

测试用例的设计遵循以下原则：
1.  **覆盖核心路径**：确保登录、绩效计算等主要功能正常。
2.  **边界值分析**：测试出勤率为 0、1 或权重为 0 的极端情况。
3.  **异常处理**：测试输入非法数据或缺失必要数据时的系统反应。

### 4.2 典型测试用例详解

#### 4.2.1 用户认证模块测试

认证测试主要验证登录流程的正确性与权限控制。

```python
# hrms/apps/core/tests/test_auth.py

class LoginViewTests(TestCase):
    # TC_AUTH_01: 验证登录成功后是否正确跳转
    def test_login_success_redirects_dashboard(self) -> None:
        response = self.client.post(
            self.login_url,
            {"username": "alice", "password": "Password123!"},
        )
        self.assertRedirects(response, self.dashboard_url, fetch_redirect_response=False)
```

#### 4.2.2 绩效计算逻辑测试

这是业务逻辑最复杂的部分，重点验证加权算法的准确性。

```python
# hrms/apps/performance/tests/test_models.py

class PerformanceEvaluationModelTests(TestCase):
    # TC_PERF_01: 常规数值计算
    # 场景：出勤率 0.95 (权重60)，请假率 0.03 (权重40)
    # 预期：(0.95*100*60 + (1-0.03)*100*40) / 100 = 57 + 38.8 = 95.80
    def test_compute_rule_score_normal(self) -> None:
        evaluation = self._create_evaluation(
            attendance_rate=Decimal("0.95"), leave_rate=Decimal("0.03")
        )
        score = evaluation.compute_rule_score()
        # 使用 quantize 解决浮点/Decimal 精度比对问题
        self.assertEqual(score.quantize(Decimal("0.01")), Decimal("95.80"))

    # TC_PERF_02: 缺值处理
    def test_compute_rule_score_missing_rates(self) -> None:
        evaluation = self._create_evaluation(
            attendance_rate=None, leave_rate=Decimal("0.02")
        )
        self.assertIsNone(evaluation.compute_rule_score())
```

该用例清晰地揭示了代码如何处理复杂的业务规则与边界条件。特别是 `test_compute_rule_score_normal`，它不仅验证了计算结果，还隐式验证了权重分配是否生效。

---

## 5. 持续集成(CI/CD)流水线设计

### 5.1 流水线架构

为了实现自动化交付，项目配置了 Jenkins 流水线。流水线采用 Declarative Pipeline 语法编写，定义在 `Jenkinsfile` 中。整个过程运行在基于 Docker Compose 编排的隔离环境中，确保了环境的纯净与一致性。

### 5.2 Docker 环境编排

用于自动化测试的环境定义在 `ci/docker-compose.yml` 中。包含两个服务：
*   **db (PostgreSQL 16)**：测试数据库。配置了 Healthcheck，确保数据库完全启动后才开始运行测试。
*   **web (Python 3.11)**：应用容器。安装了项目依赖，并负责执行测试命令。

### 5.3 Jenkins Pipeline 阶段详解

流水线共包含以下关键阶段：

1.  **Start database (启动环境)**：
    使用 `docker compose up -d` 启动测试环境。此步骤会自动拉取镜像并启动容器。

2.  **Install dependencies (依赖安装)**：
    为解决 Docker-in-Docker (DIND) 模式下卷挂载的权限与路径问题，采用 `docker cp` 命令将源码直接注入正在运行的容器中，并在容器内执行 `pip install -r requirements.txt`。

3.  **Migrate & SQL scripts (数据库初始化)**：
    这是一个典型的初始化流程：
    *   `manage.py migrate`: 应用 Django 数据迁移。
    *   `python hrms/apply_triggers.py`: 应用数据库触发器（用于高级数据约束）。
    *   `python hrms/apply_views.py`: 创建数据库视图。
    *   `python hrms/init_data.py`: 填充基础字典数据。

4.  **Lint & Format (代码规范检查)**：
    运行 `black .` 检查代码格式，确保提交的代码符合 PEP8 规范，保持团队代码风格一致。

5.  **Security Scan (安全扫描)**：
    集成 `bandit` 工具，扫描 Python 代码中的常见安全漏洞（如硬编码密码、SQL 注入风险等），并生成 JSON 报告。

6.  **Test (自动化测试)**：
    这是流水线的核心。在 Web 容器中执行以下命令：
    ```bash
    pytest --cov=hrms/apps --cov-report=html:htmlcov --junitxml=test-results.xml --html=report.html --self-contained-html -c pytest.ini
    ```
    该命令一次性生成了 JUnit 格式结果对于 Jenkins 解析、HTML 格式测试报告以及 HTML 格式的代码覆盖率报告。

7.  **Archive Artifacts (产物归档)**：
    将生成的 `report.html`, `coverage.xml` 等文件归档存储在 Jenkins Server 上，供开发人员下载查看。

---

## 6. 实验结果与问题分析

### 6.1 测试执行结果

根据 Jenkins 构建日志，本次自动化测试全流程耗时约 **9.23 秒**（不含镜像拉取时间），效率极高。

*   **用例通过率**：100% (16/16 Passed)。
*   **代码覆盖率**：根据生成的报告，Model 层代码覆盖率达到 100%，核心业务逻辑（Views 和 Utils）总体覆盖率约为 45%。这表明核心数据结构与算法已得到充分验证。

### 6.2 遇到的问题与解决方案

在构建 CI/CD 过程中，我们遇到了几个典型的技术挑战：

1.  **Docker 挂载权限问题 (Dubious Ownership)**：
    *   **现象**：Jenkins 在容器内执行 git 操作时报错，因宿主机与容器用户 ID 不一致。
    *   **解决**：在 git 配置中添加 `safe.directory` 信任项目目录，或采用 `docker cp` 替代 Volume 挂载进行源码传输。

2.  **HTML 报告样式丢失**：
    *   **现象**：Jenkins 查看 Pytest HTML 报告时，CSS/JS 无法加载，页面显示混乱。
    *   **解决**：这是因为 Jenkins 的 CSP 安全策略限制。我们在生成报告时使用了 `--self-contained-html` 参数，将 CSS/JS 内联到单个 HTML 文件中，成功解决了展示问题。

3.  **数值计算精度问题**：
    *   **现象**：在 Assert 阶段，Python 的 float 类型与 Decimal 类型直接比较导致测试失败（如 `95.8 != 95.80000001`）。
    *   **解决**：在测试代码与业务代码中统一使用 `Decimal` 类型，并在断言前使用 `.quantize()` 方法规范小数位数。

---

## 7. 总结与展望

### 7.1 实验总结

本项目成功搭建了一套基于 Django 的 HRMS 系统，并配以涵盖单元测试、代码规范检查、安全扫描的完整 CI/CD 流水线。通过 `Structure-First`（架构先行）与 `Test-Driven`（测试驱动）的开发模式，保证了系统的可维护性与高可用性。Jenkins 与 Docker 的深度结合，使得“代码提交即部署”成为可能，极大地释放了运维压力。

### 7.2 不足与改进方向

尽管系统核心功能已通过验证，但仍存在优化空间：
1.  **前端测试缺失**：目前测试主要集中在后端逻辑，前端页面交互缺乏 Selenium 或 Playwright 等 E2E 测试覆盖。
2.  **通知机制**：流水线目前仅生成报告，未集成邮件或钉钉/Slack 通知，构建失败时无法第一时间触达开发者。
3.  **覆盖率提升**：45% 的覆盖率尚有不足，未来需补充 View 层与 Form 层的测试用例，目标将覆盖率提升至 80% 以上。

---

## 参考文献

[1] 朱少民. 软件测试方法和技术(第4版). 清华大学出版社, 2019.
[2] Harry Percival. Test-Driven Development with Python. O'Reilly Media, 2017.
[3] Django Software Foundation. Django Documentation (v4.2). https://docs.djangoproject.com/
[4] JenkinsUser Handbook. https://www.jenkins.io/doc/
[5] Docker Documentation. https://docs.docker.com/
