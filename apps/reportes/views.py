from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse("App: Reportes - Módulo en construcción por Christian")