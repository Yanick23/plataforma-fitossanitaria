import 'dart:io';
import 'dart:isolate';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:tflite_flutter/tflite_flutter.dart';

import '../models/cultura.dart';
import '../models/medicao_inferencia.dart';
import '../models/modelo_ml.dart';
import '../models/resultado_classificacao.dart';
import 'gestor_modelos.dart';
import 'pre_processamento.dart';
import 'registo_tecnico.dart';

/// Erro com mensagem pronta a mostrar ao utilizador.
class ErroModelo implements Exception {
  const ErroModelo(this.mensagem);
  final String mensagem;
  @override
  String toString() => mensagem;
}

class _ModeloCarregado {
  _ModeloCarregado(this.modelo, this.interpreter, this.tamanhoBytes);
  final ModeloML modelo;
  final Interpreter interpreter;
  final int tamanhoBytes;
}

/// Inferência offline com TensorFlow Lite (RF03, RNF01), um modelo por cultura (RF02).
class Classificador {
  Classificador._();
  static final instancia = Classificador._();

  /// Uma thread: mede o desempenho no pior caso realista (telemóveis de gama baixa).
  static const int threads = 1;

  final Map<Cultura, _ModeloCarregado> _carregados = {};

  /// Cria o Interpreter e confirma a interface: entrada float32 [1,224,224,3]
  /// e saída float32 [1, n_classes] (probabilidades softmax).
  static Interpreter _criarInterpreter(Uint8List bytes, int nClasses, Cultura cultura) {
    final interpreter = Interpreter.fromBuffer(bytes, options: InterpreterOptions()..threads = threads)
      ..allocateTensors();
    final entrada = interpreter.getInputTensor(0);
    final saida = interpreter.getOutputTensor(0);
    final ok = entrada.type == TensorType.float32 &&
        listEquals(entrada.shape, const [1, tamanhoEntrada, tamanhoEntrada, 3]) &&
        saida.type == TensorType.float32 &&
        listEquals(saida.shape, [1, nClasses]);
    if (!ok) {
      interpreter.close();
      throw ErroModelo(
        'O modelo de ${cultura.nome.toLowerCase()} não tem a interface esperada.\n'
        'Entrada: ${entrada.type} ${entrada.shape} (esperado float32 [1, 224, 224, 3]).\n'
        'Saída: ${saida.type} ${saida.shape} (esperado float32 [1, $nClasses]).',
      );
    }
    return interpreter;
  }

  /// Usado pelo GestorModelos antes de activar um modelo descarregado.
  static void validarModelo(Uint8List bytes, int nClasses, Cultura cultura) =>
      _criarInterpreter(bytes, nClasses, cultura).close();

  /// Liberta o modelo em memória (ex.: depois de instalar uma versão nova).
  void descartar(Cultura cultura) => _carregados.remove(cultura)?.interpreter.close();

  Future<_ModeloCarregado> _carregar(Cultura cultura) async {
    final modelo = await GestorModelos.instancia.modeloActual(cultura);
    final existente = _carregados[cultura];
    if (existente != null && existente.modelo.versao == modelo.versao) return existente;
    descartar(cultura);

    final Uint8List bytes;
    try {
      if (modelo.embutido) {
        final dados = await rootBundle.load(modelo.caminhoTflite);
        bytes = dados.buffer.asUint8List(dados.offsetInBytes, dados.lengthInBytes);
      } else {
        bytes = await File(modelo.caminhoTflite).readAsBytes();
      }
    } on FlutterError {
      throw ErroModelo(
        'O modelo de ${cultura.nome.toLowerCase()} não está instalado na app.\n'
        'Copie ${cultura.modeloEmbutido.split('/').last} e ${cultura.classesEmbutidas.split('/').last} '
        'para app/assets/models/ e compile de novo.',
      );
    }
    final carregado =
        _ModeloCarregado(modelo, _criarInterpreter(bytes, modelo.classes.length, cultura), bytes.length);
    _carregados[cultura] = carregado;
    return carregado;
  }

  /// Executa o modelo e devolve as probabilidades softmax, medindo só a inferência.
  (Float32List, int) _inferir(_ModeloCarregado m, Float32List entrada) {
    final saida = Float32List(m.modelo.classes.length);
    final cronometro = Stopwatch()..start();
    // A entrada vai como bytes crus (float32). A saída tem de ser um ByteBuffer:
    // é a forma de o tflite_flutter escrever directamente no nosso Float32List.
    m.interpreter.run(entrada.buffer.asUint8List(), saida.buffer);
    cronometro.stop();
    return (saida, cronometro.elapsedMilliseconds);
  }

  /// [cronometroTotal] foi iniciado quando a imagem foi confirmada (RNF03).
  Future<ResultadoClassificacao> classificar(Cultura cultura, String caminhoImagem,
      {required Stopwatch cronometroTotal, required DateTime dataCaptura}) async {
    final jaCarregado = _carregados.containsKey(cultura);
    final cronoCarregamento = Stopwatch()..start();
    final m = await _carregar(cultura);
    cronoCarregamento.stop();

    final cronoPre = Stopwatch()..start();
    final Float32List entrada;
    try {
      entrada = await Isolate.run(() => preprocessarImagem(caminhoImagem));
    } on FormatException catch (e) {
      throw ErroModelo(e.message);
    }
    cronoPre.stop();

    final (probabilidades, inferenciaMs) = _inferir(m, entrada);
    cronometroTotal.stop();

    final medicao = MedicaoInferencia(
      data: DateTime.now(),
      cultura: cultura,
      versaoModelo: m.modelo.versao,
      carregamentoModeloMs: jaCarregado ? 0 : cronoCarregamento.elapsedMilliseconds,
      preProcessamentoMs: cronoPre.elapsedMilliseconds,
      inferenciaMs: inferenciaMs,
      tempoTotalMs: cronometroTotal.elapsedMilliseconds,
      memoriaRssBytes: ProcessInfo.currentRss,
      memoriaMaxRssBytes: ProcessInfo.maxRss,
      tamanhoModeloBytes: m.tamanhoBytes,
      threads: threads,
    );
    await RegistoTecnico.instancia.adicionar(medicao);

    return ResultadoClassificacao(
      cultura: cultura,
      caminhoImagem: caminhoImagem,
      dataCaptura: dataCaptura,
      classes: m.modelo.classes,
      probabilidades: probabilidades.toList(),
      versaoModelo: m.modelo.versao,
      medicao: medicao,
    );
  }

  /// Teste de desempenho para o relatório: [repeticoes] inferências seguidas com
  /// uma imagem sintética (cinzento médio). A primeira é descartada (aquecimento).
  Future<List<int>> testarDesempenho(Cultura cultura, {int repeticoes = 20}) async {
    final m = await _carregar(cultura);
    const n = tamanhoEntrada * tamanhoEntrada * 3;
    final entrada = Float32List(n)..fillRange(0, n, 127.0);
    _inferir(m, entrada); // aquecimento
    final tempos = <int>[];
    for (var i = 0; i < repeticoes; i++) {
      tempos.add(_inferir(m, entrada).$2);
      await Future<void>.delayed(Duration.zero); // deixa a interface respirar
    }
    final e = Estatisticas(tempos);
    RegistoTecnico.instancia.escrever(
      'teste de desempenho [${cultura.id} v${m.modelo.versao}] n=${e.n} média=${e.media.toStringAsFixed(1)}ms '
      'mín=${e.minimo}ms máx=${e.maximo}ms threads=$threads '
      'RSS=${(ProcessInfo.currentRss / 1048576).toStringAsFixed(1)}MB '
      'pico=${(ProcessInfo.maxRss / 1048576).toStringAsFixed(1)}MB',
    );
    return tempos;
  }
}
