import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../models/alerta.dart';

/// Alertas da zona do agricultor, guardados no telemóvel para se lerem sem rede.
///
/// Chegam na sincronização (GET /alertas/meus). Marcar como lido funciona
/// offline: o id fica numa fila e é enviado à API na sincronização seguinte.
class AlertasLocais extends ChangeNotifier {
  AlertasLocais._();
  static final instancia = AlertasLocais._();

  List<Alerta> _alertas = [];
  Set<int> _lidosPorEnviar = {};
  bool _carregado = false;

  List<Alerta> get alertas => _alertas.where((a) => !a.expirado).toList();
  int get naoLidos => alertas.where((a) => !a.lido).length;
  Alerta? get ultimoNaoLido => alertas.where((a) => !a.lido).firstOrNull;
  Set<int> get lidosPorEnviar => Set.unmodifiable(_lidosPorEnviar);

  Future<File> _ficheiro() async =>
      File(p.join((await getApplicationDocumentsDirectory()).path, 'alertas.json'));

  Future<void> carregar() async {
    if (_carregado) return;
    _carregado = true;
    final f = await _ficheiro();
    if (!await f.exists()) return;
    try {
      final j = jsonDecode(await f.readAsString()) as Map<String, dynamic>;
      _alertas = [for (final a in j['alertas'] as List) Alerta.fromJson(a as Map<String, dynamic>)];
      _lidosPorEnviar = {for (final id in j['lidos_por_enviar'] as List? ?? []) id as int};
      notifyListeners();
    } catch (_) {
      // Ficheiro corrompido: recomeça vazio; a próxima sincronização repõe os alertas.
    }
  }

  Future<void> _gravar() async => (await _ficheiro()).writeAsString(jsonEncode({
        'alertas': [for (final a in _alertas) a.toJson()],
        'lidos_por_enviar': _lidosPorEnviar.toList(),
      }));

  /// Substitui pelos alertas activos vindos da API. Mantém como lidos os que o
  /// agricultor já abriu no telemóvel e ainda não foram confirmados pela API.
  /// Devolve quantos alertas são novos.
  Future<int> actualizar(List<Alerta> daApi) async {
    final conhecidos = {for (final a in _alertas) a.id};
    _alertas = [for (final a in daApi) _lidosPorEnviar.contains(a.id) ? a.comLido(true) : a]
      ..sort((a, b) => b.criadoEm.compareTo(a.criadoEm));
    await _gravar();
    notifyListeners();
    return daApi.where((a) => !conhecidos.contains(a.id)).length;
  }

  Future<void> marcarLido(int id) async {
    final i = _alertas.indexWhere((a) => a.id == id);
    if (i < 0 || _alertas[i].lido) return;
    _alertas[i] = _alertas[i].comLido(true);
    _lidosPorEnviar.add(id);
    await _gravar();
    notifyListeners();
  }

  /// Chamado pela sincronização depois de a API registar a leitura.
  Future<void> leituraConfirmada(int id) async {
    if (_lidosPorEnviar.remove(id)) await _gravar();
  }

  /// Ao terminar a sessão: os alertas pertencem à zona da conta.
  Future<void> limpar() async {
    _alertas = [];
    _lidosPorEnviar = {};
    final f = await _ficheiro();
    if (await f.exists()) await f.delete();
    notifyListeners();
  }
}
