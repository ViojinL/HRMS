import pytest
from datetime import datetime

def pytest_html_report_title(main_title):
    main_title.set_text("HRMS 项目测试报告")

def pytest_configure(config):
    # 修改环境列名称
    if hasattr(config, '_metadata'):
        config._metadata['项目名称'] = 'HRMS_Django'
        config._metadata['测试时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 删除一些不需要显示的默认英文信息
        del config._metadata['Packages']
        del config._metadata['Platform']
        del config._metadata['Plugins']

@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    # 可以在这里做一些退出后的汉化处理，但主要通过上面两个钩子
    pass
