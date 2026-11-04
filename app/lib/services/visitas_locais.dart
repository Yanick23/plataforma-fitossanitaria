import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../models/visita.dart';
import 'api_cliente.dart';

/// Pedidos de visita do agricultor, por diagnóstico (o mais recente de cada um).
/// Guardados no telemóvel; actualizados na sincronização (GET /visitas/minhas).
class VisitasLocais extends ChangeNotifier {
  VisitasLocais._();
  static final instancia = VisitasLocais._();

  Map<String, Visita> _porDiagnostico = {};
  bool _carregado = false;

  Visita? doDiagnostico(String diagnosticoId) => _porDiagnostico[diagnosticoId];

  Future<File> _ficheiro() async =>
      File(p.join((await getApplicationDocumentsDirectory()).path, 'visitas.json'));

  Future<void> carregar() async {
    if (_carregado) return;
    _carregado = true;
    final f = await _ficheiro();
    if (!await f.exists()) return;
    try {
      final lista = jsonDecode(await f.readAsString()) as List;
      _definir([for (final v in lista) Visita.fromJson(v as Map<String, dynamic>)]);
      notifyListeners();
    } catch (_) {}
  }

  void _definir(List<Visita> visitas) {
    // A API devolve as mais recentes primeiro: fica a mais recente de cada diagnóstico.
    _porDiagnostico = {};
    for (final v in visitas) {
      _porDiagnostico.putIfAbsent(v.diagnosticoId, () => v);
    }
  }

  /// Devolve quantas visitas mudaram de estado desde a última vez.
  Future<int> actualizar(List<Visita> daApi) async {
    final antes = {for (final v in _porDiagnostico.values) v.id: v.estado};
    _definir(daApi);
    await (await _ficheiro()).writeAsString(jsonEncode([for (final v in daApi) v.toJson()]));
    notifyListeners();
    return _porDiagnostico.values.where((v) => antes.containsKey(v.id) && antes[v.id] != v.estado).length;
  }

  /// Pede uma visita (precisa de rede; o diagnóstico tem de estar sincronizado).
  Future<Visita> pedir(String diagnosticoId, String? mensagem) async {
    final v = await ApiCliente.instancia.pedirVisita(diagnosticoId, mensagem);
    _porDiagnostico[diagnosticoId] = v;
    await (await _ficheiro())
        .writeAsString(jsonEncode([for (final x in _porDiagnostico.values) x.toJson()]));
    notifyListeners();
    return v;
  }

  Future<void> limpar() async {
    _porDiagnostico = {};
    final f = await _ficheiro();
    if (await f.exists()) await f.delete();
    notifyListeners();
  }
}
