from django.urls import path
from . import views

app_name = 'cnpj'

urlpatterns = [
    path('', views.home, name='home'),
    path('buscar/', views.buscar, name='buscar'),
    path('empresa/<str:cnpj_basico>/', views.detalhe_empresa, name='detalhe_empresa'),
    path('listar/', views.listar, name='listar'),
]