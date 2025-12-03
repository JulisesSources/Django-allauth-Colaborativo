from django.urls import path
from . import views

app_name = "trabajadores"

urlpatterns = [
    path('', views.TrabajadorListView.as_view(), name='index'),
    path('crear/', views.TrabajadorCreateView.as_view(), name='crear'),
    path('<int:pk>/editar/', views.TrabajadorUpdateView.as_view(), name='editar'),
    path('<int:pk>/eliminar/', views.TrabajadorDeleteView.as_view(), name='eliminar'),
]
