#98 – Paso a paso para configurar entorno y proyecto

## 1. Descargar el repositorio
```bash
git clone <URL_DEL_REPO>
cd <carpeta_del_repo>
```

## 2. Crear y activar entorno (UV)
```bash
uv venv .venv
source .venv/bin/activate
```

## 3. Instalar dependencias
```bash
uv pip install -r requirements.txt
```

## 4. Crear archivo .env
```
DEVEL=1
```

## 5. Migraciones
```bash
uv run python manage.py migrate
```

## 6. Cargar servidor
```bash
./runserver.sh
```