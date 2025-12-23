#!/usr/bin/env bash
# build.sh - Script de build para Render
# ======================================

set -o errexit  # Salir si hay error

echo "📦 Instalando dependencias del sistema..."

# Instalar poppler para pdf2image (necesario para OpenAI Vision)
apt-get update && apt-get install -y poppler-utils

echo "🐍 Instalando dependencias de Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build completado!"

