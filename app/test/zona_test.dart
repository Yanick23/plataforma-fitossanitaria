import 'package:agrodiagnostico/models/calendario.dart';
import 'package:agrodiagnostico/models/campanha.dart';
import 'package:agrodiagnostico/models/cultura.dart';
import 'package:agrodiagnostico/services/notificacoes_fundo.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('notificações a partir de /novidades', () {
    test('sem novidades não há notificações', () {
      expect(notificacoesDe({'agora': '2026-11-08T10:00:00Z', 'alertas': [], 'validacoes': [], 'visitas': [], 'campanhas': []}),
          isEmpty);
    });

    test('um texto por alerta, visita e campanha; as validações juntam-se numa só', () {
      final n = notificacoesDe({
        'agora': '2026-11-08T10:00:00Z',
        'alertas': [
          {'id': 7, 'titulo': 'Lagarta em Mocuba', 'nivel': 'URGENTE'},
          {'id': 8, 'titulo': 'Chuva forte', 'nivel': 'INFORMACAO'},
        ],
        'validacoes': [
          {'diagnostico_id': 'a', 'classe_confirmada': 'mosaico', 'correcto': true},
          {'diagnostico_id': 'b', 'classe_confirmada': 'queima_da_folha', 'correcto': false},
        ],
        'visitas': [
          {'id': 3, 'estado': 'AGENDADA', 'data_agendada': '2026-11-12T08:00:00Z'},
          {'id': 4, 'estado': 'RESOLVIDA', 'data_agendada': null},
        ],
        'campanhas': [
          {'id': 2, 'titulo': 'Vigilância da lagarta', 'fim': '2026-11-15'},
        ],
      });
      expect(n.map((x) => x.titulo), [
        'Alerta urgente: Lagarta em Mocuba',
        'Alerta: Chuva forte',
        'O técnico reviu 2 diagnósticos',
        'Visita técnica agendada',
        'Visita técnica resolvida',
        'Campanha na sua zona: Vigilância da lagarta',
      ]);
      expect(n[2].corpo, contains('1 corrigido'));
      expect(n[3].corpo, contains('12/11'));
      expect(n[5].corpo, contains('Até 15/11'));
      // Ids diferentes por tipo: um alerta não substitui a notificação de uma visita
      expect(n.map((x) => x.id).toSet().length, n.length);
    });

    test('uma validação confirmada', () {
      final n = notificacoesDe({
        'validacoes': [
          {'diagnostico_id': 'a', 'classe_confirmada': 'mosaico', 'correcto': true},
        ],
      });
      expect(n.single.titulo, 'O técnico reviu o seu diagnóstico');
      expect(n.single.corpo, startsWith('Confirmado'));
    });
  });

  group('calendário agrícola', () {
    final json = {
      'provincia_codigo': 'MZ-Q',
      'provincia': 'Zambézia',
      'regiao': 'Centro e Sul',
      'sementeira': '3.ª década de Novembro (estação de Quelimane)',
      'aviso': 'Calendário geral.',
      'meses': [
        for (var m = 1; m <= 12; m++)
          {
            'mes': m,
            'actividades': m == 11 ? ['Sementeira principal'] : <String>[],
            'avisos': m == 11
                ? [
                    {
                      'cultura_id': 'milho',
                      'classe': 'lagarta_do_cartucho',
                      'patologia_nome': 'Lagarta-do-funil',
                      'texto': 'Veja o funil.',
                      'confianca': 'alta',
                      'fontes': ['MASA2018'],
                    },
                  ]
                : [],
          },
      ],
      'fontes': [
        {'id': 'MASA2018', 'referencia': 'MASA (2018)', 'url': null},
      ],
    };

    test('lê o mês pedido e volta igual depois de guardado', () {
      final c = Calendario.fromJson(json);
      expect(c.mes(11).actividades, ['Sementeira principal']);
      expect(c.mes(11).avisos.single.fontes, ['MASA2018']);
      expect(c.mes(3).avisos, isEmpty);
      final outra = Calendario.fromJson(c.toJson());
      expect(outra.mes(11).avisos.single.texto, 'Veja o funil.');
      expect(outra.fontes['MASA2018'], 'MASA (2018)');
    });
  });

  group('campanhas', () {
    Campanha campanha({String cultura = 'milho', bool respondeu = false}) => Campanha.fromJson({
      'id': 1,
      'titulo': 'Vigilância',
      'mensagem': 'Fotografe 3 plantas.',
      'cultura_id': cultura,
      'zona': 'Distrito de Mocuba',
      'inicio': '2026-11-05',
      'fim': '2026-11-12',
      'patologia_codigo': null,
      'respondeu': respondeu,
    });

    test('decorre do início ao fim, inclusive', () {
      final c = campanha();
      expect(c.decorre(DateTime(2026, 11, 4, 23)), isFalse);
      expect(c.decorre(DateTime(2026, 11, 5, 0, 1)), isTrue);
      expect(c.decorre(DateTime(2026, 11, 12, 23, 59)), isTrue);
      expect(c.decorre(DateTime(2026, 11, 13)), isFalse);
    });

    test('guardada e lida de novo, e marcada como respondida', () {
      final c = Campanha.fromJson(campanha().toJson());
      expect(c.fim, DateTime(2026, 11, 12));
      expect(c.respondeu, isFalse);
      expect(c.comRespondeu().respondeu, isTrue);
    });

    test('uma cultura que a app não diagnostica não falha', () {
      expect(Cultura.talvez('feijao'), isNull);
      expect(Cultura.nomeDe('feijao'), 'Feijao');
      expect(Cultura.nomeDe('milho'), 'Milho');
    });
  });
}
