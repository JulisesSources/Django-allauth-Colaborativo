# Imagen base de Python
FROM python:3.11-slim

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para PostgreSQL
RUN apt-get update && apt-get install -y \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias Python
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copiar todo el código del proyecto
COPY . /app/

# Dar permisos de ejecución al entrypoint
RUN chmod +x /app/scripts/entrypoint.sh

# Exponer puerto 8000
EXPOSE 8000

# Entrypoint
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
# Comando por defecto
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]