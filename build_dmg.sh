#!/bin/bash
#
# Watch Auction - Build DMG Installer for macOS
# Execute este script no Terminal do seu Mac
#

set -e

APP_NAME="Watch Auction"
DMG_NAME="WatchAuction-Installer"
VERSION="1.0.0"

echo "=============================================="
echo "   Watch Auction - Criando Instalador DMG    "
echo "=============================================="
echo ""

cd "$(dirname "$0")"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python 3 não encontrado."
    echo "Instale em: https://www.python.org/downloads/"
    exit 1
fi

# Create virtual environment
echo "1. Criando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "2. Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt
pip install py2app

# Build the app
echo "3. Construindo aplicação..."
rm -rf build dist

python setup_macos.py py2app 2>/dev/null || {
    echo "Usando método alternativo..."

    # Create app bundle manually
    mkdir -p "dist/$APP_NAME.app/Contents/MacOS"
    mkdir -p "dist/$APP_NAME.app/Contents/Resources"

    # Copy Python and dependencies
    cp -r venv "dist/$APP_NAME.app/Contents/Resources/"
    cp -r src "dist/$APP_NAME.app/Contents/Resources/"
    cp -r templates "dist/$APP_NAME.app/Contents/Resources/"
    cp -r static "dist/$APP_NAME.app/Contents/Resources/"
    cp app.py "dist/$APP_NAME.app/Contents/Resources/"
    cp desktop_app.py "dist/$APP_NAME.app/Contents/Resources/"
    cp requirements.txt "dist/$APP_NAME.app/Contents/Resources/"

    # Create launcher script
    cat > "dist/$APP_NAME.app/Contents/MacOS/$APP_NAME" << 'LAUNCHER'
#!/bin/bash
cd "$(dirname "$0")/../Resources"
source venv/bin/activate
python3 desktop_app.py
LAUNCHER
    chmod +x "dist/$APP_NAME.app/Contents/MacOS/$APP_NAME"

    # Create Info.plist
    cat > "dist/$APP_NAME.app/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Watch Auction</string>
    <key>CFBundleDisplayName</key>
    <string>Watch Auction</string>
    <key>CFBundleIdentifier</key>
    <string>com.watchauction.app</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundleExecutable</key>
    <string>Watch Auction</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>10.13.0</string>
</dict>
</plist>
PLIST
}

echo "4. Criando DMG..."

# Create DMG
DMG_DIR="dist/dmg"
mkdir -p "$DMG_DIR"
cp -r "dist/$APP_NAME.app" "$DMG_DIR/"

# Create Applications symlink
ln -sf /Applications "$DMG_DIR/Applications"

# Create DMG file
hdiutil create -volname "$APP_NAME" \
    -srcfolder "$DMG_DIR" \
    -ov -format UDZO \
    "dist/$DMG_NAME.dmg"

# Cleanup
rm -rf "$DMG_DIR"
deactivate

echo ""
echo "=============================================="
echo "   DMG criado com sucesso!"
echo "   Arquivo: dist/$DMG_NAME.dmg"
echo "=============================================="
echo ""
echo "Para instalar:"
echo "1. Abra o arquivo DMG"
echo "2. Arraste 'Watch Auction' para 'Applications'"
echo "3. Abra o app da pasta Aplicativos"
echo ""

# Open the dist folder
open dist/
