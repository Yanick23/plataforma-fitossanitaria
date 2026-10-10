import 'cultura.dart';

/// Estado de sincronização com a API (RF08, RF09).
enum EstadoSinc {
  pendente('PENDENTE'),
  sincronizado('SINCRONIZADO');

  const EstadoSinc(this.valor);
  final String valor;

  static EstadoSinc deTexto(String t) => values.firstWhere((e) => e.valor == t);
}

/// Fotografia associada a um diagnóstico (entidade Imagem).
class Imagem {
  const Imagem({required this.caminhoFicheiro, required this.dataCaptura});

  final String caminhoFicheiro;
  final DateTime dataCaptura;
}

/// Um diagnóstico guardado no historial local (entidade Diagnostico).
class Diagnostico {
  const Diagnostico({
    required this.id,
    required this.utilizadorId,
    required this.data,
    required this.cultura,
    required this.classePrevista,
    required this.confianca,
    required this.imagem,
    required this.versaoModelo,
    required this.tempoInferenciaMs,
    required this.tempoTotalMs,
    this.estadoSinc = EstadoSinc.pendente,
    this.imagemEnviada = false,
  });

  /// UUID gerado no telemóvel: a API usa-o para não criar duplicados (RNF07).
  final String id;
  final int utilizadorId;
  final DateTime data;
  final Cultura cultura;
  final String classePrevista;
  final double confianca; // 0..1
  final Imagem imagem;
  final int versaoModelo;
  final int tempoInferenciaMs;
  final int tempoTotalMs;
  final EstadoSinc estadoSinc;

  /// A imagem já foi aceite pela API (passo intermédio da sincronização).
  final bool imagemEnviada;

  Map<String, Object?> toMap() => {
        'id': id,
        'utilizador_id': utilizadorId,
        'data': data.toIso8601String(),
        'cultura': cultura.id,
        'classe_prevista': classePrevista,
        'confianca': confianca,
        'caminho_imagem': imagem.caminhoFicheiro,
        'data_captura': imagem.dataCaptura.toIso8601String(),
        'versao_modelo': versaoModelo,
        'tempo_inferencia_ms': tempoInferenciaMs,
        'tempo_total_ms': tempoTotalMs,
        'estado_sinc': estadoSinc.valor,
        'imagem_enviada': imagemEnviada ? 1 : 0,
      };

  factory Diagnostico.fromMap(Map<String, Object?> m) => Diagnostico(
        id: m['id'] as String,
        utilizadorId: m['utilizador_id'] as int,
        data: DateTime.parse(m['data'] as String),
        cultura: Cultura.porId(m['cultura'] as String),
        classePrevista: m['classe_prevista'] as String,
        confianca: (m['confianca'] as num).toDouble(),
        imagem: Imagem(
          caminhoFicheiro: m['caminho_imagem'] as String,
          dataCaptura: DateTime.parse(m['data_captura'] as String),
        ),
        versaoModelo: m['versao_modelo'] as int,
        tempoInferenciaMs: m['tempo_inferencia_ms'] as int,
        tempoTotalMs: m['tempo_total_ms'] as int,
        estadoSinc: EstadoSinc.deTexto(m['estado_sinc'] as String),
        imagemEnviada: (m['imagem_enviada'] as int) == 1,
      );

  /// Corpo JSON para POST /diagnosticos.
  Map<String, Object?> paraApi() => {
        'id': id,
        'cultura_id': cultura.id,
        'classe_prevista': classePrevista,
        'confianca': confianca,
        'data': data.toUtc().toIso8601String(),
        'versao_modelo': versaoModelo,
        'tempo_inferencia_ms': tempoInferenciaMs,
      };
}
