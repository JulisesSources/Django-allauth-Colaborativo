from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.index, name='index'),
    path('asistencias/', views.reporte_asistencias, name='reporte_asistencias'),
    path('asistencias/exportar/', views.exportar_asistencias_csv, name='exportar_asistencias_csv'),
]