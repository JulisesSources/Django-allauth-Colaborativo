from django.urls import path
from . import views

app_name = 'trabajadores'

urlpatterns = [
    path('', views.index, name='index'),
]