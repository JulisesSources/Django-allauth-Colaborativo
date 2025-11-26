from django.urls import path
from . import views

app_name = 'asistencias'

urlpatterns = [
    path('', views.index, name='index'),
]