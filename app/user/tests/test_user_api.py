from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """ Test the user API (public) """

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """ Test creating user with valid payload is successful """
        payload = {
            'email': 'test@domain.com',
            'password': 'test123',
            'name': 'test name'
        }
        # we making our request
        response = self.client.post(CREATE_USER_URL, payload)
        # we check the "HTTP 201 Created" return
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # We test that the object(user) actually created
        # After creating API returns user data and we get this information
        user = get_user_model().objects.get(**response.data)
        # We test the password is correct
        self.assertTrue(user.check_password(payload['password']))
        # We chech that the password is not returned as part of API return
        self.assertNotIn('password', response.data)

    def test_user_exists(self):
        """ Test creating user that already exists fails """
        payload = {
            'email': 'test@domain.com',
            'password': 'test123',
            'name': 'test name'
        }
        # We create a user
        create_user(**payload)
        # we making our request
        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """ Test that the password must be more than 5 characters """
        payload = {
            'email': 'test@domain.com',
            'password': 'test'
        }

        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """ Test that a token is created for the user """
        payload = {
            'email': 'test@domain.com',
            'password': "test123"
        }
        create_user(**payload)
        response = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """ Test that token is not created if invalid credentials are given """
        payload_true = {
            'email': 'test@domain.com',
            'password': 'test123'
        }
        create_user(**payload_true)
        payload_false = {
            'email': 'test@domain.com',
            'password': 'wrong'
        }
        response = self.client.post(TOKEN_URL, payload_false)

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """ Test that token is not created if user doesn't exists """
        payload = {
            'email': 'test@domain.com',
            'password': 'test123'
        }
        response = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_fields(self):
        """ Test that email and password are required """
        payload = {
            'email': 'one',
            'password': ''
        }
        response = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """" Test that authentication is required for users """
        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """ Test API requests that require authentication """

    def setUp(self):
        self.user = create_user(
            email='test@domain.com',
            password='test123',
            name='test'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """ Test retrieve profile for logged in used """
        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_post_me_not_allowed(self):
        """ Test that POST is not allowed ont the ME url """
        response = self.client.post(ME_URL, {})

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """ Test updating the user profile for authenticated user """
        payload = {
            'name': 'new name',
            'password': 'new123'
        }
        response = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
