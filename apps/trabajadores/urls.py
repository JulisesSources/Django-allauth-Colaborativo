from django.urls import path
from . import views
from django.views.generic import TemplateView

app_name = "trabajadores"

urlpatterns = [
    path('', views.TrabajadorListView.as_view(), name='index'),
    path('crear/', views.TrabajadorCreateView.as_view(), name='crear'),
    path('<int:pk>/editar/', views.TrabajadorUpdateView.as_view(), name='editar'),
    path('<int:pk>/eliminar/', views.TrabajadorDeleteView.as_view(), name='eliminar'),
    
    # --- PUESTOS ---
    path('puestos/', views.PuestoListView.as_view(), name='puestos-lista'),
    path('puestos/crear/', views.PuestoCreateView.as_view(), name='puestos-crear'),
    path('puestos/<int:pk>/editar/', views.PuestoUpdateView.as_view(), name='puestos-editar'),
    path('puestos/<int:pk>/eliminar/', views.PuestoDeleteView.as_view(), name='puestos-eliminar'),
    
    # --- NOMBRAMIENTOS ---
    path('nombramientos/', views.NombramientoListView.as_view(), name='nombramientos-lista'),
    path('nombramientos/crear/', views.NombramientoCreateView.as_view(), name='nombramientos-crear'),
    path('nombramientos/<int:pk>/editar/', views.NombramientoUpdateView.as_view(), name='nombramientos-editar'),
    path('nombramientos/<int:pk>/eliminar/', views.NombramientoDeleteView.as_view(), name='nombramientos-eliminar'),
]
