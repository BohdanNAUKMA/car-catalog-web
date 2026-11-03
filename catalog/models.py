from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Count

MIN_CAR_YEAR = 1886


class BrandQuerySet(models.QuerySet):
    def with_cars_count(self):
        return self.annotate(cars_count=Count('cars'))


class Brand(models.Model):
    name = models.CharField(
        'назва',
        max_length=100,
        unique=True,
        error_messages={'unique': 'Бренд з такою назвою вже існує.'},
    )
    country = models.CharField('країна', max_length=100, blank=True)
    description = models.TextField('опис', blank=True)

    objects = BrandQuerySet.as_manager()

    class Meta:
        db_table = 'brands'
        ordering = ['name']
        verbose_name = 'бренд'
        verbose_name_plural = 'бренди'

    def __str__(self):
        return self.name


class Car(models.Model):
    class BodyType(models.TextChoices):
        SEDAN = 'sedan', 'Седан'
        SUV = 'suv', 'Кросовер / позашляховик'
        HATCHBACK = 'hatchback', 'Хетчбек'
        WAGON = 'wagon', 'Універсал'
        COUPE = 'coupe', 'Купе'
        CONVERTIBLE = 'convertible', 'Кабріолет'
        MINIVAN = 'minivan', 'Мінівен'
        PICKUP = 'pickup', 'Пікап'

    class FuelType(models.TextChoices):
        PETROL = 'petrol', 'Бензин'
        DIESEL = 'diesel', 'Дизель'
        ELECTRIC = 'electric', 'Електро'
        HYBRID = 'hybrid', 'Гібрид'

    class Transmission(models.TextChoices):
        MANUAL = 'manual', 'Механічна'
        AUTOMATIC = 'automatic', 'Автоматична'
        ROBOTIC = 'robotic', 'Роботизована'
        CVT = 'cvt', 'Варіатор'

    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name='cars',
        verbose_name='бренд',
    )
    model = models.CharField('модель', max_length=100)
    year = models.PositiveSmallIntegerField(
        'рік випуску',
        validators=[MinValueValidator(MIN_CAR_YEAR)],
    )
    price = models.DecimalField(
        'ціна',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
    )
    body_type = models.CharField(
        'тип кузова', max_length=20, choices=BodyType.choices, blank=True
    )
    fuel_type = models.CharField(
        'тип палива', max_length=20, choices=FuelType.choices, blank=True
    )
    transmission = models.CharField(
        'коробка передач',
        max_length=20,
        choices=Transmission.choices,
        blank=True,
    )
    mileage = models.PositiveIntegerField('пробіг, км')
    description = models.TextField('опис', blank=True)
    image_url = models.URLField(
        'посилання на фото', max_length=500, blank=True
    )
    created_at = models.DateTimeField('створено', auto_now_add=True)

    class Meta:
        db_table = 'cars'
        ordering = ['-created_at', '-id']
        verbose_name = 'автомобіль'
        verbose_name_plural = 'автомобілі'

    def __str__(self):
        return f'{self.brand.name} {self.model} ({self.year})'
