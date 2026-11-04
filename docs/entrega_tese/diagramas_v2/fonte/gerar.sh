#!/bin/bash
# Gera os .drawio e os .png (na pasta diagramas_v2) com o draw.io headless em Docker.
set -e
AQUI="$(cd "$(dirname "$0")" && pwd)"
DESTINO="$AQUI/.."
PNG="$(mktemp -d)"
mkdir -p "$DESTINO" "$PNG"
for script in "$@"; do
  nome=$(basename "$script" .py)
  case $nome in
    d1_*) saida=D1_casos_de_uso ;; d2_*) saida=D2_classes ;; d3_*) saida=D3_arquitectura ;;
    d4_*) saida=D4_sequencia_diagnostico ;; d5_*) saida=D5_sequencia_validacao ;; d6_*) saida=D6_actividades_vigilancia ;;
  esac
  python3 "$AQUI/$script" "$PNG/$saida.drawio"
  timeout 180 docker run --rm --shm-size=1g -w /data -v "$PNG":/data \
    rlespinasse/drawio-desktop-headless:minimal-v1.77.0 -x -f png -s 2 -b 20 -o "$saida.png" "$saida.drawio" \
    2>&1 | grep -- "->" || echo "FALHOU: $saida"
  cp "$PNG/$saida.drawio" "$PNG/$saida.png" "$DESTINO/"
done
