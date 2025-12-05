# accounts/decorators.py

from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def rol_requerido(*roles_permitidos):
    """
    Verifica que el usuario tenga uno de los roles permitidos.
    Uso: @rol_requerido('admin', 'jefe')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            # 1️⃣ Usuario no logueado
            if not request.user.is_authenticated:
                return redirect('account_login')

            # 2️⃣ Sin perfil → este NO debe redirigir al dashboard, porque causará loops
            if not hasattr(request.user, 'perfil'):
                messages.error(request, 'Tu cuenta no tiene un perfil asignado.')
                return redirect('account_logout')  # preferible sacarlo para evitar loops

            # 3️⃣ Verificar rol
            if request.user.perfil.rol not in roles_permitidos:
                messages.error(request, 'No tienes permisos para acceder aquí.')
                return redirect('no_autorizado')  # vista segura sin decoradores

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# === Decoradores para roles específicos === #

def admin_requerido(view_func):
    return rol_requerido('admin')(view_func)


def jefe_o_admin_requerido(view_func):
    return rol_requerido('admin', 'jefe')(view_func)


# === Decorador especial para autorizar incidencias === #

def puede_autorizar_incidencias(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect('account_login')

        if not hasattr(request.user, 'perfil'):
            messages.error(request, 'Tu usuario no tiene un perfil asignado.')
            return redirect('account_logout')

        if not request.user.perfil.puede_autorizar_incidencias:
            messages.error(request, 'No tienes permisos para autorizar incidencias.')
            return redirect('no_autorizado')

        return view_func(request, *args, **kwargs)
    return wrapper
