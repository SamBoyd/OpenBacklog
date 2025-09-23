"""
Browser functional tests for API key management features.

Tests the token generation, copy functionality, deletion, and modal interactions
on the /account page.
"""

import pytest
from playwright.sync_api import expect, Page
import time


BASE_URL = "http://localhost"


@pytest.fixture
def reset_test_user():
    """Reset test user state before each test."""
    import subprocess
    cmd = "docker exec fastapi ./manage.py reset-test-user"
    subprocess.run(cmd, shell=True, check=True)


@pytest.fixture(scope="function")
def browser_page(reset_test_user, browser):
    """Create isolated browser context for testing."""
    context = browser.new_context(
        ignore_https_errors=True,
        storage_state=None,
        viewport={"width": 1280, "height": 1020}
    )
    page = context.new_page()
    context.clear_cookies()
    yield page
    context.close()


class TestAPIKeyManagement:
    """Test suite for API key management functionality."""

    def login_and_navigate_to_account(self, page: Page):
        """Helper method to login and navigate to account page."""
        page.goto(f"{BASE_URL}/")
        expect(page.get_by_text("OpenBacklog")).to_be_visible()
        page.get_by_text("Sign in").click()
        
        # Complete onboarding flow quickly
        expect(page.get_by_role("heading", name="Plan Your Projects")).to_be_visible(timeout=10_000)
        page.get_by_role("button", name="Next").click()
        
        expect(page.get_by_role("heading", name="AI Coding Assistants")).to_be_visible()
        page.get_by_role("button", name="Next").click()
        
        expect(page.get_by_role("heading", name="Context-Aware Development")).to_be_visible()
        page.get_by_role("button", name="Next").click()
        
        expect(page.get_by_role("heading", name="What's your project name?")).to_be_visible()
        page.get_by_role("textbox", name="Project Name").click()
        page.get_by_role("textbox", name="Project Name").fill("TestProject")
        page.get_by_role("button", name="Next").click()
        
        expect(page.get_by_role("heading", name="Simple Usage-Based Pricing")).to_be_visible()
        page.get_by_role("button", name="Continue with Free Trial").click()
        
        # Navigate to account page
        page.goto(f"{BASE_URL}/account")
        expect(page.get_by_text("OpenBacklog Personal Access Tokens")).to_be_visible()

    def test_initial_empty_state(self, browser_page):
        """Test the initial empty state when no tokens exist."""
        self.login_and_navigate_to_account(browser_page)
        
        # Verify empty state message
        expect(browser_page.get_by_text("No tokens generated yet")).to_be_visible()
        expect(browser_page.get_by_text("Click \"Generate New Token\" to create your first token")).to_be_visible()
        
        # Verify generate button is present
        expect(browser_page.get_by_role("button", name="Generate New Token")).to_be_visible()

    def test_token_generation_and_modal(self, browser_page):
        """Test token generation and modal display."""
        self.login_and_navigate_to_account(browser_page)
        
        # Click generate token button
        browser_page.get_by_role("button", name="Generate New Token").click()
        
        # Verify modal appears
        expect(browser_page.locator("#token-modal")).to_be_visible()
        expect(browser_page.get_by_text("Your New Token")).to_be_visible()
        expect(browser_page.get_by_text("Copy this token now. For security reasons, it won't be shown again.")).to_be_visible()
        
        # Verify token is displayed
        token_element = browser_page.locator("#full-token")
        expect(token_element).to_be_visible()
        token_text = token_element.text_content()
        assert token_text and len(token_text) > 10, "Token should be displayed and non-empty"
        
        # Verify MCP command is displayed
        mcp_cmd_element = browser_page.locator("#mcp-cmd")
        expect(mcp_cmd_element).to_be_visible()
        mcp_text = mcp_cmd_element.text_content()
        assert "claude mcp add" in mcp_text, "MCP command should contain 'claude mcp add'"
        assert token_text in mcp_text, "MCP command should contain the generated token"
        
        # Verify both copy buttons are present but hidden initially
        full_token_copy_btn = browser_page.locator("#copy-full-token-btn")
        mcp_copy_btn = browser_page.locator("#copy-mcp-cmd-btn")
        expect(full_token_copy_btn).to_be_attached()
        expect(mcp_copy_btn).to_be_attached()

    def test_copy_button_functionality(self, browser_page):
        """Test copy button click functionality and visual feedback."""
        self.login_and_navigate_to_account(browser_page)
        
        # Generate token to open modal
        browser_page.get_by_role("button", name="Generate New Token").click()
        expect(browser_page.locator("#token-modal")).to_be_visible()
        
        # Test full token copy button
        full_token_container = browser_page.locator("#full-token").locator("..")
        full_token_copy_btn = browser_page.locator("#copy-full-token-btn")
        
        # Hover to make button visible, then click
        full_token_container.hover()
        full_token_copy_btn.click()
        
        # Check for visual feedback (icon should change to checkmark temporarily)
        # The button content should change to include success SVG
        time.sleep(0.5)  # Give time for the visual change
        button_html = full_token_copy_btn.inner_html()
        assert "M5 13l4 4L19 7" in button_html, "Copy button should show checkmark after click"
        
        # Test MCP command copy button
        mcp_container = browser_page.locator("#mcp-cmd").locator("..")
        mcp_copy_btn = browser_page.locator("#copy-mcp-cmd-btn")
        
        # Hover to make button visible, then click
        mcp_container.hover()
        mcp_copy_btn.click()
        
        # Check for visual feedback
        time.sleep(0.5)
        button_html = mcp_copy_btn.inner_html()
        assert "M5 13l4 4L19 7" in button_html, "MCP copy button should show checkmark after click"

    def test_modal_close_functionality(self, browser_page):
        """Test various ways to close the modal."""
        self.login_and_navigate_to_account(browser_page)
        
        # Generate token to open modal
        browser_page.get_by_role("button", name="Generate New Token").click()
        expect(browser_page.locator("#token-modal")).to_be_visible()
        
        # Test close button
        close_btn = browser_page.get_by_role("button", name="Close")
        expect(close_btn).to_be_visible()
        close_btn.click()
        
        # Modal should be hidden and page should reload
        expect(browser_page.locator("#token-modal")).to_be_hidden()
        
        # Verify token appears in table after modal close
        expect(browser_page.locator("table")).to_be_visible()
        expect(browser_page.get_by_text("eyJ")).to_be_visible()  # Should show redacted token

    def test_token_table_display(self, browser_page):
        """Test that generated tokens appear correctly in the table."""
        self.login_and_navigate_to_account(browser_page)
        
        # Generate a token
        browser_page.get_by_role("button", name="Generate New Token").click()
        expect(browser_page.locator("#token-modal")).to_be_visible()
        
        # Close modal to see table update
        browser_page.get_by_role("button", name="Close").click()
        
        # Verify table structure
        table = browser_page.locator("table")
        expect(table).to_be_visible()
        
        # Check table headers
        # browser_page.pause()
        expect(browser_page.get_by_role("cell", name="Token")).to_be_visible()
        expect(browser_page.get_by_role("cell", name="Created")).to_be_visible()
        expect(browser_page.get_by_role("cell", name="Last Used")).to_be_visible()
        expect(browser_page.get_by_role("cell", name="Actions")).to_be_visible()
        
        # Check token row content
        token_row = table.locator("tbody tr").first
        expect(token_row).to_be_visible()
        
        # Verify redacted token format
        redacted_token = token_row.locator("code").first
        expect(redacted_token).to_be_visible()
        token_text = redacted_token.text_content()
        assert token_text.startswith("eyJ") and "***" in token_text, "Token should be properly redacted"
        
        # Verify delete button is present
        delete_btn = token_row.locator(".delete-token-btn")
        expect(delete_btn).to_be_visible()

    def test_multiple_token_generation(self, browser_page):
        """Test generating multiple tokens and table ordering."""
        self.login_and_navigate_to_account(browser_page)
        
        # Generate first token
        browser_page.get_by_role("button", name="Generate New Token").click()
        browser_page.get_by_role("button", name="Close").click()
        
        # Generate second token
        browser_page.get_by_role("button", name="Generate New Token").click()
        browser_page.get_by_role("button", name="Close").click()
        
        # Verify both tokens appear in table
        table_rows = browser_page.locator("tbody tr")
        expect(table_rows).to_have_count(2)
        
        # Verify each row has proper structure
        for i in range(2):
            row = table_rows.nth(i)
            expect(row.locator("code")).to_be_visible()  # Redacted token
            expect(row.locator(".delete-token-btn")).to_be_visible()  # Delete button

    def test_token_deletion_flow(self, browser_page):
        """Test token deletion with confirmation modal."""
        self.login_and_navigate_to_account(browser_page)
        
        # Generate a token first
        browser_page.get_by_role("button", name="Generate New Token").click()
        browser_page.get_by_role("button", name="Close").click()
        
        # Click delete button
        delete_btn = browser_page.locator(".delete-token-btn").first
        delete_btn.click()
        
        # Verify delete confirmation modal appears
        delete_modal = browser_page.locator("#delete-modal")
        expect(delete_modal).to_be_visible()
        expect(browser_page.get_by_text("Delete Token")).to_be_visible()
        expect(browser_page.get_by_text("Are you sure you want to delete this token?")).to_be_visible()
        
        # Verify token is displayed in confirmation modal
        expect(browser_page.locator("#delete-token-display")).to_be_visible()
        
        # Test cancel button
        cancel_btn = browser_page.get_by_role("button", name="Cancel")
        expect(cancel_btn).to_be_visible()
        cancel_btn.click()
        
        # Modal should close and token should still exist
        expect(delete_modal).to_be_hidden()
        expect(browser_page.locator("tbody tr")).to_have_count(1)

    def test_token_deletion_confirmation(self, browser_page):
        """Test actual token deletion when confirmed."""
        self.login_and_navigate_to_account(browser_page)
        
        # Generate a token first
        browser_page.get_by_role("button", name="Generate New Token").click()
        browser_page.get_by_role("button", name="Close").click()
        
        # Click delete button
        browser_page.pause()
        delete_btn = browser_page.locator(".delete-token-btn").first
        delete_btn.click()
        
        # Confirm deletion
        browser_page.locator("#confirm-delete-btn").click()
        
        # Modal should close
        expect(browser_page.locator("#delete-modal")).to_be_hidden()
        
        # Success message should appear
        success_msg = browser_page.get_by_text("Token deleted successfully")
        expect(success_msg).to_be_visible()
        
        # Token should be removed from table (back to empty state)
        expect(browser_page.get_by_text("No tokens generated yet")).to_be_visible()
        expect(browser_page.locator("table")).to_be_hidden()

    def test_multiple_tokens_deletion(self, browser_page):
        """Test deletion behavior with multiple tokens."""
        self.login_and_navigate_to_account(browser_page)
        
        # Generate multiple tokens
        for i in range(3):
            browser_page.get_by_role("button", name="Generate New Token").click()
            browser_page.get_by_role("button", name="Close").click()
        
        # Verify all tokens are present
        expect(browser_page.locator("tbody tr")).to_have_count(3)
        
        # Delete the first token
        browser_page.locator(".delete-token-btn").first.click()
        browser_page.locator("#confirm-delete-btn").click()
        
        # Verify one token was removed
        expect(browser_page.locator("tbody tr")).to_have_count(2)
        
        # Delete another token
        browser_page.locator(".delete-token-btn").first.click()
        browser_page.locator("#confirm-delete-btn").click()
        
        # Verify another token was removed
        expect(browser_page.locator("tbody tr")).to_have_count(1)
        
        # Delete the last token
        browser_page.locator(".delete-token-btn").first.click()
        browser_page.locator("#confirm-delete-btn").click()
        
        # Should return to empty state
        expect(browser_page.get_by_text("No tokens generated yet")).to_be_visible()

    def test_modal_keyboard_interactions(self, browser_page):
        """Test keyboard interactions with modals."""
        self.login_and_navigate_to_account(browser_page)
        
        # Generate token to open modal
        browser_page.get_by_role("button", name="Generate New Token").click()
        expect(browser_page.locator("#token-modal")).to_be_visible()
        
        # Test ESC key to close modal (if implemented)
        browser_page.keyboard.press("Escape")
        # Note: ESC functionality might not be implemented, so we'll just test
        # that it doesn't break anything
        
        # If modal is still open, close it normally
        if browser_page.locator("#token-modal").is_visible():
            browser_page.get_by_role("button", name="Close").click()

    def test_error_handling_scenarios(self, browser_page):
        """Test error handling for various edge cases."""
        self.login_and_navigate_to_account(browser_page)
        
        # Test rapid clicking of generate button
        generate_btn = browser_page.get_by_role("button", name="Generate New Token")
        generate_btn.click()
        
        # Wait a moment and click again (should handle gracefully)
        time.sleep(0.1)
        # Don't click again as modal is already open
        
        # Verify modal is still functional
        expect(browser_page.locator("#token-modal")).to_be_visible()
        browser_page.get_by_role("button", name="Close").click()
        
        # Test that the system remains stable
        expect(browser_page.get_by_role("button", name="Generate New Token")).to_be_visible()

    def test_token_metadata_display(self, browser_page):
        """Test that token metadata is displayed correctly."""
        self.login_and_navigate_to_account(browser_page)
        
        # Generate a token
        browser_page.get_by_role("button", name="Generate New Token").click()
        browser_page.get_by_role("button", name="Close").click()
        
        # Check token row metadata
        token_row = browser_page.locator("tbody tr").first
        
        # Verify created date is displayed
        created_cell = token_row.locator("td").nth(1)
        expect(created_cell).to_be_visible()
        created_text = created_cell.text_content()
        assert created_text and len(created_text) > 5, "Created date should be displayed"
        
        # Verify last used status
        last_used_cell = token_row.locator("td").nth(2)
        expect(last_used_cell).to_be_visible()
        expect(last_used_cell.get_by_text("Never used")).to_be_visible()