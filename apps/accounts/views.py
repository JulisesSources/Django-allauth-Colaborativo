from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse("App: Accounts - Autenticación y perfiles por Fernando")