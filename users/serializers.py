from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

User = get_user_model()

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(
        write_only=True,
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        trim_whitespace=False,
        style={'input_type': 'password'},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        max_length=PASSWORD_MAX_LENGTH,
        trim_whitespace=False,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'password_confirm',
        ]
        extra_kwargs = {
            'username': {'validators': [UnicodeUsernameValidator()]},
            'first_name': {'required': False, 'max_length': 150},
            'last_name': {'required': False, 'max_length': 150},
        }

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                'Користувач з таким username вже існує.'
            )
        return value

    def validate_email(self, value):
        value = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                'Користувач з таким email вже існує.'
            )
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {'password_confirm': ['Паролі не збігаються.']}
            )
        candidate = User(
            username=attrs['username'],
            email=attrs['email'],
            first_name=attrs.get('first_name', ''),
            last_name=attrs.get('last_name', ''),
        )
        try:
            validate_password(attrs['password'], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {'password': list(exc.messages)}
            ) from exc
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(
        max_length=PASSWORD_MAX_LENGTH,
        trim_whitespace=False,
        style={'input_type': 'password'},
    )


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()
