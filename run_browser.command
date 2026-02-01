#!/bin/bash
# Watch Auction - Open in Browser
# Double-click this file to run the application in your browser

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
    pip install -r requirements.txt
    touch venv/.installed
    echo ""
fi

echo "Iniciando servidor..."
echo ""
echo "A aplicação abrirá no seu navegador em:"
echo "  http://localhost:5000"
echo ""
echo "Pressione Ctrl+C para encerrar."
echo ""

# Open browser after a short delay
(sleep 2 && open http://localhost:5000) &

# Run Flask
python3 app.py

deactivate
