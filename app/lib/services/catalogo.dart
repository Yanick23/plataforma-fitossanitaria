import 'dart:convert';
import 'dart:io';

import 'package:flutter/services.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../models/cultura.dart';
import '../models/patologia.dart';

/// Catálogo de patologias: nome local, nome científico e recomendação (RF06, RF07).
///
/// Começa pelo assets/catalogo.json embutido; quando a sincronização traz uma
/// versão da API (GET /patologias), essa passa a ser usada e fica guardada
/// em documentos/catalogo.json para funcionar offline.
class Catalogo {
  Catalogo._();
  static final instancia = Catalogo._();

  final Map<Cultura, Map<String, Patologia>> _entradas = {};
  String aviso = '';

  Future<File> _ficheiroLocal() async =>
      File(p.join((await getApplicationDocumentsDirectory()).path, 'catalogo.json'));

  Future<void> carregar() async {
    final embutido = jsonDecode(await rootBundle.loadString('assets/catalogo.json')) as Map<String, dynamic>;
    aviso = embutido['aviso'] as String? ?? '';
    _preencher(embutido);
    final local = await _ficheiroLocal();
    if (await local.exists()) {
      _preencher(jsonDecode(await local.readAsString()) as Map<String, dynamic>);
    }
  }

  void _preencher(Map<String, dynamic> json) {
    for (final cultura in Cultura.values) {
      final entradas = json[cultura.id] as Map<String, dynamic>?;
      if (entradas == null) continue;
      _entradas[cultura] = {
        for (final MapEntry(:key, :value) in entradas.entries)
          key: Patologia.doCatalogo(cultura, key, value as Map<String, dynamic>),
      };
    }
  }

  /// Substitui o catálogo pelo da API e guarda-o localmente.
  Future<void> actualizar(List<Patologia> patologias) async {
    if (patologias.isEmpty) return;
    final json = <String, dynamic>{};
    for (final pat in patologias) {
      (json[pat.cultura.id] ??= <String, dynamic>{})[pat.codigo] = pat.paraCatalogo();
    }
    _preencher(json);
    await (await _ficheiroLocal()).writeAsString(jsonEncode(json));
  }

  Patologia patologia(Cultura cultura, String codigo) =>
      _entradas[cultura]?[codigo] ?? Patologia.desconhecida(cultura, codigo);
}
