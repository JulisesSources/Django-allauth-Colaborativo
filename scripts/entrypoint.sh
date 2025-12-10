#!/bin/bash

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== SCA-B123 Entrypoint ===${NC}"

# Esperar a que PostgreSQL esté disponible
echo -e "${YELLOW}Esperando a PostgreSQL...${NC}"
while ! nc -z db 5432; do
  sleep 0.5
done
echo -e "${GREEN}✓ PostgreSQL está listo${NC}"

# Ejecutar migraciones
echo -e "${YELLOW}Aplicando migraciones...${NC}"
python manage.py migrate --noinput
echo -e "${GREEN}✓ Migraciones aplicadas${NC}"

# Crear superusuario si no existe
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo -e "${YELLOW}Verificando superusuario...${NC}"
    python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$DJANGO_SUPERUSER_EMAIL').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print('✓ Superusuario creado')
else:
    print('✓ Superusuario ya existe')
END
fi

# Collectstatic (sin input para automatizar)
echo -e "${YELLOW}Recolectando archivos estáticos...${NC}"
python manage.py collectstatic --noinput --clear
echo -e "${GREEN}✓ Archivos estáticos recolectados${NC}"

echo -e "${GREEN}=== Iniciando servidor ===${NC}"

# Ejecutar el comando principal
exec "$@"
```
