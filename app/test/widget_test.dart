import 'package:agrodiagnostico/models/cultura.dart';
import 'package:agrodiagnostico/models/diagnostico.dart';
import 'package:agrodiagnostico/models/patologia.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('o catálogo embutido e a API usam o mesmo tipo de patologia', () {
    final p = Patologia.doCatalogo(Cultura.mandioca, 'mosaico', {
      'nome_local': 'Mosaico da mandioca',
      'nome_cientifico': 'Begomovírus',
      'tipo': 'doenca',
      'recomendacao': 'Arranque as plantas.',
    });
    expect(p.tipo, TipoPatologia.doenca);
    expect(p.paraCatalogo()['tipo'], 'DOENCA');
    expect(p.rotuloTipo, 'Doença detectada');
  });

  test('o diagnóstico vai para a API com o UUID e volta igual da base de dados', () {
    final d = Diagnostico(
      id: '3f1c2b9e-1111-4c2b-9a2e-123456789abc',
      utilizadorId: 7,
      data: DateTime.utc(2026, 10, 10, 9, 30),
      cultura: Cultura.milho,
      classePrevista: 'lagarta_do_cartucho',
      confianca: 0.93,
      imagem: Imagem(caminhoFicheiro: '/x.jpg', dataCaptura: DateTime.utc(2026, 10, 10, 9, 29)),
      versaoModelo: 1,
      tempoInferenciaMs: 210,
      tempoTotalMs: 640,
    );
    expect(d.paraApi()['id'], d.id);
    expect(d.estadoSinc, EstadoSinc.pendente);
    final copia = Diagnostico.fromMap(d.toMap());
    expect(copia.classePrevista, d.classePrevista);
    expect(copia.imagemEnviada, isFalse);
  });
}
