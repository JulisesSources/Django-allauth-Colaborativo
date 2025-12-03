from django.urls import path
from . import views

app_name = 'jornadas_laborales'

urlpatterns = [
    # Lista de jornadas
    path('', views.JornadaListView.as_view(), name='index'),
    path('lista/', views.JornadaListView.as_view(), name='lista'),
    
    # Detalle de jornada
    path('<int:pk>/', views.JornadaDetailView.as_view(), name='detalle'),
    
    # Calendario laboral
    path('calendario/', views.CalendarioListView.as_view(), name='calendario'),
]