import 'cultura.dart';

/// Medição de desempenho de um diagnóstico, para os RNF03 (tempo de resposta)
/// e RNF04 (hardware limitado).
class MedicaoInferencia {
  const MedicaoInferencia({
    required this.data,
    required this.cultura,
    required this.versaoModelo,
    required this.carregamentoModeloMs,
    required this.preProcessamentoMs,
    required this.inferenciaMs,
    required this.tempoTotalMs,
    required this.memoriaRssBytes,
    required this.memoriaMaxRssBytes,
    required this.tamanhoModeloBytes,
    required this.threads,
  });

  final DateTime data;
  final Cultura cultura;
  final int versaoModelo;

  /// 0 quando o modelo já estava carregado em memória.
  final int carregamentoModeloMs;
  final int preProcessamentoMs;

  /// Só a chamada ao Interpreter (Stopwatch à volta de `run`).
  final int inferenciaMs;

  /// RNF03: da confirmação da imagem até o resultado estar pronto.
  final int tempoTotalMs;

  /// Memória residente do processo logo após a inferência (ProcessInfo.currentRss).
  final int memoriaRssBytes;

  /// Pico de memória residente desde o arranque da app (ProcessInfo.maxRss).
  final int memoriaMaxRssBytes;
  final int tamanhoModeloBytes;
  final int threads;

  static const cabecalhoCsv =
      'data;cultura;versao_modelo;carregamento_ms;pre_processamento_ms;inferencia_ms;total_ms;'
      'rss_mb;pico_rss_mb;modelo_mb;threads';

  String paraCsv() => [
        data.toIso8601String(),
        cultura.id,
        versaoModelo,
        carregamentoModeloMs,
        preProcessamentoMs,
        inferenciaMs,
        tempoTotalMs,
        (memoriaRssBytes / 1048576).toStringAsFixed(1),
        (memoriaMaxRssBytes / 1048576).toStringAsFixed(1),
        (tamanhoModeloBytes / 1048576).toStringAsFixed(2),
        threads,
      ].join(';');

  @override
  String toString() =>
      '[${cultura.id} v$versaoModelo] inferência=${inferenciaMs}ms pré-processamento=${preProcessamentoMs}ms '
      'carregamento=${carregamentoModeloMs}ms total=${tempoTotalMs}ms '
      'RSS=${(memoriaRssBytes / 1048576).toStringAsFixed(1)}MB '
      'pico=${(memoriaMaxRssBytes / 1048576).toStringAsFixed(1)}MB threads=$threads';
}
