# incidencias/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.http import HttpResponseForbidden
from apps.accounts.decorators import jefe_o_admin_requerido, puede_autorizar_incidencias
from .models import Incidencia, TipoIncidencia
from .forms import IncidenciaForm, AutorizarIncidenciaForm, FiltroIncidenciaForm
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .forms import TipoIncidenciaForm
from apps.accounts.decorators import admin_requerido
from django.db import IntegrityError

@login_required
def index(request):
    perfil = request.user.perfil

    print(">>> Entrando a incidencias:index")
    print("Rol admin?:", perfil.es_admin())
    print("Rol jefe?:", perfil.es_jefe())
    print("Rol trabajador?:", perfil.es_trabajador())

    if perfil.es_admin():
        print("Redirigiendo a lista_incidencias")
        return redirect('incidencias:lista_incidencias')

    if perfil.es_jefe():
        print("Redirigiendo a lista_incidencias (jefe)")
        return redirect('incidencias:lista_incidencias')

    if perfil.es_trabajador():
        print("Redirigiendo a mis_incidencias")
        return redirect('incidencias:mis_incidencias')

    print("Fallback a /")
    return redirect('/')

@login_required
def lista_incidencias(request):
    """Vista para listar incidencias según el rol del usuario"""
    perfil = request.user.perfil
    
    # Filtrar incidencias según el rol
    if perfil.es_admin():
        incidencias = Incidencia.objects.all()
    elif perfil.es_jefe():
        # El jefe puede ver las de su unidad si tiene trabajador asociado
        if perfil.id_trabajador and perfil.id_trabajador.id_unidad:
            incidencias = Incidencia.objects.filter(
                id_trabajador__id_unidad=perfil.id_trabajador.id_unidad
            )
        else:
            incidencias = Incidencia.objects.all()
    else:
        # Trabajadores solo ven sus propias incidencias
        if perfil.id_trabajador:
            incidencias = Incidencia.objects.filter(id_trabajador=perfil.id_trabajador)
        else:
            incidencias = Incidencia.objects.none()
    
    # Preparar queryset de unidades para el formulario
    from apps.unidades.models import UnidadAdministrativa
    from apps.trabajadores.models import Trabajador
    
    if perfil.es_admin():
        unidades_queryset = UnidadAdministrativa.objects.all()
    else:
        unidades_queryset = UnidadAdministrativa.objects.none()
    
    # Aplicar filtros del formulario
    form = FiltroIncidenciaForm(request.GET, unidades_queryset=unidades_queryset)
    if form.is_valid():
        unidad = form.cleaned_data.get('unidad')
        trabajador = form.cleaned_data.get('trabajador')
        tipo_incidencia = form.cleaned_data.get('tipo_incidencia')
        estado = form.cleaned_data.get('estado')
        fecha_desde = form.cleaned_data.get('fecha_desde')
        fecha_hasta = form.cleaned_data.get('fecha_hasta')
        
        if unidad:
            incidencias = incidencias.filter(id_trabajador__id_unidad=unidad)
        
        if trabajador:
            incidencias = incidencias.filter(id_trabajador=trabajador)
        
        if tipo_incidencia:
            incidencias = incidencias.filter(id_tipo_incidencia=tipo_incidencia)
        
        if estado:
            incidencias = incidencias.filter(estado=estado)
        
        if fecha_desde:
            incidencias = incidencias.filter(fecha_inicio__gte=fecha_desde)
        
        if fecha_hasta:
            incidencias = incidencias.filter(fecha_fin__lte=fecha_hasta)
    
    # Preparar trabajadores agrupados por unidad para el template
    if perfil.es_admin():
        todos_trabajadores = Trabajador.objects.filter(activo=True).select_related('id_unidad').order_by('id_unidad', 'nombre', 'apellido_paterno')
    else:
        todos_trabajadores = Trabajador.objects.none()
    
    trabajadores = Trabajador.objects.filter(activo=True).select_related('id_unidad')
    if perfil.es_jefe() and perfil.id_trabajador and perfil.id_trabajador.id_unidad:
        trabajadores = trabajadores.filter(id_unidad=perfil.id_trabajador.id_unidad)
    
    # Estadísticas filtradas según el rol y unidad
    incidencias_para_stats = incidencias
    if perfil.es_jefe() and perfil.id_trabajador and perfil.id_trabajador.id_unidad:
        # Jefe ve estadísticas solo de su unidad (sin filtros aplicados)
        incidencias_para_stats = Incidencia.objects.filter(
            id_trabajador__id_unidad=perfil.id_trabajador.id_unidad
        )
    
    estadisticas = {
        'total': incidencias_para_stats.count(),
        'pendientes': incidencias_para_stats.filter(estado='pendiente').count(),
        'autorizadas': incidencias_para_stats.filter(estado='autorizada').count(),
        'rechazadas': incidencias_para_stats.filter(estado='rechazada').count(),
    }
    
    incidencias = incidencias.select_related(
        'id_trabajador',
        'id_tipo_incidencia',
        'autorizada_por',
        'created_by'
    ).order_by('-fecha_inicio', '-created_at')
    
    context = {
        'incidencias': incidencias,
        'form': form,
        'estadisticas': estadisticas,
        'perfil': perfil,
        'trabajadores': trabajadores,
        'todos_trabajadores': todos_trabajadores,
        'unidades': unidades_queryset,
        'es_admin': perfil.es_admin(),
        'es_jefe': perfil.es_jefe(),
    }
    return render(request, 'incidencias/lista_incidencias.html', context)


@login_required
def detalle_incidencia(request, pk):
    """Vista para ver el detalle de una incidencia"""
    incidencia = get_object_or_404(Incidencia, pk=pk)
    perfil = request.user.perfil
    
    # Detectar si viene desde mis_incidencias
    from_mis_incidencias = request.GET.get('from') == 'mis_incidencias'
    
    # Verificar permisos
    puede_ver = False
    if perfil.es_admin():
        puede_ver = True
    elif perfil.es_jefe():
        if perfil.id_trabajador and perfil.id_trabajador.id_unidad:
            puede_ver = incidencia.id_trabajador.id_unidad == perfil.id_trabajador.id_unidad
        else:
            puede_ver = True
    else:
        puede_ver = perfil.id_trabajador == incidencia.id_trabajador
    
    if not puede_ver:
        messages.error(request, 'No tienes permiso para ver esta incidencia.')
        return redirect('incidencias:lista_incidencias')
    
    context = {
        'incidencia': incidencia,
        'puede_autorizar': perfil.puede_autorizar_incidencias and incidencia.puede_ser_autorizada,
        'puede_editar': perfil.puede_autorizar_incidencias and incidencia.puede_ser_editada,
        'from_mis_incidencias': from_mis_incidencias,
    }
    return render(request, 'incidencias/detalle_incidencia.html', context)


@login_required
def crear_incidencia(request):
    """Vista para crear una nueva incidencia"""
    # Detectar si viene desde mis_incidencias
    from_mis_incidencias = request.GET.get('from') == 'mis_incidencias'
    
    if request.method == 'POST':
        form = IncidenciaForm(request.POST, user=request.user, from_mis_incidencias=from_mis_incidencias)
        if form.is_valid():
            try:
                incidencia = form.save(commit=False)
                incidencia.created_by = request.user
                incidencia.updated_by = request.user
                
                # Si el tipo no requiere autorización, marcarla como autorizada automáticamente
                if not incidencia.id_tipo_incidencia.requiere_autorizacion:
                    incidencia.estado = 'autorizada'
                    incidencia.autorizada_por = request.user
                    incidencia.fecha_autorizacion = timezone.now()
                
                incidencia.save()
                messages.success(request, 'Incidencia creada exitosamente.')
                
                # Si viene desde mis_incidencias, redirigir al detalle con ese parámetro
                if from_mis_incidencias:
                    return redirect(f"{reverse('incidencias:detalle_incidencia', args=[incidencia.pk])}?from=mis_incidencias")
                else:
                    return redirect('incidencias:detalle_incidencia', pk=incidencia.pk)
            except Exception as e:
                messages.error(request, f'Error al crear la incidencia: {str(e)}')
    else:
        form = IncidenciaForm(user=request.user, from_mis_incidencias=from_mis_incidencias)
    
    context = {
        'form': form,
        'titulo': 'Crear Nueva Incidencia',
        'boton': 'Crear Incidencia',
        'from_mis_incidencias': from_mis_incidencias,
        'trabajador_bloqueado': from_mis_incidencias and request.user.perfil.id_trabajador
    }
    return render(request, 'incidencias/form_incidencia.html', context)


@login_required
def editar_incidencia(request, pk):
    """Vista para editar una incidencia"""
    incidencia = get_object_or_404(Incidencia, pk=pk)
    perfil = request.user.perfil
    
    # Verificar permisos
    puede_editar = False
    if perfil.es_admin():
        puede_editar = incidencia.puede_ser_editada
    elif perfil.es_jefe():
        puede_editar = incidencia.puede_ser_editada
    else:
        puede_editar = (
            perfil.id_trabajador == incidencia.id_trabajador and 
            incidencia.puede_ser_editada
        )
    
    if not puede_editar:
        messages.error(request, 'No puedes editar esta incidencia.')
        return redirect('incidencias:detalle_incidencia', pk=pk)
    
    if request.method == 'POST':
        form = IncidenciaForm(request.POST, instance=incidencia, user=request.user)
        if form.is_valid():
            try:
                incidencia = form.save(commit=False)
                incidencia.updated_by = request.user
                incidencia.save()
                messages.success(request, 'Incidencia actualizada exitosamente.')
                return redirect('incidencias:detalle_incidencia', pk=incidencia.pk)
            except Exception as e:
                messages.error(request, f'Error al actualizar la incidencia: {str(e)}')
    else:
        form = IncidenciaForm(instance=incidencia, user=request.user)
    
    context = {
        'form': form,
        'incidencia': incidencia,
        'titulo': 'Editar Incidencia',
        'boton': 'Guardar Cambios'
    }
    return render(request, 'incidencias/form_incidencia.html', context)


@puede_autorizar_incidencias
def autorizar_incidencia(request, pk):
    """Vista para autorizar o rechazar una incidencia"""
    incidencia = get_object_or_404(Incidencia, pk=pk)
    
    if not incidencia.puede_ser_autorizada:
        messages.error(request, 'Esta incidencia no puede ser autorizada.')
        return redirect('incidencias:detalle_incidencia', pk=pk)
    
    if request.method == 'POST':
        form = AutorizarIncidenciaForm(request.POST)
        if form.is_valid():
            accion = form.cleaned_data['accion']
            comentario = form.cleaned_data['comentario']
            
            if accion == 'autorizar':
                incidencia.autorizar(request.user, comentario)
                messages.success(request, 'Incidencia autorizada exitosamente.')
            else:
                incidencia.rechazar(request.user, comentario)
                messages.success(request, 'Incidencia rechazada.')
            
            return redirect('incidencias:detalle_incidencia', pk=pk)
    else:
        form = AutorizarIncidenciaForm()
    
    context = {
        'form': form,
        'incidencia': incidencia,
    }
    return render(request, 'incidencias/autorizar_incidencia.html', context)


@login_required
def eliminar_incidencia(request, pk):
    """Vista para eliminar una incidencia"""
    incidencia = get_object_or_404(Incidencia, pk=pk)
    perfil = request.user.perfil
    
    # Solo admin puede eliminar, o el creador si está pendiente
    puede_eliminar = False
    if perfil.es_admin():
        puede_eliminar = True
    elif incidencia.created_by == request.user and incidencia.estado == 'pendiente':
        puede_eliminar = True
    
    if not puede_eliminar:
        messages.error(request, 'No tienes permiso para eliminar esta incidencia.')
        return redirect('incidencias:detalle_incidencia', pk=pk)
    
    if request.method == 'POST':
        incidencia.delete()
        messages.success(request, 'Incidencia eliminada exitosamente.')
        return redirect('incidencias:lista_incidencias')
    
    context = {
        'incidencia': incidencia,
    }
    return render(request, 'incidencias/eliminar_incidencia.html', context)


@login_required
def mis_incidencias(request):
    """Vista para que un trabajador vea solo sus incidencias"""
    perfil = request.user.perfil
    
    if not perfil.id_trabajador:
        messages.error(request, 'No tienes un trabajador asociado a tu cuenta.')
        return redirect('accounts:dashboard')
    
    incidencias = Incidencia.objects.filter(
        id_trabajador=perfil.id_trabajador
    ).select_related(
        'id_tipo_incidencia',
        'autorizada_por'
    ).order_by('-fecha_inicio')
    
    # Estadísticas
    estadisticas = {
        'total': incidencias.count(),
        'pendientes': incidencias.filter(estado='pendiente').count(),
        'autorizadas': incidencias.filter(estado='autorizada').count(),
        'rechazadas': incidencias.filter(estado='rechazada').count(),
    }
    
    context = {
        'incidencias': incidencias,
        'estadisticas': estadisticas,
        'perfil': perfil,
    }
    return render(request, 'incidencias/mis_incidencias.html', context)

@login_required
def autorizar_incidencias(request):
    """
    Lista de incidencias para autorización.
    - ADMIN: ve incidencias de todos.
    - JEFE: ve solo incidencias de su unidad.
    En la tabla se listan solo las 'pendientes',
    pero las estadísticas se calculan sobre todas las incidencias de su alcance.
    """
    perfil = request.user.perfil

    # Solo ADMIN o JEFE pueden entrar
    if not (perfil.es_admin() or perfil.es_jefe()):
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('incidencias:lista_incidencias')

    # Base de incidencias según alcance
    if perfil.es_admin():
        base_qs = Incidencia.objects.all()
    else:
        # JEFE: solo su unidad
        if perfil.id_trabajador and perfil.id_trabajador.id_unidad:
            base_qs = Incidencia.objects.filter(
                id_trabajador__id_unidad=perfil.id_trabajador.id_unidad
            )
        else:
            base_qs = Incidencia.objects.none()

    # Estadísticas dentro del alcance del usuario
    estadisticas = {
        'total': base_qs.count(),
        'pendientes': base_qs.filter(estado='pendiente').count(),
        'autorizadas': base_qs.filter(estado='autorizada').count(),
        'rechazadas': base_qs.filter(estado='rechazada').count(),
    }

    # Incidencias que se muestran en la tabla: solo pendientes
    incidencias = base_qs.select_related(
        'id_trabajador',
        'id_tipo_incidencia',
        'autorizada_por'
    ).order_by('-fecha_inicio', '-created_at')

    context = {
        'incidencias': incidencias,
        'estadisticas': estadisticas,
        'perfil': perfil,
    }
    return render(request, 'incidencias/autorizar_incidencias.html', context)


@jefe_o_admin_requerido
def crear_tipo_incidencia(request):
    """Vista para registrar un nuevo tipo de incidencia (admin o jefe)"""

    if request.method == 'POST':
        form = TipoIncidenciaForm(request.POST)

        if form.is_valid():
            try:
                tipo = form.save(commit=False)
                tipo.created_by = request.user
                tipo.updated_by = request.user
                tipo.save()

                messages.success(request, "Tipo de incidencia registrado correctamente.")
                return redirect('incidencias:lista_incidencias')

            except IntegrityError as e:
                messages.error(request, "Error al guardar: ya existe un tipo de incidencia o la base de datos rechazó el registro.")
                # no redirigimos para que el usuario vea el error en el mismo form

            except Exception as e:
                messages.error(request, f"Error inesperado: {str(e)}")

    else:
        form = TipoIncidenciaForm()

    return render(request, 'incidencias/tipo_incidencia_form.html', {
        'form': form,
        'titulo': 'Registrar Tipo de Incidencia',
        'boton': 'Guardar',
    })