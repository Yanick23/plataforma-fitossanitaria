#!/usr/bin/env bash
# Recolhe, por adb, os dados do telemóvel para o relatório do PFC (secções B1, B2 e B5).
#
# Uso (Git Bash, telemóvel ligado por USB com a depuração USB activa):
#   bash docs/entrega_tese/recolher_dados_telemovel.sh dispositivo   # B1
#   bash docs/entrega_tese/recolher_dados_telemovel.sh tempos        # B2 (depois dos 20 diagnósticos)
#   bash docs/entrega_tese/recolher_dados_telemovel.sh capturas      # B5 (interactivo)
#
# Os ficheiros ficam em docs/entrega_tese/dados_telemovel/.

set -euo pipefail

PASTA="$(dirname "$0")/dados_telemovel"
mkdir -p "$PASTA/capturas"

adb get-state >/dev/null || { echo "Nenhum telemóvel ligado (adb devices)."; exit 1; }

dispositivo() {
  local f="$PASTA/dispositivo.txt"
  {
    echo "Marca:      $(adb shell getprop ro.product.manufacturer | tr -d '\r')"
    echo "Modelo:     $(adb shell getprop ro.product.model | tr -d '\r')"
    echo "Android:    $(adb shell getprop ro.build.version.release | tr -d '\r') (API $(adb shell getprop ro.build.version.sdk | tr -d '\r'))"
    echo "RAM total:  $(adb shell grep MemTotal /proc/meminfo | tr -d '\r' | awk '{printf "%.2f GB (%s kB)", $2/1048576, $2}')"
    echo "Núcleos:    $(adb shell nproc | tr -d '\r')"
    echo "SoC:        $(adb shell getprop ro.soc.manufacturer | tr -d '\r') $(adb shell getprop ro.soc.model | tr -d '\r')"
    echo "Plataforma: $(adb shell getprop ro.board.platform | tr -d '\r') / $(adb shell getprop ro.hardware | tr -d '\r')"
    echo "ABI:        $(adb shell getprop ro.product.cpu.abi | tr -d '\r')"
  } | tee "$f"
}

# Cada diagnóstico escreve no log uma linha "AgroDiagnostico/inferencia [milho v1] ... total=XXXms ...".
# O "total" vai da confirmação da fotografia até o resultado estar pronto (RNF03).
# Limpe o log antes dos testes com:  adb logcat -c
tempos() {
  local f="$PASTA/tempos_log.txt"
  adb logcat -d -s flutter | tr -d '\r' | grep 'AgroDiagnostico/inferencia' > "$f" || true
  echo "$(wc -l < "$f") diagnósticos encontrados no log ($f)"
  for cultura in milho mandioca; do
    grep "\[$cultura " "$f" | sed -E 's/.*total=([0-9]+)ms.*/\1/' | awk -v c="$cultura" '
      { t[NR] = $1 / 1000; s += t[NR]; if (NR == 1 || t[NR] < mn) mn = t[NR]; if (t[NR] > mx) mx = t[NR] }
      END {
        if (NR == 0) { printf "%s: sem medições\n", c; exit }
        printf "%s (n=%d):", c, NR; for (i = 1; i <= NR; i++) printf " %.3f", t[i]
        printf "\n  média=%.3f s  mín=%.3f s  máx=%.3f s\n", s / NR, mn, mx
      }'
  done | tee "$PASTA/tempos_resumo.txt"
}

capturas() {
  local nomes=(
    01_inicio_sessao 01b_criar_conta 02_ecra_inicial 03_seleccao_cultura 04_captura
    05_processamento 06_resultado_confianca_alta 07_resultado_confianca_baixa 08_historial
    09_detalhe_gradcam 10_administracao_ou_docs 11_diagnostico_tecnico
  )
  for n in "${nomes[@]}"; do
    read -r -p "Abra o ecrã '$n' e prima Enter (s = saltar): " r
    [[ "$r" == "s" ]] && continue
    adb exec-out screencap -p > "$PASTA/capturas/$n.png"
    echo "  -> capturas/$n.png"
  done
}

case "${1:-}" in
  dispositivo) dispositivo ;;
  tempos) tempos ;;
  capturas) capturas ;;
  *) echo "Uso: $0 dispositivo|tempos|capturas"; exit 1 ;;
esac
