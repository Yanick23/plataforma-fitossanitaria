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

/// Uma classe do modelo: doença, praga ou folha saudável.
/// Nome local e científico (RF06) e recomendação básica (RF07).
class Patologia {
  const Patologia({
    this.id,
    required this.cultura,
    required this.codigo,
    required this.nomeLocal,
    required this.nomeCientifico,
    required this.tipo,
    required this.recomendacao,
  });

  final int? id; // id na API (nulo no catálogo embutido)
  final Cultura cultura;
  final String codigo; // igual à classe do modelo, ex.: "mosaico"
  final String nomeLocal;
  final String nomeCientifico;
  final TipoPatologia tipo;
  final String recomendacao;

  /// Formato do catálogo embutido (assets/catalogo.json).
  factory Patologia.doCatalogo(Cultura cultura, String codigo, Map<String, dynamic> j) => Patologia(
        cultura: cultura,
        codigo: codigo,
        nomeLocal: j['nome_local'] as String,
        nomeCientifico: j['nome_cientifico'] as String,
        tipo: TipoPatologia.deTexto(j['tipo'] as String),
        recomendacao: j['recomendacao'] as String,
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
      );

  Map<String, dynamic> paraCatalogo() => {
        'nome_local': nomeLocal,
        'nome_cientifico': nomeCientifico,
        'tipo': tipo.valor,
        'recomendacao': recomendacao,
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
