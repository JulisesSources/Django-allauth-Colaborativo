from django.urls import path, include
from . import views

app_name = 'accounts'

urlpatterns = [
    # Dashboard y perfil
    path('dashboard/', views.dashboard, name='dashboard'),
    path('perfil/', views.mi_perfil, name='mi_perfil'),
    
    # Gestión de usuarios (solo admin)
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/<int:user_id>/rol/', views.asignar_rol, name='asignar_rol'),
    path('usuarios/<int:user_id>/desactivar/', views.desactivar_usuario, name='desactivar_usuario'),
    path('usuarios/<int:user_id>/activar/', views.activar_usuario, name='activar_usuario'),
    path('no-autorizado/', views.no_autorizado, name='no_autorizado'),

]