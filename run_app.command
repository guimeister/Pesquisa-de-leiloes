#!/bin/bash
# Watch Auction - Mac OS Launch Script
# Double-click this file to run the application

cd "$(dirname "$0")"

echo "=========================================="
echo "   Watch Auction - Pesquisa de Leilões   "
echo "=========================================="
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python 3 não está instalado."
    echo "Instale em: https://www.python.org/downloads/"
    read -p "Pressione Enter para sair..."
    exit 1
fi

# Check/create virtual environment
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.installed" ]; then
    echo "Instalando dependências..."
    pip install --upgrade pip
    pip install flask pywebview playwright
    pip install -r requirements.txt
    touch venv/.installed
    echo ""
fi

echo "Iniciando aplicação..."
echo "(Feche a janela para encerrar)"
echo ""

# Run the desktop app
python3 desktop_app.py

deactivate
