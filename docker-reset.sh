#!/usr/bin/env bash
echo "⛔ Matando contenedores..."
docker rm -f $(docker ps -aq) 2>/dev/null

echo "🗑 Eliminando imágenes..."
docker rmi -f $(docker images -aq) 2>/dev/null

echo "📦 Borrando volúmenes..."
docker volume rm $(docker volume ls -q) 2>/dev/null

echo "🌐 Borrando redes..."
docker network rm $(docker network ls -q) 2>/dev/null

echo "🧹 Limpiando cache..."
docker system prune -a --volumes --force

echo "✔ Docker limpiado completamente."
