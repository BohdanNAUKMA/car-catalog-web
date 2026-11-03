import math

from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import Conflict, build_error_body
from .models import Brand, Car
from .serializers import BrandSerializer, CarListQuerySerializer, CarSerializer

CAR_SORT_ORDERING = {
    'price_asc': ('price', 'id'),
    'price_desc': ('-price', '-id'),
    'year_asc': ('year', 'id'),
    'year_desc': ('-year', '-id'),
    'mileage_asc': ('mileage', 'id'),
    'mileage_desc': ('-mileage', '-id'),
    'newest': ('-created_at', '-id'),
}


def get_brand_or_404(pk):
    try:
        return Brand.objects.with_cars_count().get(pk=pk)
    except Brand.DoesNotExist:
        raise NotFound(f'Бренд з id={pk} не знайдено.') from None


def get_car_or_404(pk):
    try:
        return Car.objects.select_related('brand').get(pk=pk)
    except Car.DoesNotExist:
        raise NotFound(f'Автомобіль з id={pk} не знайдено.') from None


def filter_cars(queryset, params):
    search = params.get('search', '').strip()
    if search:
        queryset = queryset.filter(model__icontains=search)
    if params.get('brandId'):
        queryset = queryset.filter(brand_id=params['brandId'])
    if params.get('bodyType'):
        queryset = queryset.filter(body_type=params['bodyType'])
    if params.get('fuelType'):
        queryset = queryset.filter(fuel_type=params['fuelType'])
    if params.get('sort'):
        queryset = queryset.order_by(*CAR_SORT_ORDERING[params['sort']])
    return queryset


def paginate(queryset, page, limit):
    total_items = queryset.count()
    total_pages = max(1, math.ceil(total_items / limit))
    offset = (page - 1) * limit
    pagination = {
        'totalItems': total_items,
        'currentPage': page,
        'totalPages': total_pages,
    }
    return queryset[offset:offset + limit], pagination


class BrandListView(APIView):
    def get(self, request):
        brands = Brand.objects.with_cars_count()
        serializer = BrandSerializer(brands, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BrandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BrandDetailView(APIView):
    def get(self, request, pk):
        serializer = BrandSerializer(get_brand_or_404(pk))
        return Response(serializer.data)

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def delete(self, request, pk):
        brand = get_brand_or_404(pk)
        if brand.cars_count:
            raise Conflict(
                f'Неможливо видалити бренд «{brand.name}»: з ним пов\'язано '
                f'автомобілів — {brand.cars_count}. Спочатку видаліть або '
                f'перенесіть ці автомобілі до іншого бренду.'
            )
        brand.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _update(self, request, pk, partial):
        brand = get_brand_or_404(pk)
        serializer = BrandSerializer(brand, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class BrandCarsView(APIView):
    def get(self, request, pk):
        brand = get_brand_or_404(pk)
        cars = brand.cars.select_related('brand')
        serializer = CarSerializer(cars, many=True)
        return Response(serializer.data)


class CarListView(APIView):
    def get(self, request):
        query = CarListQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data

        cars = filter_cars(Car.objects.select_related('brand'), params)
        page_items, pagination = paginate(
            cars, params['page'], params['limit']
        )
        serializer = CarSerializer(page_items, many=True)
        return Response({'data': serializer.data, 'pagination': pagination})

    def post(self, request):
        serializer = CarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CarDetailView(APIView):
    def get(self, request, pk):
        serializer = CarSerializer(get_car_or_404(pk))
        return Response(serializer.data)

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def delete(self, request, pk):
        get_car_or_404(pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _update(self, request, pk, partial):
        car = get_car_or_404(pk)
        serializer = CarSerializer(car, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


def json_page_not_found(request, exception):
    return JsonResponse(
        build_error_body('Запитаний ресурс не знайдено.'),
        status=status.HTTP_404_NOT_FOUND,
        json_dumps_params={'ensure_ascii': False},
    )


def json_server_error(request):
    return JsonResponse(
        build_error_body('Внутрішня помилка сервера.'),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        json_dumps_params={'ensure_ascii': False},
    )
