from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

User = get_user_model()

PASSWORD = 'StrongPass123!'


class RegisterTests(APITestCase):
    url = reverse('auth-register')

    def valid_payload(self, **overrides):
        payload = {
            'username': 'ivan',
            'email': 'ivan@example.com',
            'first_name': 'Іван',
            'last_name': 'Коваленко',
            'password': PASSWORD,
            'password_confirm': PASSWORD,
        }
        payload.update(overrides)
        return payload

    def assert_validation_error(self, response, *fields):
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Помилка валідації')
        for field in fields:
            self.assertIn(field, response.data['details'])

    def test_register_creates_user_with_hashed_password(self):
        response = self.client.post(
            self.url, self.valid_payload(), format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            set(response.data),
            {'id', 'username', 'email', 'first_name', 'last_name'},
        )
        user = User.objects.get(username='ivan')
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.password.startswith('pbkdf2_'))
        self.assertTrue(user.check_password(PASSWORD))

    def test_register_optional_names(self):
        payload = self.valid_payload()
        del payload['first_name'], payload['last_name']
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['first_name'], '')

    def test_register_requires_mandatory_fields(self):
        response = self.client.post(self.url, {}, format='json')
        self.assert_validation_error(
            response, 'username', 'email', 'password', 'password_confirm'
        )
        self.assertNotIn('first_name', response.data['details'])

    def test_register_invalid_email(self):
        response = self.client.post(
            self.url, self.valid_payload(email='not-an-email'), format='json'
        )
        self.assert_validation_error(response, 'email')

    def test_register_short_password(self):
        response = self.client.post(
            self.url,
            self.valid_payload(password='Ab1!', password_confirm='Ab1!'),
            format='json',
        )
        self.assert_validation_error(response, 'password')

    def test_register_password_mismatch(self):
        response = self.client.post(
            self.url,
            self.valid_payload(password_confirm='OtherPass123!'),
            format='json',
        )
        self.assert_validation_error(response, 'password_confirm')

    def test_register_too_long_fields(self):
        response = self.client.post(
            self.url,
            self.valid_payload(username='u' * 151, first_name='n' * 151),
            format='json',
        )
        self.assert_validation_error(response, 'username', 'first_name')

    def test_register_duplicate_username_and_email(self):
        User.objects.create_user(
            username='Ivan', email='IVAN@example.com', password=PASSWORD
        )
        response = self.client.post(
            self.url, self.valid_payload(), format='json'
        )
        self.assert_validation_error(response, 'username', 'email')
        self.assertEqual(User.objects.count(), 1)


class AuthFlowTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='ivan', email='ivan@example.com', password=PASSWORD
        )

    def login(self, username='ivan', password=PASSWORD):
        return self.client.post(
            reverse('auth-login'),
            {'username': username, 'password': password},
            format='json',
        )


class LoginTests(AuthFlowTestCase):
    def test_login_returns_tokens_and_user(self):
        response = self.login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['user'],
            {
                'id': self.user.pk,
                'username': 'ivan',
                'email': 'ivan@example.com',
                'first_name': '',
                'last_name': '',
            },
        )
        access = AccessToken(response.data['access'])
        refresh = RefreshToken(response.data['refresh'])
        self.assertEqual(
            access[api_settings.USER_ID_CLAIM], str(self.user.pk)
        )
        self.assertEqual(refresh['token_type'], 'refresh')

    def test_token_lifetimes(self):
        self.assertLessEqual(
            api_settings.ACCESS_TOKEN_LIFETIME, timedelta(minutes=30)
        )
        self.assertGreaterEqual(
            api_settings.REFRESH_TOKEN_LIFETIME, timedelta(days=7)
        )

    def test_login_updates_last_login(self):
        self.login()
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_login)

    def test_login_wrong_password(self):
        response = self.login(password='WrongPass123!')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data, {'error': "Невірне ім'я користувача або пароль"}
        )

    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        response = self.login()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_fields(self):
        response = self.client.post(reverse('auth-login'), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data['details'])
        self.assertIn('password', response.data['details'])

    def test_login_ignores_stale_authorization_header(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer broken')
        response = self.login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TokenRefreshTests(AuthFlowTestCase):
    url = reverse('auth-token-refresh')

    def test_refresh_returns_new_working_access_token(self):
        refresh = self.login().data['refresh']
        response = self.client.post(
            self.url, {'refresh': refresh}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), {'access'})

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}'
        )
        me = self.client.get(reverse('auth-me'))
        self.assertEqual(me.status_code, status.HTTP_200_OK)

    def test_refresh_with_invalid_token(self):
        response = self.client.post(
            self.url, {'refresh': 'invalid.token.value'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_refresh_with_access_token_is_rejected(self):
        access = self.login().data['access']
        response = self.client.post(
            self.url, {'refresh': access}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_with_expired_token(self):
        refresh = RefreshToken.for_user(self.user)
        refresh.set_exp(lifetime=-timedelta(seconds=1))
        response = self.client.post(
            self.url, {'refresh': str(refresh)}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_for_deleted_user(self):
        refresh = str(RefreshToken.for_user(self.user))
        self.user.delete()
        response = self.client.post(
            self.url, {'refresh': refresh}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_missing_token(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('refresh', response.data['details'])


class MeTests(AuthFlowTestCase):
    url = reverse('auth-me')

    def test_me_with_valid_token(self):
        access = self.login().data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        for method in ('get', 'post'):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data['username'], 'ivan')
                self.assertNotIn('password', response.data)

    def test_me_without_token(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {'error': 'Потрібна авторизація'})

    def test_me_with_expired_token(self):
        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=-timedelta(seconds=1))
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {'error': 'Потрібна авторизація'})
