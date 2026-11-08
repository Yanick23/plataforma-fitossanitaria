import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../models/audio.dart';
import 'api_cliente.dart';
import 'registo_tecnico.dart';

/// Gravações de voz no telemóvel (funcionalidade 14), para ouvir sem rede.
///
/// Só se descarregam as da língua do agricultor e as em português (para quando ainda não há
/// gravação na língua dele). As vezes que cada uma é ouvida contam-se aqui, mesmo sem rede,
/// e vão para a API na sincronização seguinte.
class VozesLocais extends ChangeNotifier {
  VozesLocais._();
  static final instancia = VozesLocais._();

  Directory? _pasta;
  Map<int, int> _reproducoes = {};

  Future<File> _ficheiroReproducoes() async =>
      File(p.join((await getApplicationDocumentsDirectory()).path, 'reproducoes_audio.json'));

  Future<void> carregar() async {
    _pasta = Directory(p.join((await getApplicationDocumentsDirectory()).path, 'audio'));
    final f = await _ficheiroReproducoes();
    if (await f.exists()) {
      try {
        _reproducoes = {
          for (final e in (jsonDecode(await f.readAsString()) as Map<String, dynamic>).entries)
            int.parse(e.key): e.value as int,
        };
      } catch (_) {
        _reproducoes = {}; // ficheiro estragado: perde-se só a contagem
      }
    }
  }

  /// As gravações que devem estar no telemóvel de quem escolheu [lingua].
  static List<AudioVoz> necessarias(Iterable<AudioVoz> todas, String? lingua) => lingua == null
      ? const []
      : [for (final a in todas) if (a.lingua == lingua || a.lingua == Lingua.portugues.codigo) a];

  /// Descarrega as que faltam e apaga as que já não servem (gravação substituída, apagada ou
  /// de outra língua). Uma que falhe fica para a próxima sincronização. Devolve quantas descarregou.
  Future<int> sincronizar(Iterable<AudioVoz> todas, String? lingua) async {
    final pasta = _pasta;
    if (pasta == null) return 0;
    await pasta.create(recursive: true);
    final precisas = {for (final a in necessarias(todas, lingua)) a.ficheiro: a};
    var novas = 0;
    for (final a in precisas.values) {
      final destino = File(p.join(pasta.path, a.ficheiro));
      if (await destino.exists()) continue;
      try {
        await destino.writeAsBytes(await ApiCliente.instancia.descarregar(a.url), flush: true);
        novas++;
      } on ErroApi catch (e) {
        RegistoTecnico.instancia.escrever('áudio ${a.ficheiro} não descarregado: ${e.mensagem}');
      }
    }
    await for (final f in pasta.list()) {
      if (!precisas.containsKey(p.basename(f.path))) await f.delete();
    }
    if (novas > 0) notifyListeners();
    return novas;
  }

  File? ficheiro(AudioVoz a) {
    final pasta = _pasta;
    if (pasta == null) return null;
    final f = File(p.join(pasta.path, a.ficheiro));
    return f.existsSync() ? f : null;
  }

  /// A gravação a tocar: na língua do agricultor ou, se faltar, em português — desde que já
  /// esteja no telemóvel.
  AudioVoz? paraOuvir(List<AudioVoz> audios, String? lingua) =>
      AudioVoz.escolher([for (final a in audios) if (ficheiro(a) != null) a], lingua);

  Future<void> ouvida(AudioVoz a) async {
    _reproducoes[a.id] = (_reproducoes[a.id] ?? 0) + 1;
    await _guardarReproducoes();
  }

  /// Envia as contagens e só as apaga depois de a API as aceitar.
  Future<void> enviarReproducoes() async {
    if (_reproducoes.isEmpty) return;
    final enviar = Map<int, int>.of(_reproducoes);
    await ApiCliente.instancia.enviarReproducoes(enviar);
    for (final e in enviar.entries) {
      final resto = (_reproducoes[e.key] ?? 0) - e.value;
      if (resto > 0) {
        _reproducoes[e.key] = resto;
      } else {
        _reproducoes.remove(e.key);
      }
    }
    await _guardarReproducoes();
  }

  Future<void> _guardarReproducoes() async => (await _ficheiroReproducoes())
      .writeAsString(jsonEncode({for (final e in _reproducoes.entries) '${e.key}': e.value}));
}
