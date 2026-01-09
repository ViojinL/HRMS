import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import expect
from hrms.apps.organization.models import Organization
from hrms.apps.employee.models import Employee
from django.utils import timezone

@pytest.mark.django_db
@pytest.mark.e2e
def test_leave_application_and_approval_flow(live_server, page):
    """
    Test Leave Workflow:
    1. Setup: Manager and Subordinate.
    2. Subordinate applies for leave.
    3. Manager approves leave.
    4. Verify status.
    """
    
    # --- Setup ---
    # Create Organization
    org = Organization.objects.create(
        org_code="TEST_LEAVE",
        org_name="Leave Dept",
        status="enabled"
    )
    
    # Create Manager User & Employee
    manager_user = get_user_model().objects.create_user(
        username="manager01", password="Password123!"
    )
    manager = Employee.objects.create(
        emp_id="MGR001",
        emp_name="Manager Alice",
        org=org,
        user=manager_user,
        email="manager@test.com",
        phone="13900000001",
        hire_date=timezone.now().date(),
        emp_status="active"
    )
    
    # Create Subordinate User & Employee
    sub_user = get_user_model().objects.create_user(
        username="sub01", password="Password123!"
    )
    subordinate = Employee.objects.create(
        emp_id="SUB001",
        emp_name="Sub Bob",
        org=org,
        report_to=manager,      # Assuming report_to is the field for hierarchy
        manager_emp=manager,    # Or manager_emp, checking model def is best but assuming manager_emp based on views
        user=sub_user,
        email="sub@test.com",
        phone="13900000002",
        hire_date=timezone.now().date(),
        emp_status="active"
    )
    
    # --- Subordinate Applies ---
    # Login as Subordinate
    page.goto(f"{live_server.url}/login/")
    page.locator("input#username").fill("sub01")
    page.locator("input#password").fill("Password123!")
    page.locator("button[type='submit']").click()
    
    # Navigate to Apply Page
    page.goto(f"{live_server.url}/leave/apply/")
    
    # Fill Form
    # Leave Type (Select)
    # Assuming 'annual' or similar exists. Inspect choice list or select first option
    page.locator("select[name='leave_type']").select_option(index=1) # Select second option (often first is placeholder or actual type)
    
    # Start/End Time
    # Format YYYY-MM-DDTHH:MM
    start_str = (timezone.now() + timezone.timedelta(days=1)).strftime("%Y-%m-%dT09:00")
    end_str = (timezone.now() + timezone.timedelta(days=1)).strftime("%Y-%m-%dT18:00")
    
    page.locator("input[name='start_time']").fill(start_str)
    page.locator("input[name='end_time']").fill(end_str)
    
    page.locator("textarea[name='reason']").fill("Need rest for E2E testing.")
    
    # Submit
    page.locator("button[type='submit']").click()
    
    # Verify redirect to list and "审核中" (Reviewing) status
    expect(page).to_have_url(f"{live_server.url}/leave/")
    expect(page.locator("text=审核中")).to_be_visible()
    
    # Logout
    page.goto(f"{live_server.url}/logout/")

    # --- Manager Approves ---
    # Login as Manager
    page.goto(f"{live_server.url}/login/")
    page.locator("input#username").fill("manager01")
    page.locator("input#password").fill("Password123!")
    page.locator("button[type='submit']").click()
    
    # Go to Approvals
    page.goto(f"{live_server.url}/leave/approvals/")
    
    # Should see the request from Sub Bob
    expect(page.locator("text=Sub Bob")).to_be_visible()
    expect(page.locator("text=Need rest")).to_be_visible()
    
    # Click "处理" (Handle)
    row = page.locator("tr", has_text="Sub Bob")
    row.locator("text=处理").click()
    
    # On Detail Page, Approve
    # Expect "批准申请" button
    approve_btn = page.locator("button[value='approve']")
    expect(approve_btn).to_be_visible()
    approve_btn.click()
    
    # Verify Status changed to "已批准" (Approved) on detail page or redirected page
    # Usually redirects to list or stays on detail. 
    # Let's assume it redirects to approval list or stays on detail with updated status.
    # The view usually redirects to success_url.
    # We can check for "success message" or status text.
    expect(page.locator("text=已批准")).to_be_visible()

