from django.urls import path

from . import views

urlpatterns = [
    path('brands/', views.BrandListView.as_view(), name='brand-list'),
    path(
        'brands/<int:pk>/',
        views.BrandDetailView.as_view(),
        name='brand-detail',
    ),
    path(
        'brands/<int:pk>/cars/',
        views.BrandCarsView.as_view(),
        name='brand-cars',
    ),
    path('cars/', views.CarListView.as_view(), name='car-list'),
    path('cars/<int:pk>/', views.CarDetailView.as_view(), name='car-detail'),
]
