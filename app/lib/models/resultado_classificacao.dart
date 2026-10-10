import 'cultura.dart';
import 'medicao_inferencia.dart';

/// Abaixo deste valor a app avisa que não tem certeza e sugere nova foto (RF05).
/// É uma heurística: a probabilidade softmax não está calibrada (Guo et al., 2017).
const double limiarConfianca = 0.60;

class ResultadoClassificacao {
  const ResultadoClassificacao({
    required this.cultura,
    required this.caminhoImagem,
    required this.dataCaptura,
    required this.classes,
    required this.probabilidades,
    required this.versaoModelo,
    required this.medicao,
  });

  final Cultura cultura;
  final String caminhoImagem;
  final DateTime dataCaptura;
  final List<String> classes;
  final List<double> probabilidades; // mesma ordem que [classes]
  final int versaoModelo;
  final MedicaoInferencia medicao;

  int get indicePrevisto {
    var melhor = 0;
    for (var i = 1; i < probabilidades.length; i++) {
      if (probabilidades[i] > probabilidades[melhor]) melhor = i;
    }
    return melhor;
  }

  String get classe => classes[indicePrevisto];
  double get confianca => probabilidades[indicePrevisto];
  bool get confiancaBaixa => confianca < limiarConfianca;
}
