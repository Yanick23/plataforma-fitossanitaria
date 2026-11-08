import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../models/calendario.dart';
import '../models/campanha.dart';

Future<File> _ficheiro(String nome) async => File(p.join((await getApplicationDocumentsDirectory()).path, nome));

/// Campanhas de vigilância da zona (chegam na sincronização; lêem-se sem rede).
class CampanhasLocais extends ChangeNotifier {
  CampanhasLocais._();
  static final instancia = CampanhasLocais._();

  List<Campanha> _campanhas = [];
  bool _carregado = false;

  /// Campanhas a decorrer hoje, as que ainda não teve resposta primeiro.
  List<Campanha> get activas {
    final agora = DateTime.now();
    return _campanhas.where((c) => c.decorre(agora)).toList()
      ..sort((a, b) => a.respondeu == b.respondeu ? a.fim.compareTo(b.fim) : (a.respondeu ? 1 : -1));
  }

  Future<void> carregar() async {
    if (_carregado) return;
    _carregado = true;
    final f = await _ficheiro('campanhas.json');
    if (!await f.exists()) return;
    try {
      _campanhas = [
        for (final c in (jsonDecode(await f.readAsString()) as List).cast<Map<String, dynamic>>()) Campanha.fromJson(c),
      ];
      notifyListeners();
    } catch (_) {
      // Ficheiro corrompido: a próxima sincronização repõe as campanhas.
    }
  }

  /// Substitui pelas campanhas activas vindas da API; devolve quantas são novas.
  Future<int> actualizar(List<Campanha> daApi) async {
    final conhecidas = {for (final c in _campanhas) c.id};
    _campanhas = daApi;
    await (await _ficheiro('campanhas.json')).writeAsString(jsonEncode([for (final c in daApi) c.toJson()]));
    notifyListeners();
    return daApi.where((c) => !conhecidas.contains(c.id)).length;
  }

  /// Depois de guardar um diagnóstico desta cultura: a campanha passa a «respondida» no ecrã,
  /// antes mesmo de sincronizar (a API confirma na sincronização seguinte).
  Future<void> diagnosticoFeito(String culturaId) async {
    final agora = DateTime.now();
    bool responde(Campanha c) => !c.respondeu && c.culturaId == culturaId && c.decorre(agora);
    if (!_campanhas.any(responde)) return;
    _campanhas = [for (final c in _campanhas) responde(c) ? c.comRespondeu() : c];
    await (await _ficheiro('campanhas.json')).writeAsString(jsonEncode([for (final c in _campanhas) c.toJson()]));
    notifyListeners();
  }

  Future<void> limpar() async {
    _campanhas = [];
    final f = await _ficheiro('campanhas.json');
    if (await f.exists()) await f.delete();
    notifyListeners();
  }
}

/// Calendário agrícola da província do agricultor (funcionalidade 10), para «Nesta altura…».
class CalendarioLocal extends ChangeNotifier {
  CalendarioLocal._();
  static final instancia = CalendarioLocal._();

  Calendario? calendario;
  bool _carregado = false;

  Future<void> carregar() async {
    if (_carregado) return;
    _carregado = true;
    final f = await _ficheiro('calendario.json');
    if (!await f.exists()) return;
    try {
      calendario = Calendario.fromJson(jsonDecode(await f.readAsString()) as Map<String, dynamic>);
      notifyListeners();
    } catch (_) {}
  }

  Future<void> actualizar(Calendario c) async {
    calendario = c;
    await (await _ficheiro('calendario.json')).writeAsString(jsonEncode(c.toJson()));
    notifyListeners();
  }

  Future<void> limpar() async {
    calendario = null;
    final f = await _ficheiro('calendario.json');
    if (await f.exists()) await f.delete();
    notifyListeners();
  }
}
