import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import expect
from apps.organization.models import Organization
from apps.employee.models import Employee

# Helper function similar to the one in test_login_playwright.py
def human_type(page, locator, text, delay_ms=50):
    """Simulate human typing with a small delay."""
    locator.click()
    page.wait_for_timeout(50)
    locator.fill(text) 
    # locator.type(text, delay=delay_ms) # using fill is faster/more robust for functional tests

@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_employee_creation_and_lifecycle(live_server, page):
    """
    Test the full lifecycle of an employee:
    1. Login as Admin.
    2. Create a new Organization (via DB for setup).
    3. Use UI to create a new Employee.
    4. Verify Employee exists in the list.
    5. Edit Employee details.
    """
    
    # --- Setup ---
    # Create Admin User
    admin_user = get_user_model().objects.create_superuser(
        username="admin_e2e",
        email="admin@example.com",
        password="AdminPassword123!"
    )
    
    # Create an Organization to assign valid org in the form
    org = Organization.objects.create(
        org_code="TEST_IT",
        org_name="Testing Department",
        status="enabled"
    )

    # --- Login ---
    page.goto(f"{live_server.url}/login/")
    page.locator("input#username").fill("admin_e2e")
    page.locator("input#password").fill("AdminPassword123!")
    page.locator("button[type='submit']").click()
    
    # Ensure login success (check for dashboard or nav)
    expect(page.locator("text=注销")).to_be_visible()

    # --- Create Employee ---
    # Navigate to Employee Add Page
    page.goto(f"{live_server.url}/employee/add/")
    
    # Monitor for console errors just in case
    page.on("console", lambda msg: print(f"PAGE LOG: {msg.text}"))

    # Fill Form
    page.locator("input[name='emp_name']").fill("Playwright Tester")
    page.locator("select[name='gender']").select_option("male")
    page.locator("input[name='id_card']").fill("110101199001011234")
    page.locator("input[name='phone']").fill("13812345678")
    page.locator("input[name='email']").fill("tester@example.com")
    
    # Select Org (It's a select element)
    page.locator("select[name='org']").select_option(str(org.id))
    
    page.locator("input[name='position']").fill("Senior SDET")
    page.locator("input[name='hire_date']").fill("2024-01-01")
    
    # Select Employment Type
    page.locator("select[name='employment_type']").select_option("full_time")
    
    # Select Status
    page.locator("select[name='emp_status']").select_option("probation")

    # Submit
    page.locator("button[type='submit']").click()
    
    # --- Verify Creation ---
    # Should redirect to list
    expect(page).to_have_url(f"{live_server.url}/employee/")
    
    # Check if name appears in list
    expect(page.locator("text=Playwright Tester")).to_be_visible()
    expect(page.locator(f"text={org.org_name}")).to_be_visible()

    # --- Edit Employee ---
    # Click "Edit" link for this user.
    # We find the row containing the text, then find the Edit button/link.
    # Assuming standard table structure: Row -> Cell -> Edit Link
    
    # A robust way: row with "Playwright Tester", click "编辑" inside it.
    row = page.locator("tr", has_text="Playwright Tester")
    row.locator("text=编辑").click()
    
    # Verify we are on edit page
    expect(page.locator("h3:has-text('编辑档案')")).to_be_visible()
    
    # Change name
    page.locator("input[name='emp_name']").fill("Playwright Updated")
    page.locator("button[type='submit']").click()
    
    # Verify update in detail/list page (redirects to detail usually, let's check views.py)
    # View says success_url = reverse_lazy("employee:detail", ...)
    
    expect(page.locator("h3:has-text('Playwright Updated')")).to_be_visible()
    expect(page.locator("text=Senior SDET")).to_be_visible()

