# # myapp/middleware.py
# from django.utils.deprecation import MiddlewareMixin
# from django.conf import settings
# from django.contrib.auth import get_user_model
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from rest_framework_simplejwt.tokens import UntypedToken
# from rest_framework.exceptions import AuthenticationFailed
#
# User = get_user_model()
#
# class AzureADAuthenticationMiddleware(MiddlewareMixin):
#
#     def process_request(self, request):
#         # Allow superusers to bypass JWT authentication
#         if request.user.is_authenticated and request.user.is_superuser:
#             return
#
#         auth_header = request.headers.get('Authorization')
#         if auth_header is None:
#             return
#
#         try:
#             # Extract token from the header
#             token_type, token = auth_header.split()
#             if token_type != 'Bearer':
#                 raise AuthenticationFailed('Invalid token header')
#
#             # Validate the token using rest_framework_simplejwt
#             validated_token = UntypedToken(token)
#
#             # Decode the JWT to get user info
#             jwt_auth = JWTAuthentication()
#             # decoded_token = jwt_auth.get_validated_token(token)
#
#             user_info = jwt_auth.get_user(validated_token)
#
#             # Get or create user based on the token info
#             user = self.get_or_create_user(user_info)
#             request.user = user
#
#         except Exception as e:
#             raise AuthenticationFailed(f'Authentication failed: {str(e)}')
#
#     def get_or_create_user(self, user_info):
#         user_id = user_info.id
#         email = user_info.email
#         user, created = User.objects.get_or_create(username=user_id, defaults={'email': email})
#         return user

# import json
# import requests
# from django.conf import settings
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
# from django.utils.deprecation import MiddlewareMixin
# from django.http import JsonResponse
#
# class AzureADTokenAuthenticationMiddleware(MiddlewareMixin):
#
#     def process_request(self, request):
#         auth_header = request.headers.get('Authorization')
#         if auth_header and auth_header.startswith('Bearer '):
#             token = auth_header.split(' ')[1]
#             try:
#                 jwt_auth = JWTAuthentication()
#                 decoded_token = jwt_auth.get_validated_token(token)
#                 validated_token = jwt_auth.get_user(decoded_token)
#                 request.user = validated_token
#             except (InvalidToken, TokenError) as e:
#                 return JsonResponse({'error': str(e)}, status=401)
