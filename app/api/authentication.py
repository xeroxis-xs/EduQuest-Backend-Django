import jwt
import requests
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from django.contrib.auth.models import User


class CustomJWTAuthentication(JWTAuthentication):

    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return self.session_authenticate(request)

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return self.session_authenticate(request)

        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_or_create_user(validated_token)
            return user, validated_token
        except AuthenticationFailed as e:
            print(f"Authentication failed: {str(e)}")
            raise e
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise AuthenticationFailed(f"Unexpected error: {str(e)}")

    def get_validated_token(self, raw_token):
        try:
            # Decode the token without verification to get the payload
            unverified_header = jwt.get_unverified_header(raw_token)
            unverified_payload = jwt.decode(raw_token, options={"verify_signature": False})

            issuer = unverified_payload.get('iss')
            tenant_id = unverified_payload.get('tid')

            # Fetch the public keys from the Azure AD endpoint
            jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
            response = requests.get(jwks_url)
            if response.status_code != 200:
                raise AuthenticationFailed('Failed to fetch public keys from Azure AD.')

            # The keys are used to verify the token signature
            keys = response.json().get('keys')
            key = next(k for k in keys if k['kid'] == unverified_header['kid'])
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)

            # Validate the token using the public key
            decoded_token = jwt.decode(raw_token, key=public_key, algorithms=["RS256"], audience=settings.AZURE_CLIENT_ID)
            return decoded_token
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired, please authenticate again.')
        except jwt.InvalidAudienceError:
            print("Invalid audience")
            raise AuthenticationFailed('Invalid audience.')
        except jwt.DecodeError:
            print("Error decoding token")
            raise AuthenticationFailed('Error decoding token.')
        except jwt.PyJWTError as e:
            raise AuthenticationFailed(f'Token is invalid: {str(e)}')

    def get_or_create_user(self, validated_token):
        try:
            email = validated_token.get('preferred_username')
            username = validated_token.get('name', '')
            first_name = validated_token.get('name', '')
            last_name = validated_token.get('name', '')

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'email': email,
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )
            # print(user)

            if created:
                # print("New user created")
                # Here you can add any additional setup for the new user
                pass

            return user
        except Exception as e:
            print(f'Failed to get or create user: {str(e)}')
            raise AuthenticationFailed(f'Failed to get or create user: {str(e)}')

    def session_authenticate(self, request):
        session_authenticator = SessionAuthentication()
        try:
            return session_authenticator.authenticate(request)
        except AuthenticationFailed as e:
            return None
        except Exception as e:
            return None
