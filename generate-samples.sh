#!/bin/bash

mkdir -p samples

snatch -f pyproject.toml -t miasma -o samples/miasma.png --no-chrome --no-decorations
snatch -f pyproject.toml -t monokai -o samples/monokai.png --no-chrome --no-decorations
snatch -f pyproject.toml -t solarized-dark -o samples/solarized-dark.png --no-chrome --no-decorations
snatch -f pyproject.toml -t solarized-light -o samples/solarized-light.png --no-chrome --no-decorations
snatch -f pyproject.toml -t coffee -o samples/coffee.png --no-chrome --no-decorations
snatch -f pyproject.toml -t gruvbox-light -o samples/gruvbox-light.png --no-chrome --no-decorations
snatch -f pyproject.toml -t gruvbox-dark -o samples/gruvbox-dark.png --no-chrome --no-decorations
snatch -f pyproject.toml -t dracula -o samples/dracula.png --no-chrome --no-decorations
