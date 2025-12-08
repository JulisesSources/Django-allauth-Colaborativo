# CHANGELOG — SCA-B123
Historial completo de cambios en el sistema de control de asistencia SCA-B123.  
Todas las versiones listadas aquí corresponden a la rama `develop` y se consideran **pre-releases** antes del lanzamiento oficial `v1.0.0` a `main`.

---

## 📚 Índice
- [v0.6.0 — Administración de Tipos de Incidencia (#8)](#v060--administración-de-tipos-de-incidencia-8)
- [v0.5.0 — Jornadas, Asistencias y Rediseño en Tema Oscuro (#1)](#v050--jornadas-asistencias-y-rediseño-en-tema-oscuro-1)
- [v0.4.0 — Trabajadores, Unidades, Puestos y Nombramientos (#7)](#v040--trabajadores-unidades-puestos-y-nombramientos-7)
- [v0.3.0 — Rediseño UI de Allauth y Gestión de Usuarios (#6)](#v030--rediseño-ui-de-allauth-y-gestión-de-usuarios-6)
- [v0.2.0 — Mejoras en Autorización y Filtros de Incidencias (#4)](#v020--mejoras-en-autorización-y-filtros-de-incidencias-4)
- [v0.1.0 — Autenticación y Gestión Inicial de Incidencias (#2)](#v010--autenticación-y-gestión-inicial-de-incidencias-2)

---

---

## **v0.6.0 — Administración de Tipos de Incidencia (#8)**
**Commit:** `0edb129`  
**Fecha:** No especificada

### ✨ Cambios principales
- Implementación del catálogo administrativo de **Tipos de Incidencia**.
- Vista para listar y editar tipos de incidencia.
- Control de acceso exclusivo para administradores.
- Navegación mejorada desde el módulo de incidencias.
- Nuevos templates:
  - `lista_tipos_incidencia.html`
  - `tipo_incidencia_form.html`
- Refuerzo de validaciones y permisos internos.

### 🔧 Archivos modificados
- `apps/incidencias/views.py`
- `apps/incidencias/urls.py`
- `templates/incidencias/lista_tipos_incidencia.html`
- `templates/incidencias/tipo_incidencia_form.html`
- `templates/incidencias/lista_incidencias.html`

---

## **v0.5.0 — Jornadas, Asistencias y Rediseño en Tema Oscuro (#1)**
**Commit:** `a00a024`  
**Fecha:** 2–6 de diciembre 2025

### 🗓️ Jornadas Laborales
- CRUD completo de jornadas.
- Asignaciones laborales con vigencia.
- Calendario laboral (días inhábiles).
- Vista personalizada “Mi Jornada”.
- Dashboard con métricas principales.
- Validaciones: días no laborales, dependencias, vigencias.

### 📝 Asistencias
- Registro rápido estilo checador.
- Registro manual con validaciones completas.
- Cálculo automático de estatus (ASI, RET, FAL, JUS).
- Vista personal “Mi Asistencia”.
- Filtros avanzados por fecha, trabajador y estatus.

### 🎨 Rediseño Completo (Tema Oscuro)
- Nuevo diseño unificado del sistema.
- Paleta de colores oscura.
- Badges, tablas, formularios y navegación renovados.
- Sidebar con sección “Personal”.

### 📁 Plantillas
Incluye más de 20 templates actualizados o nuevos:  
`lista_jornadas.html`, `form_jornada.html`, `lista_asistencias.html`, `registro_rapido.html`, `mi_registro.html`, etc.

---

## **v0.4.0 — Trabajadores, Unidades, Puestos y Nombramientos (#7)**
**Commit:** `266e0b2`  
**Fecha:** No especificada

### 👥 Módulo de Trabajadores
- Modelado completo con validaciones: RFC, CURP, número de empleado único.
- CRUD con tablas modernas y filtros avanzados.
- Integración con Unidades, Puestos y Nombramientos.

### 🏢 Módulo de Unidades Administrativas
- CRUD completo.
- Validaciones de dependencia (no eliminar unidades con trabajadores).
- UI moderna con Tailwind.

### 💼 Módulo de Puestos
- CRUD estándar.
- Validación de dependencias.
- Integración con Trabajadores.

### 🪪 Tipos de Nombramiento
- CRUD completo.
- Integración obligatoria al crear trabajadores.

### 🎨 UI
- Plantillas unificadas con Tailwind.
- Nuevas tablas, formularios y pantallas de edición.

---

## **v0.3.0 — Rediseño UI de Allauth y Gestión de Usuarios (#6)**
**Commit:** `a2a3fe7`

### 🎨 Rediseño Allauth
- Estilizado completo de todas las pantallas de autenticación:
  - `login`, `signup`, `password_reset`, `email_confirm`, etc.
- Implementación de layout base (`base_auth.html`).

### 👤 Gestión de Usuarios
- Nueva UI para administración de usuarios:
  - búsqueda, edición, desactivación.
- Pantalla moderna de perfil (`mi_perfil.html`).

### ⚙️ Configuración
- `ACCOUNT_UNIQUE_EMAIL = True` agregado.

---

## **v0.2.0 — Mejoras en Autorización y Filtros de Incidencias (#4)**
**Commit:** `0cb01f1`

### 🔐 Autorización y Visibilidad
- Los jefes solo ven incidencias de su unidad.
- Los administradores mantienen acceso total.
- Formulario de incidencias ahora filtra trabajadores según rol.
- Nuevas reglas de visibilidad en la vista de autorización.

### 🎨 Mejoras en Plantillas
- Rediseño visual en:
  - `lista_incidencias.html`
  - `mis_incidencias.html`
  - `detalle_incidencia.html`
  - `autorizar_incidencia.html`
- Nueva plantilla: `autorizar_incidencias.html`

### 🧩 Ajustes adicionales
- Refactor menor de vistas y urls.
- Integración de navegación por unidad.

---

## **v0.1.0 — Autenticación y Gestión Inicial de Incidencias (#2)**
**Commit:** `867afab`

### 🔐 Sistema de Autenticación (Accounts)
- Integración completa de django-allauth.
- Sistema de roles jerárquicos: Admin, Jefe, Trabajador.
- Gestión de perfiles de usuario.
- Decoradores personalizados para control de acceso.
- Templates modernos con Tailwind.

### 📄 Módulo de Incidencias
- CRUD completo con validaciones:
  - fechas coherentes  
  - solapamiento  
  - permisos  
- Auditoría completa:
  - `created_by`, `updated_by`, timestamps
- Filtros avanzados para búsqueda.

---