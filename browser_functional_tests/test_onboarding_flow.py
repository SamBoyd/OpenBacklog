import time
from typing import Optional
import pytest
from playwright.sync_api import expect, Page, Frame
import re

BASE_URL = "http://localhost"

@pytest.fixture
def reset_test_user():
    import subprocess
    cmd = "docker exec -i fastapi ./manage.py reset-test-user"
    subprocess.run(cmd, shell=True, check=True)

# Add a custom page fixture that sets ignore_https_errors to True
@pytest.fixture(scope="function")
def browser_page(reset_test_user, browser): # type: ignore
    context = browser.new_context(
        ignore_https_errors=True,
        # Use incognito mode to isolate sessions
        storage_state=None,
        viewport={"width":1280,"height":1020}
    )
    page = context.new_page()
    # Clear any existing cookies
    context.clear_cookies()
    yield page
    context.close()

def test_onbording_flow_with_dev_user(browser_page: Page):
    browser_page.set_default_timeout(10_000)

    browser_page.goto("http://localhost/")
    expect(browser_page.get_by_role("link", name="OpenBacklog")).to_be_visible()
    browser_page.get_by_text("Sign in").click()
    expect(browser_page.get_by_role("heading", name="Plan Your Projects")).to_be_visible(timeout=10_000)
    browser_page.get_by_role("button", name="Next").click()
    
    expect(browser_page.get_by_role("heading", name="AI Coding Assistants")).to_be_visible()
    browser_page.get_by_role("button", name="Next").click()

    expect(browser_page.get_by_role("heading", name="Context-Aware Development")).to_be_visible()
    browser_page.get_by_role("button", name="Next").click()

    expect(browser_page.get_by_role("heading", name="What's your project name?")).to_be_visible()
    browser_page.get_by_role("textbox", name="Project Name").click()
    browser_page.get_by_role("textbox", name="Project Name").fill("TaskManagement")    
    browser_page.get_by_role("button", name="Next").click()

    expect(browser_page.get_by_role("heading", name="Hybrid Pricing Model")).to_be_visible()
    browser_page.get_by_role("button", name="Setup Monthly Subscription").click()

    expect(browser_page.get_by_role("heading", name="Start Your Subscription")).to_be_visible(timeout=30_000)

    # Wait for Stripe iframes to load
    browser_page.wait_for_function(
        "() => document.querySelectorAll('iframe[src*=\"js.stripe.com\"]').length >= 2",
        timeout=30_000
    )

    time.sleep(10)
    
    stripe_address_frame: Optional[Frame] = browser_page.frame(url='https://js.stripe.com/v3/elements-inner-address-*')
    if stripe_address_frame is None:
        raise Exception("Stripe frame not found")
    
    stripe_address_frame.locator("input[name='name']").fill("John Doe")

    stripe_address_frame.locator("select[name='country']").select_option("United States")

    stripe_address_frame.locator("input[name='addressLine1']").fill("123 Main St")

    stripe_address_frame.locator("input[name='locality']").fill("San Francisco")

    stripe_address_frame.locator("select[name='administrativeArea']").select_option("California")
    
    stripe_address_frame.locator("input[name='postalCode']").fill("12345")

    stripe_payment_frame: Optional[Frame] = browser_page.frame(url='https://js.stripe.com/v3/elements-inner-payment-*')
    if stripe_payment_frame is None:
        raise Exception("Stripe frame not found")
    
    time.sleep(3)

    stripe_payment_frame.get_by_role("button", name="Card").click()
    stripe_payment_frame.locator("input[name='number']").fill("4242424242424242")
    stripe_payment_frame.locator("input[name='expiry']").fill("01/2028")
    stripe_payment_frame.locator("input[name='cvc']").fill("123")

    browser_page.get_by_role("checkbox", name="I agree to the Terms of").click()

    time.sleep(3)

    browser_page.get_by_role("button", name="Start Subscription").click()

    expect(browser_page.get_by_role("heading", name="Subscription Active!")).to_be_visible(timeout=30_000)
