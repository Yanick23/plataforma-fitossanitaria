import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter/services.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../models/cultura.dart';
import '../models/modelo_ml.dart';
import 'api_cliente.dart';
import 'classificador.dart';
import 'registo_tecnico.dart';

/// Decide que versão do modelo usar em cada cultura (RF12).
///
/// A versão 1 vem dentro do APK. Quando a API publica uma versão mais recente,
/// a sincronização descarrega-a, confirma o SHA-256 e a interface do modelo, e
/// só então a activa. O estado fica em documentos/modelos/estado.json.
class GestorModelos {
  GestorModelos._();
  static final instancia = GestorModelos._();

  final Map<Cultura, ModeloML> _descarregados = {};
  final Map<Cultura, List<String>> _classesEmbutidas = {};
  bool _carregado = false;

  Future<Directory> _pasta() async {
    final pasta = Directory(p.join((await getApplicationDocumentsDirectory()).path, 'modelos'));
    await pasta.create(recursive: true);
    return pasta;
  }

  Future<File> _ficheiroEstado() async => File(p.join((await _pasta()).path, 'estado.json'));

  Future<void> _carregarEstado() async {
    if (_carregado) return;
    final f = await _ficheiroEstado();
    if (await f.exists()) {
      final j = jsonDecode(await f.readAsString()) as Map<String, dynamic>;
      for (final c in Cultura.values) {
        final m = j[c.id];
        if (m != null) {
          final modelo = ModeloML.fromJson(c, m as Map<String, dynamic>);
          if (await File(modelo.caminhoTflite).exists()) _descarregados[c] = modelo;
        }
      }
    }
    _carregado = true;
  }

  Future<void> _gravarEstado() async {
    final f = await _ficheiroEstado();
    await f.writeAsString(jsonEncode({for (final e in _descarregados.entries) e.key.id: e.value.toJson()}));
  }

  /// Modelo em uso: o descarregado mais recente ou, se não houver, o embutido (v1).
  Future<ModeloML> modeloActual(Cultura cultura) async {
    await _carregarEstado();
    final descarregado = _descarregados[cultura];
    if (descarregado != null) return descarregado;
    final classes = _classesEmbutidas[cultura] ??=
        (jsonDecode(await rootBundle.loadString(cultura.classesEmbutidas)) as List).cast<String>();
    return ModeloML(
      cultura: cultura,
      versao: 1,
      caminhoTflite: cultura.modeloEmbutido,
      classes: classes,
      embutido: true,
    );
  }

  /// Verifica na API se há versão nova e instala-a. Devolve true se actualizou.
  Future<bool> actualizar(Cultura cultura) async {
    final actual = await modeloActual(cultura);
    final info = await ApiCliente.instancia.ultimaVersaoModelo(cultura);
    if (info == null || info.versao <= actual.versao) return false;

    final bytes = await ApiCliente.instancia.descarregar(info.urlFicheiro);
    if (sha256.convert(bytes).toString() != info.sha256) {
      throw const ErroApi('O modelo descarregado está corrompido (SHA-256 diferente).');
    }
    // Confirma que o novo modelo tem a interface esperada antes de o activar.
    Classificador.validarModelo(bytes, info.classes.length, cultura);

    final destino = File(p.join((await _pasta()).path, 'modelo_${cultura.id}_v${info.versao}.tflite'));
    await destino.writeAsBytes(bytes, flush: true);
    final anterior = _descarregados[cultura];
    _descarregados[cultura] = ModeloML(
      cultura: cultura,
      versao: info.versao,
      caminhoTflite: destino.path,
      classes: info.classes,
      acuraciaTeste: info.acuraciaTeste,
      embutido: false,
    );
    await _gravarEstado();
    Classificador.instancia.descartar(cultura); // a próxima inferência usa a versão nova
    if (anterior != null && anterior.caminhoTflite != destino.path) {
      await File(anterior.caminhoTflite).delete().catchError((_) => File(''));
    }
    RegistoTecnico.instancia.escrever('modelo ${cultura.id} actualizado para a versão ${info.versao}');
    return true;
  }
}
