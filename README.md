<div align="center">

# 🏢 SCA-B123

### Sistema de Control de Asistencias

*Sistema integral de gestión de recursos humanos desarrollado con Django 5.0*

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)

---

**Instituto Tecnológico de Ciudad Guzmán**

[🚀 Inicio Rápido](#-inicio-rápido) •
[📖 Documentación](#-módulos-del-sistema) •
[🔧 Configuración](#️-configuración) •
[🐛 Troubleshooting](#-solución-de-problemas)

</div>

---

## 📋 Descripción

**SCA-B123** es una plataforma web para la gestión eficiente del personal en instituciones educativas. Permite el control de asistencias, jornadas laborales e incidencias con un sistema de roles diferenciado.

### ✨ Características Principales

| Módulo | Descripción |
|--------|-------------|
| ✅ **Control de Asistencias** | Registro rápido tipo checador con cálculo automático de estatus |
| 🗓️ **Jornadas Laborales** | Definición de horarios, días laborales y calendario de días inhábiles |
| 📝 **Gestión de Incidencias** | Solicitudes de permisos, justificaciones y autorizaciones |
| 👥 **Sistema de Roles** | Permisos diferenciados (Admin, Jefe, Trabajador) |
| 📊 **Reportes** | Dashboards con métricas y estadísticas en tiempo real |

---

## 🚀 Inicio Rápido

### Requisitos Previos

- [Docker](https://www.docker.com/get-started) y Docker Compose
- Git

### ⚡ Instalación en 5 pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/JulisesSources/Django-allauth-Colaborativo.git
cd Django-allauth-Colaborativo

# 2. Configurar variables de entorno
copy .env.example .env          # Windows
cp .env.example .env            # Linux/Mac

# 3. Construir y levantar contenedores
docker compose up --build

# 4. Aplicar migraciones (en otra terminal)
docker compose exec web python manage.py migrate

# 5. Crear superusuario
docker compose exec web python manage.py createsuperuser
```

### 🌐 URLs de Acceso

| Servicio | URL | Descripción |
|:--------:|:---:|-------------|
| 🏠 **App** | [localhost:8000](http://localhost:8000) | Sistema principal |
| 🔐 **Admin** | [localhost:8000/admin](http://localhost:8000/admin) | Panel administrativo |
| 📧 **MailHog** | [localhost:8025](http://localhost:8025) | Visualizador de emails |

---

## 🏗️ Estructura del Proyecto

```
📦 Django-allauth-Colaborativo/
├── 📂 apps/
│   ├── 🔐 accounts/              # Autenticación y perfiles
│   ├── 👤 trabajadores/          # Gestión de empleados
│   ├── 🏛️ unidades/              # Unidades administrativas
│   ├── ⏰ jornadas_laborales/    # Horarios y calendario
│   ├── ✅ asistencias/           # Control de asistencias
│   ├── 📝 incidencias/           # Permisos y justificaciones
│   └── 📊 reportes/              # Generación de reportes
├── 📂 config/                    # Configuración Django
├── 📂 templates/                 # Templates HTML
├── 📂 static/                    # Archivos estáticos
├── 🐳 docker-compose.yml
├── 🐳 Dockerfile
└── 📄 requirements.txt
```

---

## 🛠️ Stack Tecnológico

<table>
<tr>
<td align="center" width="150">

**Backend**

</td>
<td align="center" width="150">

**Frontend**

</td>
<td align="center" width="150">

**Base de Datos**

</td>
<td align="center" width="150">

**DevOps**

</td>
</tr>
<tr>
<td align="center">

Django 5.0<br>
django-allauth<br>
Python 3.11

</td>
<td align="center">

Tailwind CSS<br>
Alpine.js<br>
HTML5

</td>
<td align="center">

PostgreSQL 15

</td>
<td align="center">

Docker<br>
Docker Compose<br>
MailHog

</td>
</tr>
</table>

---

## 📦 Módulos del Sistema

<details>
<summary><b>🔐 Accounts (Autenticación)</b></summary>

- Login/Logout con django-allauth
- Gestión de perfiles con roles (Admin, Jefe, Trabajador)
- Recuperación de contraseña
- Dashboard personalizado por rol

</details>

<details>
<summary><b>👤 Trabajadores</b></summary>

- CRUD de empleados con validaciones
- Asignación a unidades administrativas
- Gestión de puestos y nombramientos

</details>

<details>
<summary><b>⏰ Jornadas Laborales</b></summary>

- Definición de horarios (entrada/salida)
- Selección de días laborales (Lun-Dom)
- Calendario de días inhábiles
- Asignación de jornadas con vigencia

</details>

<details>
<summary><b>✅ Asistencias</b></summary>

- **Registro Rápido:** Checador con reloj en tiempo real
- **Mi Asistencia:** Vista personal con estadísticas
- **Cálculo Automático:** ASI (Asistencia), RET (Retardo), FAL (Falta), JUS (Justificado)
- Validación de días inhábiles y jornadas vigentes

</details>

<details>
<summary><b>📝 Incidencias</b></summary>

- Solicitud de permisos y justificaciones
- Flujo de autorización (Pendiente → Aprobado/Rechazado)
- Tipos de incidencia configurables

</details>

<details>
<summary><b>📊 Reportes</b></summary>

- Dashboard con métricas en tiempo real
- Estadísticas por trabajador/unidad/período
- Porcentajes y gráficas de asistencia

</details>

---

## 👥 Roles y Permisos

```
┌─────────────────────────────────────────────────────────────────┐
│                        ADMINISTRADOR                            │
│  • Control total del sistema                                    │
│  • Gestión de usuarios, trabajadores y unidades                 │
│  • Configuración de jornadas y calendario                       │
│  • Autorización de todas las incidencias                        │
│  • Acceso a reportes globales                                   │
├─────────────────────────────────────────────────────────────────┤
│                       JEFE DE UNIDAD                            │
│  • Registro de asistencias de su equipo                         │
│  • Autorización de incidencias de su unidad                     │
│  • Consulta de reportes de su personal                          │
├─────────────────────────────────────────────────────────────────┤
│                         TRABAJADOR                              │
│  • Registro de su propia asistencia                             │
│  • Solicitud de incidencias                                     │
│  • Consulta de su historial y estadísticas                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuración

### Variables de Entorno

```env
# 🔑 Django
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True

# 🗄️ Base de Datos
DB_NAME=sca_b123_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=db
DB_PORT=5432

# 📧 Email
EMAIL_HOST=mailhog
EMAIL_PORT=1025
DEFAULT_FROM_EMAIL=noreply@scab123.local
```

### 🐳 Servicios Docker

| Servicio | Imagen | Puerto | Descripción |
|----------|--------|--------|-------------|
| **db** | PostgreSQL 15 | 5432 | Base de datos |
| **web** | Django App | 8000 | Aplicación web |
| **mailhog** | MailHog | 8025 | Servidor SMTP dev |

---

## 🔧 Comandos Útiles

<details>
<summary><b>🐳 Docker Compose</b></summary>

```bash
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
```

</details>

<details>
<summary><b>🗄️ Base de Datos</b></summary>

```bash
# Crear migraciones
docker compose exec web python manage.py makemigrations

# Aplicar migraciones
docker compose exec web python manage.py migrate

# Acceder a PostgreSQL
docker compose exec db psql -U postgres -d sca_b123_db
```

</details>

<details>
<summary><b>⏹️ Detener la Aplicación</b></summary>

```bash
# Detener contenedores
docker compose down

# Detener y eliminar volúmenes (⚠️ borra la BD)
docker compose down -v
```

</details>

---

## 🔒 Seguridad

| Característica | Implementación |
|----------------|----------------|
| 🔐 Autenticación | django-allauth con verificación de email |
| 🛡️ Permisos | Decoradores `@rol_requerido` personalizados |
| 🔑 CSRF | Tokens CSRF en todos los formularios |
| ✅ Validaciones | A nivel de modelo, formulario y vista |
| 🔒 Contraseñas | Hash seguro con PBKDF2 de Django |

---

## 🐛 Solución de Problemas

<details>
<summary><b>❌ Puerto 8000 ya en uso</b></summary>

```bash
# Windows: Verificar y terminar proceso
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# O cambiar el puerto en docker-compose.yml
ports:
  - "8001:8000"
```

</details>

<details>
<summary><b>❌ No se puede conectar a la base de datos</b></summary>

```bash
# Verificar contenedores
docker compose ps

# Ver logs
docker compose logs db

# Reiniciar servicios
docker compose restart
```

</details>

<details>
<summary><b>❌ Cambios en el código no se reflejan</b></summary>

```bash
# Reiniciar el contenedor web
docker compose restart web

# Si agregaste dependencias
docker compose up --build
```

</details>

---

<div align="center">

## 📄 Licencia

Este proyecto fue desarrollado para el **Instituto Tecnológico de Ciudad Guzmán**

---

**SCA-B123** • Sistema de Control de Asistencias

Hecho con ❤️ usando Django 5.0 + PostgreSQL 15 + Docker

</div>
