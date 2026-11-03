from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Brand, Car


class CatalogAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.toyota = Brand.objects.create(name='Toyota', country='Японія')
        cls.bmw = Brand.objects.create(name='BMW', country='Німеччина')
        cls.empty_brand = Brand.objects.create(name='Audi')
        cls.camry = Car.objects.create(
            brand=cls.toyota,
            model='Camry',
            year=2021,
            price=Decimal('24500'),
            body_type=Car.BodyType.SEDAN,
            fuel_type=Car.FuelType.PETROL,
            mileage=45000,
        )
        cls.rav4 = Car.objects.create(
            brand=cls.toyota,
            model='RAV4',
            year=2022,
            price=Decimal('31000'),
            body_type=Car.BodyType.SUV,
            fuel_type=Car.FuelType.HYBRID,
            mileage=28000,
        )
        cls.x5 = Car.objects.create(
            brand=cls.bmw,
            model='X5',
            year=2020,
            price=Decimal('52000'),
            body_type=Car.BodyType.SUV,
            fuel_type=Car.FuelType.DIESEL,
            mileage=67000,
        )

    def assert_error_format(self, response, expected_status):
        self.assertEqual(response.status_code, expected_status)
        self.assertIn('error', response.data)
        self.assertIsInstance(response.data['error'], str)


class BrandAPITests(CatalogAPITestCase):
    def test_list_brands_with_cars_count(self):
        response = self.client.get(reverse('brand-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        counts = {item['name']: item['carsCount'] for item in response.data}
        self.assertEqual(counts, {'Audi': 0, 'BMW': 1, 'Toyota': 2})

    def test_create_brand(self):
        payload = {'name': 'Honda', 'country': 'Японія'}
        response = self.client.post(
            reverse('brand-list'), payload, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Honda')
        self.assertEqual(response.data['carsCount'], 0)

    def test_create_brand_validation_error(self):
        response = self.client.post(reverse('brand-list'), {}, format='json')
        self.assert_error_format(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data['details'])

    def test_create_duplicate_brand_case_insensitive(self):
        response = self.client.post(
            reverse('brand-list'), {'name': 'toyota'}, format='json'
        )
        self.assert_error_format(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data['details'])

    def test_retrieve_brand_not_found(self):
        response = self.client.get(reverse('brand-detail', args=[999]))
        self.assert_error_format(response, status.HTTP_404_NOT_FOUND)

    def test_put_requires_all_fields(self):
        url = reverse('brand-detail', args=[self.bmw.pk])
        response = self.client.put(url, {'country': 'DE'}, format='json')
        self.assert_error_format(response, status.HTTP_400_BAD_REQUEST)

    def test_patch_brand(self):
        url = reverse('brand-detail', args=[self.bmw.pk])
        response = self.client.patch(
            url, {'description': 'Оновлений опис'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Оновлений опис')
        self.assertEqual(response.data['name'], 'BMW')

    def test_delete_brand_with_cars_returns_conflict(self):
        url = reverse('brand-detail', args=[self.toyota.pk])
        response = self.client.delete(url)
        self.assert_error_format(response, status.HTTP_409_CONFLICT)
        self.assertTrue(Brand.objects.filter(pk=self.toyota.pk).exists())

    def test_delete_brand_without_cars(self):
        url = reverse('brand-detail', args=[self.empty_brand.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Brand.objects.filter(pk=self.empty_brand.pk).exists()
        )

    def test_brand_cars(self):
        url = reverse('brand-cars', args=[self.toyota.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class CarAPITests(CatalogAPITestCase):
    def test_list_cars_with_pagination(self):
        response = self.client.get(reverse('car-list'), {'limit': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)
        self.assertEqual(
            response.data['pagination'],
            {'totalItems': 3, 'currentPage': 1, 'totalPages': 2},
        )

    def test_filter_by_search(self):
        response = self.client.get(reverse('car-list'), {'search': 'cam'})
        models = [car['model'] for car in response.data['data']]
        self.assertEqual(models, ['Camry'])

    def test_filter_by_brand_and_fuel(self):
        response = self.client.get(
            reverse('car-list'),
            {'brandId': self.toyota.pk, 'fuelType': 'hybrid'},
        )
        models = [car['model'] for car in response.data['data']]
        self.assertEqual(models, ['RAV4'])

    def test_sort_by_price_desc(self):
        response = self.client.get(reverse('car-list'), {'sort': 'price_desc'})
        prices = [car['price'] for car in response.data['data']]
        self.assertEqual(prices, sorted(prices, reverse=True))

    def test_invalid_query_params(self):
        response = self.client.get(
            reverse('car-list'), {'sort': 'wrong', 'fuelType': 'coal'}
        )
        self.assert_error_format(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('sort', response.data['details'])
        self.assertIn('fuelType', response.data['details'])

    def test_create_car(self):
        payload = {
            'brandId': self.bmw.pk,
            'model': '320i',
            'year': 2019,
            'price': 27800,
            'bodyType': 'sedan',
            'fuelType': 'petrol',
            'transmission': 'automatic',
            'mileage': 82000,
        }
        response = self.client.post(
            reverse('car-list'), payload, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data['brand'], {'id': self.bmw.pk, 'name': 'BMW'}
        )
        self.assertEqual(response.data['bodyType'], 'sedan')

    def test_create_car_validation_error(self):
        payload = {
            'brandId': 999,
            'model': '',
            'year': 1500,
            'price': -1,
            'fuelType': 'coal',
        }
        response = self.client.post(
            reverse('car-list'), payload, format='json'
        )
        self.assert_error_format(response, status.HTTP_400_BAD_REQUEST)
        for field in ('brandId', 'model', 'year', 'price', 'fuelType',
                      'mileage'):
            self.assertIn(field, response.data['details'])

    def test_retrieve_car_not_found(self):
        response = self.client.get(reverse('car-detail', args=[999]))
        self.assert_error_format(response, status.HTTP_404_NOT_FOUND)

    def test_patch_car(self):
        url = reverse('car-detail', args=[self.camry.pk])
        response = self.client.patch(
            url, {'price': 23900, 'mileage': 46000}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['price'], 23900)
        self.assertEqual(response.data['mileage'], 46000)

    def test_put_car(self):
        url = reverse('car-detail', args=[self.x5.pk])
        payload = {
            'brandId': self.bmw.pk,
            'model': 'X5 xDrive30d',
            'year': 2020,
            'price': 49900,
            'mileage': 68000,
        }
        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['model'], 'X5 xDrive30d')

    def test_delete_car(self):
        url = reverse('car-detail', args=[self.rav4.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Car.objects.filter(pk=self.rav4.pk).exists())

    def test_malformed_json(self):
        response = self.client.post(
            reverse('car-list'),
            data='{"model": ',
            content_type='application/json',
        )
        self.assert_error_format(response, status.HTTP_400_BAD_REQUEST)

    def test_cors_header_for_frontend_origin(self):
        response = self.client.get(
            reverse('car-list'), HTTP_ORIGIN='http://127.0.0.1:5500'
        )
        self.assertEqual(
            response.headers['Access-Control-Allow-Origin'],
            'http://127.0.0.1:5500',
        )

    def test_cors_preflight_for_frontend_origin(self):
        response = self.client.options(
            reverse('car-list'),
            HTTP_ORIGIN='http://localhost:5500',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS='content-type',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.headers['Access-Control-Allow-Origin'],
            'http://localhost:5500',
        )

    def test_cors_rejects_foreign_origin(self):
        response = self.client.get(
            reverse('car-list'), HTTP_ORIGIN='http://evil.example'
        )
        self.assertNotIn('Access-Control-Allow-Origin', response.headers)


class ErrorFormatTests(APITestCase):
    def test_unknown_url_returns_json_error(self):
        response = self.client.get('/api/v1/unknown/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertIn('error', response.json())

    def test_method_not_allowed_uses_unified_format(self):
        response = self.client.delete(reverse('car-list'))
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )
        self.assertIn('error', response.data)
