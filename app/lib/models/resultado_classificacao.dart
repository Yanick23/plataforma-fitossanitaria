import 'cultura.dart';
import 'medicao_inferencia.dart';

/// Abaixo deste valor a app avisa que não tem certeza e sugere nova foto (RF05).
/// É uma heurística: a probabilidade softmax não está calibrada (Guo et al., 2017).
const double limiarConfianca = 0.60;

/// Até quantas fotografias da mesma planta se podem juntar num diagnóstico.
const int maximoFotos = 3;

/// Uma fotografia analisada e as probabilidades que o modelo lhe deu.
class FotoAnalisada {
  const FotoAnalisada(this.caminho, this.probabilidades);
  final String caminho;
  final List<double> probabilidades;
}

class ResultadoClassificacao {
  ResultadoClassificacao({
    required this.cultura,
    required this.caminhoImagem,
    required this.dataCaptura,
    required this.classes,
    required this.probabilidades,
    required this.versaoModelo,
    required this.medicao,
    List<FotoAnalisada>? fotos,
  }) : fotos = fotos ?? [FotoAnalisada(caminhoImagem, probabilidades)];

  final Cultura cultura;

  /// A fotografia guardada com o diagnóstico (com várias, a que mais mostra a classe final).
  final String caminhoImagem;
  final DateTime dataCaptura;
  final List<String> classes;
  final List<double> probabilidades; // mesma ordem que [classes]; com várias fotos, a média
  final int versaoModelo;
  final MedicaoInferencia medicao; // da última fotografia
  final List<FotoAnalisada> fotos;

  bool get podeJuntarFoto => fotos.length < maximoFotos;

  /// Junta outra fotografia da mesma planta: a decisão passa a ser a média das probabilidades
  /// (um conjunto de vistas reduz o efeito de uma foto má ou de um ângulo enganador).
  ResultadoClassificacao juntar(ResultadoClassificacao outra) {
    assert(outra.cultura == cultura && outra.versaoModelo == versaoModelo);
    final todas = [...fotos, ...outra.fotos];
    final media = List<double>.generate(
        classes.length, (i) => todas.map((f) => f.probabilidades[i]).reduce((a, b) => a + b) / todas.length);
    var k = 0;
    for (var i = 1; i < media.length; i++) {
      if (media[i] > media[k]) k = i;
    }
    final melhor = todas.reduce((a, b) => b.probabilidades[k] > a.probabilidades[k] ? b : a);
    return ResultadoClassificacao(
      cultura: cultura,
      caminhoImagem: melhor.caminho,
      dataCaptura: dataCaptura,
      classes: classes,
      probabilidades: media,
      versaoModelo: versaoModelo,
      medicao: outra.medicao,
      fotos: todas,
    );
  }

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
