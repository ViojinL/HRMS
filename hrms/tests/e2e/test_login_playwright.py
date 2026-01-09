import re

import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import expect


def human_type(page, locator, text, delay_ms=120, pause_ms=60):
    for ch in text:
        locator.type(ch, delay=delay_ms)
        page.wait_for_timeout(pause_ms)


@pytest.mark.django_db
@pytest.mark.e2e
def test_login_flow_human_like(live_server, page):
    user = get_user_model().objects.create_user(
        username="e2e_user",
        password="E2ePass123!",
    )

    login_url = f"{live_server.url}/login/"
    page.goto(login_url, wait_until="domcontentloaded")
    page.wait_for_timeout(300)

    username = page.locator("input#username")
    password = page.locator("input#password")
    submit = page.locator("button[type='submit']")

    username.click()
    human_type(page, username, user.username)
    page.wait_for_timeout(150)
    password.click()
    human_type(page, password, "E2ePass123!")

    submit.hover()
    page.wait_for_timeout(150)
    submit.click()

    expect(page).to_have_url(
        re.compile(re.escape(live_server.url) + r"/$")
    )
    expect(page.get_by_text("您的账号尚未关联员工档案")).to_be_visible()
