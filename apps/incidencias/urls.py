# incidencias/urls.py

from django.urls import path
from . import views

app_name = 'incidencias'

urlpatterns = [
    path('', views.index, name='index'),
    path('lista/', views.lista_incidencias, name='lista_incidencias'),
    path('mis-incidencias/', views.mis_incidencias, name='mis_incidencias'),
    path('autorizar/', views.autorizar_incidencias, name='autorizar_incidencias'),
    path('crear/', views.crear_incidencia, name='crear_incidencia'),
    path('tipos/crear/', views.crear_tipo_incidencia, name='crear_tipo_incidencia'),
    path('tipos/', views.lista_tipos_incidencia, name='lista_tipos_incidencia'),
    path('tipos/<int:pk>/editar/', views.editar_tipo_incidencia, name='editar_tipo_incidencia'),
    # Rutas basadas en ID
    path('<int:pk>/', views.detalle_incidencia, name='detalle_incidencia'),
    path('<int:pk>/editar/', views.editar_incidencia, name='editar_incidencia'),
    path('<int:pk>/eliminar/', views.eliminar_incidencia, name='eliminar_incidencia'),
    path('<int:pk>/autorizar/', views.autorizar_incidencia, name='autorizar_incidencia'),
]
