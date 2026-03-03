.PHONY: run build install clean dmg

# Run in development mode
run:
	python3 -m kitto.main

# Build .app bundle
build:
	bash build.sh

# Install to /Applications
install: build
	cp -r dist/Kitto.app /Applications/
	@echo "Kitto installed to /Applications/Kitto.app"

# Create DMG
dmg: build
	hdiutil create -volname Kitto -srcfolder dist/Kitto.app -ov -format UDZO dist/Kitto.dmg
	@echo "DMG created at dist/Kitto.dmg"

# Clean build artifacts
clean:
	rm -rf build dist .eggs *.egg-info
	find . -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
