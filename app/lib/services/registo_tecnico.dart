import 'dart:developer' as developer;
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../models/medicao_inferencia.dart';

/// Medições de desempenho (RNF03, RNF04):
///  - em memória, para o ecrã "Diagnóstico técnico";
///  - no log (`flutter logs` / `adb logcat`, etiqueta "AgroDiagnostico");
///  - num ficheiro CSV persistente (documentos/registo_tecnico.csv), para o relatório.
class RegistoTecnico extends ChangeNotifier {
  RegistoTecnico._();
  static final instancia = RegistoTecnico._();

  final List<MedicaoInferencia> _medicoes = [];
  List<MedicaoInferencia> get medicoes => List.unmodifiable(_medicoes.reversed);

  Future<File> ficheiroCsv() async =>
      File(p.join((await getApplicationDocumentsDirectory()).path, 'registo_tecnico.csv'));

  Future<void> adicionar(MedicaoInferencia medicao) async {
    _medicoes.add(medicao);
    debugPrint('AgroDiagnostico/inferencia $medicao');
    developer.log(medicao.toString(), name: 'AgroDiagnostico.inferencia');
    notifyListeners();
    try {
      final f = await ficheiroCsv();
      final novo = !await f.exists();
      await f.writeAsString('${novo ? '${MedicaoInferencia.cabecalhoCsv}\n' : ''}${medicao.paraCsv()}\n',
          mode: FileMode.append, flush: true);
    } catch (e) {
      debugPrint('AgroDiagnostico/tecnico não foi possível escrever o CSV: $e');
    }
  }

  void escrever(String mensagem) {
    debugPrint('AgroDiagnostico/tecnico $mensagem');
    developer.log(mensagem, name: 'AgroDiagnostico.tecnico');
  }
}

/// Estatísticas simples de uma lista de tempos (ms).
class Estatisticas {
  Estatisticas(List<int> valores)
      : n = valores.length,
        media = valores.isEmpty ? 0 : valores.reduce((a, b) => a + b) / valores.length,
        minimo = valores.isEmpty ? 0 : valores.reduce((a, b) => a < b ? a : b),
        maximo = valores.isEmpty ? 0 : valores.reduce((a, b) => a > b ? a : b);

  final int n;
  final double media;
  final int minimo;
  final int maximo;
}
