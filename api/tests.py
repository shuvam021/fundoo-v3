from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.core.cache import cache
from django_fakeredis.fakeredis import FakeRedis

from api.models import User

# user_details = {"username": "user1", "email": "user@email.com", "password": "password"}
# superuser_details = {"username": "sups", "email": "admin@email.com", "password": "password"}

ENDPOINT_USER_LIST = reverse('users-list')
ENDPOINT_NOTE_LIST = reverse('notes-list')
ENDPOINT_LABEL_LIST = reverse('labels-list')
ENDPOINT_LOGIN = reverse('login')


def create_user(**params):
    return User.objects.create_user(**params)


def create_superuser(**params):
    return User.objects.create_superuser(**params)


class TestUserAccessibleApiView(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    @staticmethod
    def remove_cache(user_id):
        if cache.get(user_id):
            cache.delete(user_id)

    def test_end_points_are_accessible_by_appropriate_user(self):
        """
        Test urls accessible by Regular, Super. and Anonymous users
        """
        regular_user_details = {"username": "user1", "email": "user@email.com", "password": "password"}
        superuser_details = {"username": "sups", "email": "admin@email.com", "password": "password"}

        anonymous_client = APIClient()

        reg_user = create_user(**regular_user_details)
        reg_client = APIClient()
        res = reg_client.post(ENDPOINT_LOGIN, {"email": "user@email.com", "password": "password"})
        reg_client.credentials(HTTP_AUTHORIZATION='Bearer ' + res.data['access'])

        super_user = create_superuser(**superuser_details)
        super_client = APIClient()
        res = super_client.post(ENDPOINT_LOGIN, superuser_details)
        super_client.credentials(HTTP_AUTHORIZATION='Bearer ' + res.data['access'])

        # Super User
        res = super_client.get(ENDPOINT_USER_LIST)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Regular User
        res = reg_client.get(ENDPOINT_USER_LIST)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # # Anonymous User
        res = anonymous_client.get(ENDPOINT_USER_LIST)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    @FakeRedis("redis://127.0.0.1:6379/")
    def test_notes_api_crud_operation(self):
        """
        Test Get, Post, Put, Delete operations working condition
        """
        user_details = {"username": "user1", "email": "user@email.com", "password": "password"}
        user = create_user(**user_details)

        login_res = self.client.post(ENDPOINT_LOGIN, {"email": "user@email.com", "password": "password"})
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + login_res.data['access'])
        self.remove_cache(user.id)

        # Get Response list()
        get_res = self.client.get(ENDPOINT_NOTE_LIST, format='json')
        self.assertEqual(get_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(get_res.data['data']), 0)

        # Post Response create()
        payload = {'title': "test note 001", "description": "test description 001"}
        response = self.client.post(ENDPOINT_NOTE_LIST, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payload['title'], response.data['data']['title'])
        self.assertEqual(payload['description'], response.data['data']['description'])
        self.remove_cache(user.id)
