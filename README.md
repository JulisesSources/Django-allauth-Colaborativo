# 🏢 SCA-B123 - Sistema de Control de Asistencias

Sistema integral de gestión de recursos humanos desarrollado con Django 5.0, enfocado en el control de asistencias, jornadas laborales e incidencias del personal del Instituto Tecnológico de Ciudad Guzmán.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)

---

## 📑 Tabla de Contenidos

- [Descripción del Proyecto](#-descripción-del-proyecto)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Stack Tecnológico](#-stack-tecnológico)
- [Ejecución con Docker Compose](#-ejecución-con-docker-compose)
- [Módulos del Sistema](#-módulos-del-sistema)
- [Comandos Útiles](#-comandos-útiles)
- [Contribuir](#-contribuir)

---

## 📋 Descripción del Proyecto

*SCA-B123* es una plataforma web para la gestión eficiente del personal en instituciones educativas. El sistema incluye:

- ✅ *Control de Asistencias* - Registro rápido tipo checador con cálculo automático de retardos (ASI, RET, FAL, JUS)
- 🗓 *Jornadas Laborales* - Definición de horarios, días laborales y calendario de días inhábiles
- 📝 *Gestión de Incidencias* - Solicitudes de permisos, justificaciones y autorizaciones
- 👥 *Sistema de Roles* - Permisos diferenciados (Admin, Jefe, Trabajador)
- 📊 *Reportes* - Dashboards con métricas y estadísticas en tiempo real

## 🏗 Estructura del Proyecto


Django-allauth-Colaborativo/
├── apps/
│   ├── accounts/              # Autenticación y perfiles de usuario
│   ├── trabajadores/          # Gestión de empleados
│   ├── unidades/              # Unidades administrativas
│   ├── jornadas_laborales/    # Horarios y calendario laboral
│   ├── asistencias/           # Control de asistencias y registros
│   ├── incidencias/           # Permisos y justificaciones
│   └── reportes/              # Generación de reportes
├── config/                    # Configuración Django (settings, urls)
├── templates/                 # Templates HTML
├── static/                    # Archivos estáticos (CSS, JS, img)
├── docker-compose.yml         # Orquestación de servicios
├── Dockerfile                 # Imagen Docker
└── requirements.txt           # Dependencias Python


## 🛠 Stack Tecnológico

- *Backend:* Django 5.0 + django-allauth
- *Base de Datos:* PostgreSQL 15
- *Frontend:* Tailwind CSS + Alpine.js
- *Containerización:* Docker + Docker Compose
- *SMTP Dev:* MailHog (visualizador de emails)

---

## 📦 Módulos del Sistema

### 1. Accounts (Autenticación)
- Login/Logout con django-allauth
- Gestión de perfiles con roles (Admin, Jefe, Trabajador)
- Recuperación de contraseña
- Dashboard personalizado por rol

### 2. Trabajadores
- CRUD de empleados con validaciones
- Asignación a unidades administrativas
- Gestión de puestos y nombramientos

### 3. Jornadas Laborales
- Definición de horarios (entrada/salida)
- Selección de días laborales (Lun-Dom)
- Calendario de días inhábiles
- Asignación de jornadas con vigencia

### 4. Asistencias
- *Registro Rápido:* Checador con reloj en tiempo real
- *Mi Asistencia:* Vista personal con estadísticas
- *Cálculo Automático:* ASI (Asistencia), RET (Retardo), FAL (Falta), JUS (Justificado)
- Validación de días inhábiles y jornadas vigentes

### 5. Incidencias
- Solicitud de permisos y justificaciones
- Flujo de autorización (Pendiente → Aprobado/Rechazado)
- Tipos de incidencia configurables

### 6. Reportes
- Dashboard con métricas en tiempo real
- Estadísticas por trabajador/unidad/período
- Porcentajes y gráficas de asistencia

---

## 🚀 Ejecución con Docker Compose

### Requisitos

- Docker
- Docker Compose

### Pasos para ejecutar

1. *Clonar el repositorio:*

   bash
   git clone https://github.com/JulisesSources/Django-allauth-Colaborativo.git
   cd Django-allauth-Colaborativo
   

2. *Configurar variables de entorno:*

   Copia el archivo de ejemplo .env.example a .env:

   bash
   # Windows (cmd)
   copy .env.example .env

   # Linux/Mac
   cp .env.example .env
   

   Puedes editar el archivo .env si necesitas cambiar alguna configuración, pero los valores por defecto funcionan correctamente con Docker Compose.

3. *Construir y levantar los contenedores:*

   bash
   docker compose up --build
   

   La primera vez tomará unos minutos mientras se descargan las imágenes y se instalan las dependencias.

4. *Aplicar migraciones y crear superusuario:*

   bash
   # Ejecutar migraciones
   docker compose exec web python manage.py migrate

   # Crear superusuario
   docker compose exec web python manage.py createsuperuser
   

5. *Acceder a la aplicación:*

   Una vez que los contenedores estén en ejecución, puedes acceder a:

   | Servicio | URL | Descripción |
   |----------|-----|-------------|
   | *Aplicación* | [http://localhost:8000](http://localhost:8000) | Sistema principal |
   | *Admin Django* | [http://localhost:8000/admin](http://localhost:8000/admin) | Panel administrativo |
   | *Login* | [http://localhost:8000/accounts/login](http://localhost:8000/accounts/login) | Página de inicio de sesión |
   | *MailHog* | [http://localhost:8025](http://localhost:8025) | Visualizador de emails |

---

## 🔧 Comandos Útiles

### Docker Compose

bash
# Ver logs en tiempo real
docker compose logs -f web

# Reiniciar un servicio
docker compose restart web

# Ver estado de los contenedores
docker compose ps

# Ejecutar comandos Django
docker compose exec web python manage.py <comando>

# Acceder al shell de Django
docker compose exec web python manage.py shell

# Recolectar archivos estáticos
docker compose exec web python manage.py collectstatic --noinput


### Base de Datos

bash
# Crear migraciones después de cambios en models
docker compose exec web python manage.py makemigrations

# Aplicar migraciones
docker compose exec web python manage.py migrate

# Acceder a PostgreSQL
docker compose exec db psql -U postgres -d sca_b123_db


---

## ⏹ Detener la Aplicación

Para detener los contenedores, presiona Ctrl+C en la terminal donde se está ejecutando, o ejecuta:

bash
docker compose down


Si deseas eliminar también los volúmenes (⚠ esto borra la base de datos):

bash
docker compose down -v


---

## 👥 Roles y Permisos

El sistema cuenta con tres tipos de roles con permisos específicos:

| Rol | Permisos | Acceso |
|-----|----------|--------|
| *Administrador* | Control total del sistema | Todos los módulos y configuraciones |
| *Jefe de Unidad* | Gestión de su unidad | Trabajadores, asistencias e incidencias de su unidad |
| *Trabajador* | Vista personal | Mi asistencia, mi jornada, mis incidencias |

### Funcionalidades por Rol

*Administrador:*
- ✅ Gestión completa de usuarios, trabajadores y unidades
- ✅ Configuración de jornadas laborales y calendario
- ✅ Autorización de todas las incidencias
- ✅ Acceso a reportes globales

*Jefe de Unidad:*
- ✅ Registro de asistencias de su equipo
- ✅ Autorización de incidencias de su unidad
- ✅ Consulta de reportes de su personal

*Trabajador:*
- ✅ Registro de su propia asistencia
- ✅ Solicitud de incidencias
- ✅ Consulta de su historial y estadísticas

---


## ⚙ Configuración del Sistema

### Variables de Entorno Principales

El archivo .env debe contener las siguientes variables clave:

env
# Django
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True

# Base de Datos
DB_NAME=sca_b123_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=db
DB_PORT=5432

# Email
EMAIL_HOST=mailhog
EMAIL_PORT=1025
DEFAULT_FROM_EMAIL=noreply@scab123.local


### Servicios Docker

El docker-compose.yml levanta 3 servicios:

- *db:* PostgreSQL 15 (Base de datos)
- *web:* Django App (Aplicación web en puerto 8000)
- *mailhog:* Servidor SMTP para desarrollo (UI en puerto 8025)

---

## 🔒 Seguridad

- *Autenticación:* django-allauth con verificación de email opcional
- *Permisos:* Decoradores personalizados @rol_requerido para proteger vistas
- *CSRF Protection:* Tokens CSRF en todos los formularios
- *Validaciones:* Validaciones a nivel de modelo, formulario y vista
- *Contraseñas:* Hash seguro con PBKDF2 de Django

---

## 🐛 Solución de Problemas Comunes

### Error: Puerto 8000 ya en uso

bash
# Windows: Verificar y terminar proceso
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# O cambiar el puerto en docker-compose.yml
ports:
  - "8001:8000"


### Error: No se puede conectar a la base de datos

bash
# Verificar que el contenedor db esté corriendo
docker compose ps

# Ver logs del contenedor
docker compose logs db

# Reiniciar servicios
docker compose restart


### Los cambios en el código no se reflejan

bash
# Reiniciar el contenedor web
docker compose restart web

# Si agregaste dependencias en requirements.txt
docker compose up --build


### Error al cargar volumen de datos o fixture

bash
# Si tienes un archivo de datos (fixture), primero asegúrate que las migraciones estén aplicadas
docker compose exec web python manage.py migrate

# Luego carga los datos
docker compose exec web python manage.py loaddata nombre_del_archivo.json

# Si el error persiste, verifica la estructura del archivo JSON


---

<div align="center">

*SCA-B123* - Sistema de Control de Asistencias
Instituto Tecnológico de Ciudad Guzmán

Desarrollado con Django 5.0 + PostgreSQL 15 + Docker

</div>