from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q, Count
from datetime import datetime, timedelta
from .models import PerfilUsuario
from .decorators import admin_requerido, jefe_o_admin_requerido
from .forms import PerfilUsuarioForm, AsignarRolForm


@login_required
def dashboard(request):
    """Vista principal del dashboard según el rol del usuario"""
    perfil = request.user.perfil
    
    context = {
        'perfil': perfil,
        'es_admin': perfil.es_admin(),
        'es_jefe': perfil.es_jefe(),
        'es_trabajador': perfil.es_trabajador(),
    }
    
    # Estadísticas según el rol
    if perfil.es_admin():
        # Importar modelos necesarios
        from apps.trabajadores.models import Trabajador
        from apps.asistencias.models import RegistroAsistencia
        from apps.incidencias.models import Incidencia
        from apps.unidades.models import UnidadAdministrativa
        
        # Estadísticas generales
        context['total_usuarios'] = User.objects.filter(is_active=True).count()
        context['total_trabajadores'] = Trabajador.objects.filter(activo=True).count()
        context['total_unidades'] = UnidadAdministrativa.objects.count()
        
        # Asistencias del día
        hoy = datetime.now().date()
        asistencias_hoy = RegistroAsistencia.objects.filter(fecha=hoy)
        context['asistencias_hoy'] = asistencias_hoy.filter(estatus='ASI').count()
        context['retardos_hoy'] = asistencias_hoy.filter(estatus='RET').count()
        context['faltas_hoy'] = asistencias_hoy.filter(estatus='FAL').count()
        
        # Incidencias pendientes
        context['incidencias_pendientes'] = Incidencia.objects.filter(
            estado='pendiente'
        ).count()
        
        # Usuarios por rol
        context['usuarios_por_rol'] = PerfilUsuario.objects.values('rol').annotate(
            total=Count('id_perfil')
        ).order_by('rol')
        
        # Últimas asistencias registradas (últimas 5)
        context['ultimas_asistencias'] = RegistroAsistencia.objects.select_related(
            'id_trabajador', 'id_trabajador__id_unidad'
        ).order_by('-fecha', '-hora_entrada')[:5]
        
    elif perfil.es_jefe():
        if perfil.id_trabajador:
            from apps.trabajadores.models import Trabajador
            from apps.asistencias.models import RegistroAsistencia
            from apps.incidencias.models import Incidencia
            
            mi_unidad = perfil.id_trabajador.id_unidad
            context['mi_unidad'] = mi_unidad
            
            # Trabajadores de la unidad
            trabajadores_unidad = Trabajador.objects.filter(
                id_unidad=mi_unidad,
                activo=True
            )
            context['total_trabajadores_unidad'] = trabajadores_unidad.count()
            
            # Asistencias del día en la unidad
            hoy = datetime.now().date()
            asistencias_hoy = RegistroAsistencia.objects.filter(
                fecha=hoy,
                id_trabajador__id_unidad=mi_unidad
            )
            context['asistencias_hoy'] = asistencias_hoy.filter(estatus='ASI').count()
            context['retardos_hoy'] = asistencias_hoy.filter(estatus='RET').count()
            context['faltas_hoy'] = asistencias_hoy.filter(estatus='FAL').count()
            
            # Incidencias pendientes de autorización de la unidad
            context['incidencias_pendientes'] = Incidencia.objects.filter(
                id_trabajador__id_unidad=mi_unidad,
                estado='pendiente'
            ).count()
            
            # Últimas asistencias de la unidad
            context['ultimas_asistencias'] = RegistroAsistencia.objects.filter(
                id_trabajador__id_unidad=mi_unidad
            ).select_related(
                'id_trabajador'
            ).order_by('-fecha', '-hora_entrada')[:5]
            
            # Trabajadores de la unidad
            context['trabajadores_unidad'] = trabajadores_unidad.select_related(
                'id_puesto'
            )[:10]
    
    elif perfil.es_trabajador():
        if perfil.id_trabajador:
            from apps.asistencias.models import RegistroAsistencia
            from apps.incidencias.models import Incidencia
            from apps.jornadas_laborales.models import TrabajadorJornada
            
            mi_trabajador = perfil.id_trabajador
            context['mi_trabajador'] = mi_trabajador
            
            # Asistencias del mes actual
            hoy = datetime.now().date()
            inicio_mes = hoy.replace(day=1)
            
            mis_asistencias = RegistroAsistencia.objects.filter(
                id_trabajador=mi_trabajador,
                fecha__gte=inicio_mes,
                fecha__lte=hoy
            )
            
            context['asistencias_mes'] = mis_asistencias.filter(estatus='ASI').count()
            context['retardos_mes'] = mis_asistencias.filter(estatus='RET').count()
            context['faltas_mes'] = mis_asistencias.filter(estatus='FAL').count()
            
            # Asistencia de hoy
            context['asistencia_hoy'] = RegistroAsistencia.objects.filter(
                id_trabajador=mi_trabajador,
                fecha=hoy
            ).first()
            
            # Mis incidencias
            context['mis_incidencias_pendientes'] = Incidencia.objects.filter(
                id_trabajador=mi_trabajador,
                estado='pendiente'
            ).count()
            
            context['mis_incidencias_rechazadas'] = Incidencia.objects.filter(
                id_trabajador=mi_trabajador,
                estado='rechazada'
            ).count()
            
            # Jornada asignada (vigente = sin fecha_fin o con fecha_fin futura)
            jornada_asignada = TrabajadorJornada.objects.filter(
                id_trabajador=mi_trabajador
            ).filter(
                Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=hoy)
            ).select_related('id_jornada').first()
            
            if jornada_asignada:
                context['mi_jornada'] = jornada_asignada.id_jornada
            
            # Últimas asistencias
            context['mis_ultimas_asistencias'] = RegistroAsistencia.objects.filter(
                id_trabajador=mi_trabajador
            ).order_by('-fecha')[:7]
    
    return render(request, 'account/dashboard.html', context)


@login_required
def mi_perfil(request):
    """Vista para que el usuario vea y edite su perfil"""
    perfil = request.user.perfil
    
    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, instance=perfil, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('accounts:mi_perfil')
    else:
        form = PerfilUsuarioForm(instance=perfil, user=request.user)
    
    context = {
        'form': form,
        'perfil': perfil,
    }
    return render(request, 'account/mi_perfil.html', context)


@admin_requerido
def lista_usuarios(request):
    """Vista para listar todos los usuarios (solo admin)"""
    query = request.GET.get('q', '')
    rol_filtro = request.GET.get('rol', '')
    
    usuarios = User.objects.select_related('perfil').all()
    
    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )
    
    if rol_filtro:
        usuarios = usuarios.filter(perfil__rol=rol_filtro)
    
    context = {
        'usuarios': usuarios.order_by('perfil__rol', 'email'),
        'query': query,
        'rol_filtro': rol_filtro,
        'roles': PerfilUsuario.ROLES,
        'es_admin': request.user.perfil.es_admin(),
    }
    return render(request, 'account/lista_usuarios.html', context)


@admin_requerido
def asignar_rol(request, user_id):
    """Vista para asignar o cambiar el rol de un usuario"""
    usuario = get_object_or_404(User, id=user_id)
    perfil = usuario.perfil
    
    if request.method == 'POST':
        form = AsignarRolForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, f'Rol actualizado para {usuario.email}')
            return redirect('accounts:lista_usuarios')
    else:
        form = AsignarRolForm(instance=perfil)
    
    context = {
        'form': form,
        'usuario': usuario,
        'perfil': perfil,
    }
    return render(request, 'account/asignar_rol.html', context)


@admin_requerido
def desactivar_usuario(request, user_id):
    """Vista para desactivar un usuario"""
    if request.method == 'POST':
        usuario = get_object_or_404(User, id=user_id)
        
        if usuario == request.user:
            messages.error(request, 'No puedes desactivar tu propia cuenta.')
        elif usuario.is_superuser:
            messages.error(request, 'No puedes desactivar una cuenta de superusuario.')
        else:
            usuario.is_active = False
            usuario.save()
            messages.success(request, f'Usuario {usuario.email} desactivado exitosamente.')
    
    return redirect('accounts:lista_usuarios')


@admin_requerido
def activar_usuario(request, user_id):
    """Vista para activar un usuario"""
    if request.method == 'POST':
        usuario = get_object_or_404(User, id=user_id)
        usuario.is_active = True
        usuario.save()
        messages.success(request, f'Usuario {usuario.email} activado exitosamente.')
    
    return redirect('accounts:lista_usuarios')


# 🚨 MUY IMPORTANTE: NO LLEVA DECORADORES
def no_autorizado(request):
    return render(request, 'account/no_autorizado.html')
