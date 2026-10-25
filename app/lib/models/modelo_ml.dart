import 'cultura.dart';

/// Versão do modelo de classificação em uso para uma cultura (entidade ModeloML).
class ModeloML {
  const ModeloML({
    required this.cultura,
    required this.versao,
    required this.caminhoTflite,
    required this.classes,
    required this.embutido,
    this.acuraciaTeste,
    this.piloto = false,
  });

  final Cultura cultura;
  final int versao;

  /// Caminho do asset (embutido) ou do ficheiro descarregado da API.
  final String caminhoTflite;

  /// Nomes das classes pela ordem das saídas do modelo.
  final List<String> classes;
  final bool embutido;
  final double? acuraciaTeste;

  /// Versão em teste no distrito do agricultor (piloto); pode ser retirada e a app volta à anterior.
  final bool piloto;

  Map<String, dynamic> toJson() => {
        'versao': versao,
        'caminho_tflite': caminhoTflite,
        'classes': classes,
        'acuracia_teste': acuraciaTeste,
        'piloto': piloto,
      };

  factory ModeloML.fromJson(Cultura cultura, Map<String, dynamic> j) => ModeloML(
        cultura: cultura,
        versao: j['versao'] as int,
        caminhoTflite: j['caminho_tflite'] as String,
        classes: (j['classes'] as List).cast<String>(),
        acuraciaTeste: (j['acuracia_teste'] as num?)?.toDouble(),
        piloto: j['piloto'] as bool? ?? false,
        embutido: false,
      );
}
