from django.contrib.auth.backends import BaseBackend
from rest_framework_simplejwt.backends import TokenBackend as SimpleJWTTokenBackend
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from models import WooclapUser


class TokenBackend(BaseBackend):
    def authenticate(self, request, token=None, **kwargs):
        if token is None:
            return None

        simplejwt_backend = SimpleJWTTokenBackend()
        try:
            payload = simplejwt_backend.decode(token, request)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        user_id = payload.get('user_id')

        try:
            user = WooclapUser.objects.get(pk=user_id)
        except WooclapUser.DoesNotExist:
            raise InvalidToken('User not found.')

        return user

    def get_user(self, user_id):
        try:
            return WooclapUser.objects.get(pk=user_id)
        except WooclapUser.DoesNotExist:
            return None