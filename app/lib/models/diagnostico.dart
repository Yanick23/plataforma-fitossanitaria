import 'cultura.dart';

/// Estado de sincronização com a API (RF08, RF09).
enum EstadoSinc {
  pendente('PENDENTE'),
  sincronizado('SINCRONIZADO');

  const EstadoSinc(this.valor);
  final String valor;

  static EstadoSinc deTexto(String t) => values.firstWhere((e) => e.valor == t);
}

/// Validação do diagnóstico por um técnico (feita no painel web).
enum Validacao {
  pendente('PENDENTE'),
  confirmado('CONFIRMADO'),
  corrigido('CORRIGIDO');

  const Validacao(this.valor);
  final String valor;

  static Validacao deTexto(String t) => values.firstWhere((e) => e.valor == t, orElse: () => pendente);
}

/// Seguimento do tratamento: o agricultor seguiu a recomendação?
enum Seguiu {
  sim('SIM', 'Sim'),
  parcial('PARCIAL', 'Em parte'),
  nao('NAO', 'Não');

  const Seguiu(this.valor, this.rotulo);
  final String valor;
  final String rotulo;

  static Seguiu? deTexto(String? t) => values.where((e) => e.valor == t).firstOrNull;
}

/// Seguimento do tratamento: como ficou a planta?
enum ResultadoTratamento {
  melhorou('MELHOROU', 'Melhorou'),
  igual('IGUAL', 'Está igual'),
  piorou('PIOROU', 'Piorou'),
  naoSei('NAO_SEI', 'Não sei');

  const ResultadoTratamento(this.valor, this.rotulo);
  final String valor;
  final String rotulo;

  static ResultadoTratamento? deTexto(String? t) => values.where((e) => e.valor == t).firstOrNull;
}

/// Dias depois do diagnóstico em que a app pergunta pelo resultado do tratamento.
const int diasSeguimento = 7;

/// Depois disto já não se pergunta (a resposta deixa de ser fiável).
const int diasSeguimentoMaximo = 60;

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
    this.validacao = Validacao.pendente,
    this.classeConfirmada,
    this.notaTecnico,
    this.seguiu,
    this.resultadoTratamento,
    this.seguimentoEnviado = false,
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

  /// Validação pelo técnico, recebida na sincronização.
  final Validacao validacao;
  final String? classeConfirmada;
  final String? notaTecnico;

  /// Resposta do agricultor ao seguimento (nula se ainda não respondeu neste telemóvel).
  final Seguiu? seguiu;
  final ResultadoTratamento? resultadoTratamento;

  /// A API já tem a resposta (enviada daqui ou dada noutro telemóvel).
  final bool seguimentoEnviado;

  bool get seguimentoRespondido => seguiu != null || seguimentoEnviado;

  /// A classe a mostrar: a do técnico, se a corrigiu; senão a do modelo.
  String get classeFinal => classeConfirmada ?? classePrevista;

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
        'validacao': validacao.valor,
        'classe_confirmada': classeConfirmada,
        'nota_tecnico': notaTecnico,
        'seguiu': seguiu?.valor,
        'resultado_tratamento': resultadoTratamento?.valor,
        'seguimento_enviado': seguimentoEnviado ? 1 : 0,
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
        validacao: Validacao.deTexto(m['validacao'] as String? ?? 'PENDENTE'),
        classeConfirmada: m['classe_confirmada'] as String?,
        notaTecnico: m['nota_tecnico'] as String?,
        seguiu: Seguiu.deTexto(m['seguiu'] as String?),
        resultadoTratamento: ResultadoTratamento.deTexto(m['resultado_tratamento'] as String?),
        seguimentoEnviado: (m['seguimento_enviado'] as int? ?? 0) == 1,
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
