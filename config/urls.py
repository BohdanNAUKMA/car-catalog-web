from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('catalog.urls')),
    path('api/v1/auth/', include('users.urls')),
]

handler404 = 'catalog.views.json_page_not_found'
handler500 = 'catalog.views.json_server_error'
