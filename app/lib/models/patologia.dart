import 'cultura.dart';

enum TipoPatologia {
  doenca('DOENCA'),
  praga('PRAGA'),
  saudavel('SAUDAVEL');

  const TipoPatologia(this.valor);
  final String valor;

  /// Aceita "DOENCA" (API) ou "doenca" (catálogo embutido).
  static TipoPatologia deTexto(String texto) =>
      values.firstWhere((t) => t.valor == texto.toUpperCase());
}

/// Fotografia de exemplo de uma patologia (descarregada na sincronização para ver sem rede).
class FotoReferencia {
  const FotoReferencia({required this.id, this.legenda, required this.url});

  final int id;
  final String? legenda;
  final String url; // relativo à API, ex.: /fotos-referencia/3

  Map<String, dynamic> toJson() => {'id': id, 'legenda': legenda, 'url': url};

  factory FotoReferencia.fromJson(Map<String, dynamic> j) =>
      FotoReferencia(id: j['id'] as int, legenda: j['legenda'] as String?, url: j['url'] as String);
}

/// Uma classe do modelo: doença, praga ou folha saudável.
/// Nome local e científico (RF06), recomendação básica (RF07) e, desde a fase 2,
/// sintomas, prevenção e fotografias de referência revistos no painel.
class Patologia {
  const Patologia({
    this.id,
    required this.cultura,
    required this.codigo,
    required this.nomeLocal,
    required this.nomeCientifico,
    required this.tipo,
    required this.recomendacao,
    this.sintomas,
    this.prevencao,
    this.validado = false,
    this.fotos = const [],
  });

  final int? id; // id na API (nulo no catálogo embutido)
  final Cultura cultura;
  final String codigo; // igual à classe do modelo, ex.: "mosaico"
  final String nomeLocal;
  final String nomeCientifico;
  final TipoPatologia tipo;
  final String recomendacao;
  final String? sintomas;
  final String? prevencao;

  /// O texto foi revisto e validado por um técnico no painel.
  final bool validado;
  final List<FotoReferencia> fotos;

  /// Formato do catálogo embutido (assets/catalogo.json).
  factory Patologia.doCatalogo(Cultura cultura, String codigo, Map<String, dynamic> j) => Patologia(
        cultura: cultura,
        codigo: codigo,
        nomeLocal: j['nome_local'] as String,
        nomeCientifico: j['nome_cientifico'] as String,
        tipo: TipoPatologia.deTexto(j['tipo'] as String),
        recomendacao: j['recomendacao'] as String,
        sintomas: j['sintomas'] as String?,
        prevencao: j['prevencao'] as String?,
        validado: j['validado'] as bool? ?? false,
        fotos: [for (final f in (j['fotos'] as List? ?? const [])) FotoReferencia.fromJson(f as Map<String, dynamic>)],
      );

  /// Formato da API (GET /patologias).
  factory Patologia.daApi(Map<String, dynamic> j) => Patologia(
        id: j['id'] as int?,
        cultura: Cultura.porId(j['cultura_id'] as String),
        codigo: j['codigo'] as String,
        nomeLocal: j['nome_local'] as String,
        nomeCientifico: j['nome_cientifico'] as String,
        tipo: TipoPatologia.deTexto(j['tipo'] as String),
        recomendacao: j['recomendacao'] as String,
        sintomas: j['sintomas'] as String?,
        prevencao: j['prevencao'] as String?,
        validado: j['validado_por_nome'] != null,
        fotos: [for (final f in (j['fotos'] as List? ?? const [])) FotoReferencia.fromJson(f as Map<String, dynamic>)],
      );

  Map<String, dynamic> paraCatalogo() => {
        'nome_local': nomeLocal,
        'nome_cientifico': nomeCientifico,
        'tipo': tipo.valor,
        'recomendacao': recomendacao,
        'sintomas': sintomas,
        'prevencao': prevencao,
        'validado': validado,
        'fotos': [for (final f in fotos) f.toJson()],
      };

  /// Usada se o modelo devolver uma classe que não está no catálogo.
  factory Patologia.desconhecida(Cultura cultura, String codigo) => Patologia(
        cultura: cultura,
        codigo: codigo,
        nomeLocal: codigo.replaceAll('_', ' '),
        nomeCientifico: '—',
        tipo: TipoPatologia.doenca,
        recomendacao: 'Sem informação no catálogo para esta classe. Consulte um técnico.',
      );

  String get rotuloTipo => switch (tipo) {
        TipoPatologia.praga => 'Praga detectada',
        TipoPatologia.doenca => 'Doença detectada',
        TipoPatologia.saudavel => 'Planta saudável',
      };
}
