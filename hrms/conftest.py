import pytest
from datetime import datetime


def pytest_addoption(parser):
    parser.addoption(
        "--e2e",
        action="store_true",
        default=False,
        help="run Playwright end-to-end tests",
    )


def pytest_html_report_title(report):
    # pytest-html>=3 uses a `report` object instead of `main_title`
    report.title = "HRMS 项目测试报告"


def pytest_configure(config):
    # 修改环境列名称
    if hasattr(config, "_metadata"):
        config._metadata["项目名称"] = "HRMS_Django"
        config._metadata["测试时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 删除一些不需要显示的默认英文信息
        config._metadata.pop("Packages", None)
        config._metadata.pop("Platform", None)
        config._metadata.pop("Plugins", None)


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    # 可以在这里做一些退出后的汉化处理，但主要通过上面两个钩子
    pass


def pytest_collection_modifyitems(config, items):
    if config.getoption("--e2e"):
        return
    skip_e2e = pytest.mark.skip(reason="use --e2e to run Playwright tests")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)
