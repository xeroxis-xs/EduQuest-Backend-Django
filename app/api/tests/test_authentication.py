from django.test import TestCase, RequestFactory
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
import jwt
from datetime import datetime, timedelta
from ..authentication import CustomJWTAuthentication


User = get_user_model()


class CustomJWTAuthenticationTest(TestCase):

    def setUp(self):
        self.auth = CustomJWTAuthentication()
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='#Test User#',
            email='testuser@example.com',
        )

    @patch('api.authentication.jwt.get_unverified_header')
    @patch('api.authentication.jwt.decode')
    @patch('api.authentication.requests.get')
    def test_authenticate_valid_token(self, mock_requests_get, mock_jwt_decode, mock_get_unverified_header):
        """
        Test that a valid token is successfully authenticated.
        """
        token = 'valid.jwt.token'
        mock_get_unverified_header.return_value = {'kid': 'testkid'}

        # Mock JWKS response
        mock_jwks = {
            'keys': [
                {
                    'kid': 'testkid',
                    'kty': 'RSA',
                    'use': 'sig',
                    'n': 'testn',
                    'e': 'AQAB'
                }
            ]
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_jwks
        mock_requests_get.return_value = mock_response

        # Mock decoded token
        payload = {
            'iss': 'https://issuer.example.com',
            'tid': 'tenant123',
            'preferred_username': 'testuser@example.com',
            'name': '#Test User#',
            'iat': datetime.utcnow().timestamp()
        }
        mock_jwt_decode.return_value = payload

        # Mock public key
        with patch('api.authentication.jwt.algorithms.RSAAlgorithm.from_jwk') as mock_from_jwk:
            mock_from_jwk.return_value = MagicMock()

            # Mock get_or_create_user
            with patch.object(self.auth, 'get_or_create_user') as mock_get_or_create_user:
                mock_get_or_create_user.return_value = self.user

                request = self.factory.get('/some-url/', HTTP_AUTHORIZATION=f'Bearer {token}')
                user, validated_token = self.auth.authenticate(request)
                self.assertEqual(user, self.user)
                self.assertEqual(validated_token, payload)

    @patch('api.authentication.jwt.get_unverified_header')
    def test_authenticate_no_token(self, mock_get_unverified_header):
        """
        Test that no token is returned when no Authorization header is provided.
        """
        request = self.factory.get('/some-url/')
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    @patch('api.authentication.jwt.get_unverified_header')
    @patch('api.authentication.jwt.decode')
    @patch('api.authentication.requests.get')
    def test_authenticate_invalid_token(self, mock_get_unverified_header, mock_jwt_decode, mock_requests_get):
        """
        Test that an invalid token raises an AuthenticationFailed exception.
        """
        invalid_token = 'invalid.jwt.token'

        # Simulate an invalid token by raising a DecodeError
        mock_get_unverified_header.side_effect = jwt.DecodeError('Invalid header')

        request = self.factory.get('/some-url/', HTTP_AUTHORIZATION=f'Bearer {invalid_token}')

        # Assert that AuthenticationFailed is raised due to invalid token
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    @patch('api.authentication.jwt.decode')
    def test_authenticate_expired_token(self, mock_jwt_decode):
        """
        Test that an expired token raises an AuthenticationFailed Token Expired exception.
        """
        # Generate an expired token
        expired_time = datetime.utcnow() - timedelta(hours=1)
        expired_token = jwt.encode({'exp': expired_time}, 'secret', algorithm='HS256')

        # Simulate an expired token
        mock_jwt_decode.side_effect = jwt.ExpiredSignatureError('Token expired')

        request = self.factory.get('/some-url/', HTTP_AUTHORIZATION=f'Bearer {expired_token}')

        # Assert that AuthenticationFailed is raised due to expired token
        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)

        # Check that the expected error message is in the exception
        self.assertIn('Token has expired, please authenticate again.', str(context.exception))