import 'dart:convert';
import 'dart:io';

import 'package:flutter/services.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../models/cultura.dart';
import '../models/patologia.dart';
import 'api_cliente.dart';
import 'registo_tecnico.dart';

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
  Directory? _pastaFotos;

  Future<File> _ficheiroLocal() async =>
      File(p.join((await getApplicationDocumentsDirectory()).path, 'catalogo.json'));

  Future<void> carregar() async {
    _pastaFotos = Directory(p.join((await getApplicationDocumentsDirectory()).path, 'fotos_referencia'));
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

  /// Descarrega as fotografias de referência que faltam e apaga as que o painel removeu.
  /// Uma foto que falhe não interrompe a sincronização (fica para a próxima). Devolve quantas descarregou.
  Future<int> sincronizarFotos() async {
    final pasta = _pastaFotos;
    if (pasta == null) return 0;
    await pasta.create(recursive: true);
    final fotos = {for (final e in _entradas.values) for (final pat in e.values) for (final f in pat.fotos) f.id: f};
    var novas = 0;
    for (final f in fotos.values) {
      final destino = File(p.join(pasta.path, 'ref_${f.id}'));
      if (await destino.exists()) continue;
      try {
        await destino.writeAsBytes(await ApiCliente.instancia.descarregar(f.url), flush: true);
        novas++;
      } on ErroApi catch (e) {
        RegistoTecnico.instancia.escrever('foto de referência ${f.id} não descarregada: ${e.mensagem}');
      }
    }
    await for (final f in pasta.list()) {
      final id = int.tryParse(p.basename(f.path).replaceFirst('ref_', ''));
      if (id != null && !fotos.containsKey(id)) await f.delete();
    }
    return novas;
  }

  /// O ficheiro local da fotografia, se já foi descarregada.
  File? ficheiroFoto(FotoReferencia f) {
    final pasta = _pastaFotos;
    if (pasta == null) return null;
    final ficheiro = File(p.join(pasta.path, 'ref_${f.id}'));
    return ficheiro.existsSync() ? ficheiro : null;
  }

  Patologia patologia(Cultura cultura, String codigo) =>
      _entradas[cultura]?[codigo] ?? Patologia.desconhecida(cultura, codigo);
}
