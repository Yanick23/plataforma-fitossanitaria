import 'package:agrodiagnostico/models/alerta.dart';
import 'package:agrodiagnostico/models/audio.dart';
import 'package:agrodiagnostico/models/cultura.dart';
import 'package:agrodiagnostico/models/patologia.dart';
import 'package:agrodiagnostico/models/utilizador.dart';
import 'package:agrodiagnostico/services/vozes_locais.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> audio(int id, String lingua) => {
      'id': id,
      'lingua': lingua,
      'lingua_nome': Lingua.nomeDe(lingua),
      'url': '/audios/ficheiros/p7_${lingua}_abc$id.webm',
      'duracao_s': 12.5,
      'tipo_mime': 'audio/webm',
    };

void main() {
  group('escolher a gravação a tocar', () {
    final audios = [AudioVoz.fromJson(audio(1, 'por')), AudioVoz.fromJson(audio(2, 'tso'))];

    test('na língua do agricultor', () {
      expect(AudioVoz.escolher(audios, 'tso')!.id, 2);
    });

    test('em português quando falta a da língua dele', () {
      expect(AudioVoz.escolher(audios, 'vmw')!.id, 1);
    });

    test('nenhuma sem língua escolhida, ou sem gravação nem em português', () {
      expect(AudioVoz.escolher(audios, null), isNull);
      expect(AudioVoz.escolher([AudioVoz.fromJson(audio(3, 'seh'))], 'vmw'), isNull);
    });

    test('só se descarregam as da língua dele e as em português', () {
      final todas = [...audios, AudioVoz.fromJson(audio(3, 'seh'))];
      expect(VozesLocais.necessarias(todas, 'tso').map((a) => a.id), [1, 2]);
      expect(VozesLocais.necessarias(todas, null), isEmpty);
    });

    test('o ficheiro local é o nome único do url', () {
      expect(audios[1].ficheiro, 'p7_tso_abc2.webm');
      expect(audios[1].nomeLingua, 'Xichangana');
    });
  });

  test('a praga do catálogo guarda as gravações (API → ficheiro local → leitura)', () {
    final p = Patologia.daApi({
      'id': 7,
      'cultura_id': 'milho',
      'codigo': 'lagarta_do_cartucho',
      'nome_local': 'Lagarta-do-funil',
      'nome_cientifico': 'Spodoptera frugiperda',
      'tipo': 'PRAGA',
      'recomendacao': 'Veja o funil.',
      'validado_por_nome': 'Ana',
      'fotos': [],
      'audios': [audio(2, 'tso')],
    });
    final local = Patologia.doCatalogo(Cultura.milho, p.codigo, p.paraCatalogo());
    expect(local.audios.single.lingua, 'tso');
    expect(local.audios.single.duracaoS, 12.5);
    // Um catálogo guardado por uma versão anterior da app não tem «audios»
    final antigo = Map<String, dynamic>.of(p.paraCatalogo())..remove('audios');
    expect(Patologia.doCatalogo(Cultura.milho, p.codigo, antigo).audios, isEmpty);
  });

  test('o alerta guarda a mensagem de voz e mantém-na ao marcar como lido', () {
    final a = Alerta.fromJson({
      'id': 4,
      'titulo': 'Lagarta',
      'mensagem': 'Veja o funil.',
      'nivel': 'AVISO',
      'zona': 'Distrito de Boane',
      'criado_em': '2026-11-08T10:00:00Z',
      'audios': [audio(9, 'rng')],
    });
    expect(Alerta.fromJson(a.toJson()).audios.single.lingua, 'rng');
    expect(a.comLido(true).audios, hasLength(1));
  });

  test('a língua da conta é guardada e pode ser mudada', () {
    final u = Utilizador.fromJson({'id': 1, 'nome': 'Ana', 'telefone': '842000000', 'perfil': 'AGRICULTOR', 'lingua': 'tso'});
    expect(Utilizador.fromJson(u.toJson()).lingua, 'tso');
    expect(u.comLingua(null).lingua, isNull);
    expect(u.comLingua('vmw').nome, 'Ana');
  });
}
