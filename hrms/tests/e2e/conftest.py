import os

import pytest

# Allow synchronous DB operations in async contexts (Playwright threads)
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


@pytest.fixture(scope="session")
def browser_type_launch_args():
    headless = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() != "false"
    slow_mo = int(os.getenv("PLAYWRIGHT_SLOW_MO", "60"))
    return {"headless": headless, "slow_mo": slow_mo}
