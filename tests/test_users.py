import pytest
from rest_framework.test import APIClient
from users.models import User

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_user(db):
    return User.objects.create_user(username='testuser', password='testpass123')

def test_user_login(api_client, create_user):
    response = api_client.post('/users/token/', {'username': 'testuser', 'password': 'testpass123'})
    assert response.status_code == 200
    assert 'access' in response.data
