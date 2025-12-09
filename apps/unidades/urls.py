from django.urls import path
from . import views

app_name = "unidades"

urlpatterns = [
    path('', views.UnidadListView.as_view(), name='lista'),
    path('crear/', views.UnidadCreateView.as_view(), name='crear'),
    path('<int:pk>/editar/', views.UnidadUpdateView.as_view(), name='editar'),
    path('<int:pk>/eliminar/', views.UnidadDeleteView.as_view(), name='eliminar'),
]
