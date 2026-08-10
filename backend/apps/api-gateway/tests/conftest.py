import pytest
import os

@pytest.fixture
def test_password():
    return os.environ.get("TEST_PASSWORD", "TestPassword123!")

@pytest.fixture
def test_email():
    return os.environ.get("TEST_EMAIL", "testuser@example.com")

@pytest.fixture
def test_credentials(test_email, test_password):
    return {"email": test_email, "password": test_password}
