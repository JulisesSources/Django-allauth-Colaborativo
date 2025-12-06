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
                return redirect(request.META.get("HTTP_REFERER", "/"))

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# === Decoradores para roles específicos === #

def admin_requerido(view_func):
    return rol_requerido('admin')(view_func)


def jefe_o_admin_requerido(view_func):
	return rol_requerido('admin', 'jefe')(view_func)


def requiere_trabajador_y_unidad(view_func):
	"""
	Verifica que el usuario tenga un trabajador asociado y una unidad.
	EXCEPCIÓN: Los admins saltan esta validación.
	Usado para jefes y trabajadores que necesitan estas relaciones.
	"""
	@wraps(view_func)
	def wrapper(request, *args, **kwargs):
		# Los admins no necesitan estas validaciones
		if request.user.is_authenticated and hasattr(request.user, 'perfil') and request.user.perfil.es_admin():
			return view_func(request, *args, **kwargs)

		if not request.user.is_authenticated:
			return redirect('account_login')

		if not hasattr(request.user, 'perfil') or not request.user.perfil:
			messages.error(request, 'Tu cuenta no tiene un perfil asignado.')
			return redirect('account_logout')

		if not hasattr(request.user.perfil, 'id_trabajador') or not request.user.perfil.id_trabajador:
			messages.error(request, 'Tu perfil no tiene un trabajador asociado.')
			return redirect('account_logout')

		if not hasattr(request.user.perfil.id_trabajador, 'id_unidad') or not request.user.perfil.id_trabajador.id_unidad:
			messages.error(request, 'Tu trabajador no tiene una unidad asociada.')
			return redirect('account_logout')

		return view_func(request, *args, **kwargs)
	return wrapper


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
