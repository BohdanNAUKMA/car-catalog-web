from django.utils import timezone
from rest_framework import serializers

from .models import Brand, Car


class BrandSerializer(serializers.ModelSerializer):
    carsCount = serializers.SerializerMethodField(method_name='get_cars_count')

    class Meta:
        model = Brand
        fields = ['id', 'name', 'country', 'description', 'carsCount']

    def get_cars_count(self, obj):
        cars_count = getattr(obj, 'cars_count', None)
        if cars_count is None:
            cars_count = obj.cars.count()
        return cars_count

    def validate_name(self, value):
        duplicates = Brand.objects.filter(name__iexact=value)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError(
                'Бренд з такою назвою вже існує.'
            )
        return value


class BrandShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name']


class CarSerializer(serializers.ModelSerializer):
    brand = BrandShortSerializer(read_only=True)
    brandId = serializers.PrimaryKeyRelatedField(
        source='brand',
        queryset=Brand.objects.all(),
        error_messages={
            'required': "Поле brandId є обов'язковим.",
            'does_not_exist': 'Бренд з id={pk_value} не існує.',
            'incorrect_type': 'Очікується числовий id бренду.',
        },
    )
    bodyType = serializers.ChoiceField(
        source='body_type',
        choices=Car.BodyType.choices,
        required=False,
        allow_blank=True,
    )
    fuelType = serializers.ChoiceField(
        source='fuel_type',
        choices=Car.FuelType.choices,
        required=False,
        allow_blank=True,
    )
    imageUrl = serializers.URLField(
        source='image_url',
        max_length=500,
        required=False,
        allow_blank=True,
    )
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Car
        fields = [
            'id',
            'brand',
            'brandId',
            'model',
            'year',
            'price',
            'bodyType',
            'fuelType',
            'transmission',
            'mileage',
            'description',
            'imageUrl',
            'createdAt',
        ]

    def validate_year(self, value):
        max_year = timezone.now().year + 1
        if value > max_year:
            raise serializers.ValidationError(
                f'Рік випуску не може бути більшим за {max_year}.'
            )
        return value


class CarListQuerySerializer(serializers.Serializer):
    SORT_CHOICES = [
        'price_asc',
        'price_desc',
        'year_asc',
        'year_desc',
        'mileage_asc',
        'mileage_desc',
        'newest',
    ]
    DEFAULT_LIMIT = 12
    MAX_LIMIT = 100

    search = serializers.CharField(
        required=False, allow_blank=True, max_length=100
    )
    brandId = serializers.IntegerField(required=False, min_value=1)
    bodyType = serializers.ChoiceField(
        choices=Car.BodyType.values, required=False, allow_blank=True
    )
    fuelType = serializers.ChoiceField(
        choices=Car.FuelType.values, required=False, allow_blank=True
    )
    sort = serializers.ChoiceField(
        choices=SORT_CHOICES, required=False, allow_blank=True
    )
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    limit = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=MAX_LIMIT,
        default=DEFAULT_LIMIT,
    )
