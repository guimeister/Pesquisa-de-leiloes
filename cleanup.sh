#!/bin/bash
#
# Watch Auction - Script de Limpeza
# Remove o programa e todos os resíduos
#

echo "=============================================="
echo "   Removendo Watch Auction e resíduos...     "
echo "=============================================="
echo ""

# Pasta do projeto
PROJECT_DIR="$HOME/Desktop/Pesquisa-de-leiloes"

# Remover pasta do projeto
if [ -d "$PROJECT_DIR" ]; then
    echo "Removendo pasta do projeto..."
    rm -rf "$PROJECT_DIR"
    echo "  ✓ Pasta removida: $PROJECT_DIR"
else
    echo "  - Pasta não encontrada: $PROJECT_DIR"
fi

# Remover DMG se existir
if [ -f "$HOME/Desktop/WatchAuction-Installer.dmg" ]; then
    rm -f "$HOME/Desktop/WatchAuction-Installer.dmg"
    echo "  ✓ DMG removido"
fi

# Remover app se foi instalado em Applications
if [ -d "/Applications/Watch Auction.app" ]; then
    rm -rf "/Applications/Watch Auction.app"
    echo "  ✓ App removido de Aplicativos"
fi

# Limpar cache pip relacionado (opcional)
echo ""
echo "Limpeza concluída!"
echo ""
