from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import update_last_login
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from config.exceptions import Unauthorized

from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    TokenRefreshSerializer,
    UserSerializer,
)

User = get_user_model()

INVALID_CREDENTIALS_MESSAGE = "Невірне ім'я користувача або пароль"
INVALID_REFRESH_MESSAGE = 'Refresh-токен недійсний або прострочений'


class PublicAuthAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]


class RegisterView(PublicAuthAPIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user).data, status=status.HTTP_201_CREATED
        )


class LoginView(PublicAuthAPIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(request, **serializer.validated_data)
        if user is None:
            raise Unauthorized(INVALID_CREDENTIALS_MESSAGE)

        refresh = RefreshToken.for_user(user)
        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        })


class TokenRefreshView(PublicAuthAPIView):
    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh = RefreshToken(serializer.validated_data['refresh'])
        except TokenError:
            raise Unauthorized(INVALID_REFRESH_MESSAGE) from None

        user_id = refresh.payload.get(api_settings.USER_ID_CLAIM)
        user_exists = User.objects.filter(
            **{api_settings.USER_ID_FIELD: user_id, 'is_active': True}
        ).exists()
        if not user_exists:
            raise Unauthorized(INVALID_REFRESH_MESSAGE)

        return Response({'access': str(refresh.access_token)})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def post(self, request):
        return self.get(request)
