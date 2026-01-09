import os
from pathlib import Path

import pytest

# Allow synchronous DB operations in async contexts (Playwright threads)
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# Create directories for test artifacts
SCREENSHOTS_DIR = Path("test-results/screenshots")
VIDEOS_DIR = Path("test-results/videos")
TRACES_DIR = Path("test-results/traces")

for directory in [SCREENSHOTS_DIR, VIDEOS_DIR, TRACES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def browser_type_launch_args():
    headless = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() != "false"
    slow_mo = int(os.getenv("PLAYWRIGHT_SLOW_MO", "60"))
    return {"headless": headless, "slow_mo": slow_mo}


@pytest.fixture(scope="session")
def browser_context_args():
    """Configure browser context with video and screenshot settings."""
    return {
        "viewport": {"width": 1280, "height": 720},
        "record_video_dir": str(VIDEOS_DIR),
        "record_video_size": {"width": 1280, "height": 720},
    }


@pytest.fixture
def page(context, request):
    """Override default page fixture to add screenshot on failure."""
    page = context.new_page()
    
    # Start tracing before the test
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    
    yield page
    
    # Save trace and screenshot on test failure
    if request.node.rep_call.failed:
        test_name = request.node.name.replace("[", "_").replace("]", "_")
        
        # Save screenshot
        screenshot_path = SCREENSHOTS_DIR / f"{test_name}_failure.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"\n📸 Screenshot saved: {screenshot_path}")
        
        # Save trace
        trace_path = TRACES_DIR / f"{test_name}_trace.zip"
        context.tracing.stop(path=str(trace_path))
        print(f"🔍 Trace saved: {trace_path}")
    else:
        # Stop tracing without saving if test passed
        context.tracing.stop()
    
    page.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Store test result for screenshot decision."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
