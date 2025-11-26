from django.urls import path
from . import views

app_name = 'jornadas_laborales'

urlpatterns = [
    path('', views.index, name='index'),
]