# tests/e2e/test_e2e.py

import os
from uuid import uuid4

import pytest
from playwright.sync_api import Page, expect


BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


def unique_user() -> dict[str, str]:
    """Create unique registration data so repeated test runs do not conflict."""
    unique_id = uuid4().hex[:10]

    return {
        "first_name": "Playwright",
        "last_name": "Tester",
        "username": f"user_{unique_id}",
        "email": f"user_{unique_id}@example.com",
        "password": "Password123",
    }


def register_user_through_ui(page: Page, user: dict[str, str]) -> None:
    """Register a user through the browser registration form."""
    page.goto(f"{BASE_URL}/register")

    page.fill("#first-name", user["first_name"])
    page.fill("#last-name", user["last_name"])
    page.fill("#username", user["username"])
    page.fill("#email", user["email"])
    page.fill("#password", user["password"])
    page.fill("#confirm-password", user["password"])

    page.click("#register-button")

    expect(page.locator("#message")).to_contain_text(
        "Registration successful"
    )


@pytest.mark.e2e
def test_successful_registration(page: Page):
    """A user can register with valid information."""
    user = unique_user()

    register_user_through_ui(page, user)

    expect(page.locator("#message")).to_have_class(
        "message success"
    )


@pytest.mark.e2e
def test_registration_rejects_short_password(page: Page):
    """Client-side validation rejects a password shorter than six characters."""
    user = unique_user()

    page.goto(f"{BASE_URL}/register")

    page.fill("#first-name", user["first_name"])
    page.fill("#last-name", user["last_name"])
    page.fill("#username", user["username"])
    page.fill("#email", user["email"])
    page.fill("#password", "Ab1")
    page.fill("#confirm-password", "Ab1")

    page.click("#register-button")

    expect(page.locator("#message")).to_contain_text(
        "Password must be at least 6 characters long"
    )

    expect(page.locator("#message")).to_have_class(
        "message error"
    )


@pytest.mark.e2e
def test_successful_login_stores_jwt(page: Page):
    """A registered user can log in and the JWT is stored locally."""
    user = unique_user()

    register_user_through_ui(page, user)

    page.goto(f"{BASE_URL}/login")

    page.fill("#username", user["username"])
    page.fill("#password", user["password"])
    page.click("#login-button")

    expect(page.locator("#message")).to_contain_text(
        "Login successful"
    )

    access_token = page.evaluate(
        "() => localStorage.getItem('access_token')"
    )

    assert access_token is not None
    assert len(access_token) > 0


@pytest.mark.e2e
def test_login_rejects_wrong_password(page: Page):
    """The UI displays an error when a user enters the wrong password."""
    user = unique_user()

    register_user_through_ui(page, user)

    page.goto(f"{BASE_URL}/login")

    page.fill("#username", user["username"])
    page.fill("#password", "WrongPassword123")
    page.click("#login-button")

    expect(page.locator("#message")).to_contain_text(
        "Invalid username or password"
    )

    expect(page.locator("#message")).to_have_class(
        "message error"
    )

    access_token = page.evaluate(
        "() => localStorage.getItem('access_token')"
    )

    assert access_token is None