.PHONY: install run run-desktop run-browser build-macos clean

# Install dependencies
install:
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt
	@echo ""
	@echo "Instalação concluída!"
	@echo "Execute: make run"

# Run in browser (default)
run: run-browser

# Run Flask server and open browser
run-browser:
	@echo "Iniciando servidor em http://localhost:5000"
	@(sleep 2 && open http://localhost:5000 2>/dev/null || xdg-open http://localhost:5000 2>/dev/null) &
	./venv/bin/python app.py

# Run as desktop app
run-desktop:
	./venv/bin/python desktop_app.py

# Build macOS .app bundle
build-macos:
	./venv/bin/pip install py2app
	./venv/bin/python setup_macos.py py2app
	@echo ""
	@echo "App criado em: dist/Watch Auction.app"

# Clean build files
clean:
	rm -rf build dist venv __pycache__ src/__pycache__
	rm -f *.pyc watches.db
