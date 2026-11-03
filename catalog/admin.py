from django.contrib import admin

from .models import Brand, Car


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'country')
    search_fields = ('name',)


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'brand', 'model', 'year', 'price', 'fuel_type', 'mileage',
    )
    list_filter = ('brand', 'fuel_type', 'body_type', 'transmission')
    search_fields = ('model', 'brand__name')
    list_select_related = ('brand',)
