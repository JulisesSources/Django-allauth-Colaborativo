# incidencias/urls.py

from django.urls import path
from . import views

app_name = 'incidencias'

urlpatterns = [
    path('', views.index, name='index'),
    # Lista y gestión de incidencias
    path('lista/', views.lista_incidencias, name='lista_incidencias'),
    path('mis-incidencias/', views.mis_incidencias, name='mis_incidencias'),
    path('crear/', views.crear_incidencia, name='crear_incidencia'),
    path('<int:pk>/', views.detalle_incidencia, name='detalle_incidencia'),
    
    path('<int:pk>/editar/', views.editar_incidencia, name='editar_incidencia'),
    path('<int:pk>/eliminar/', views.eliminar_incidencia, name='eliminar_incidencia'),
    path('<int:pk>/autorizar/', views.autorizar_incidencia, name='autorizar_incidencia'),
]