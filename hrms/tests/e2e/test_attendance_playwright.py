import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import expect
from hrms.apps.organization.models import Organization
from hrms.apps.employee.models import Employee
from django.utils import timezone

@pytest.mark.django_db
@pytest.mark.e2e
def test_attendance_check_in_flow(live_server, page):
    """
    Test details:
    1. Login as Employee.
    2. Visit Attendance Dashboard.
    3. Perform Check-in.
    4. Verify success message and updated UI status.
    """
    
    # --- Setup ---
    org = Organization.objects.create(
        org_code="TEST_ATT",
        org_name="Attendance Dept",
        status="enabled"
    )
    
    user = get_user_model().objects.create_user(
        username="att_user", password="Password123!"
    )
    
    emp = Employee.objects.create(
        emp_id="ATT001",
        emp_name="CheckIn Tester",
        org=org,
        user=user,
        email="att@test.com",
        phone="13900000003",
        hire_date=timezone.now().date(),
        emp_status="active"
    )

    # --- Login ---
    page.goto(f"{live_server.url}/login/")
    page.locator("input#username").fill("att_user")
    page.locator("input#password").fill("Password123!")
    page.locator("button[type='submit']").click()
    
    # --- Dashboard ---
    page.goto(f"{live_server.url}/attendance/")
    
    # Check if clock is visible (simple check that page loaded)
    expect(page.locator("#clock")).to_be_visible()
    
    # Verify "上班打卡" (Check In) button exists
    # The text changes based on status, initial state is "上班打卡"
    check_in_btn = page.locator("button[type='submit']")
    expect(check_in_btn).to_contain_text("上班打卡")
    
    # Click Check In
    check_in_btn.click()
    
    # --- Verify Result ---
    # Should stay on dashboard or redirect to it
    expect(page).to_have_url(f"{live_server.url}/attendance/")
    
    # Check for success message "签到成功" or "早安"
    # Django messages usually appear in a specific div.
    # We can search for text on page.
    expect(page.locator("text=签到成功")).to_be_visible()
    
    # Verify button text might have changed to "下班打卡" or "更新打卡" depending on logic/time
    # Since it's same day, logic says:
    # if is_morning: check_in.
    # if submitted again in morning: "warning: already checked in".
    # if afternoon: check_out.
    
    # Let's just verify the record appears in the status area
    # "上班" label next to time
    expect(page.locator("text=上班")).to_be_visible()
    
