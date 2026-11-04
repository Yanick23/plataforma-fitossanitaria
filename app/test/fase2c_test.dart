import 'package:agrodiagnostico/models/cultura.dart';
import 'package:agrodiagnostico/models/diagnostico.dart';
import 'package:agrodiagnostico/models/medicao_inferencia.dart';
import 'package:agrodiagnostico/models/patologia.dart';
import 'package:agrodiagnostico/models/resultado_classificacao.dart';
import 'package:flutter_test/flutter_test.dart';

const _classes = ['gafanhoto', 'lagarta_do_cartucho', 'saudavel'];

ResultadoClassificacao _foto(String caminho, List<double> p, {int versao = 2}) => ResultadoClassificacao(
      cultura: Cultura.milho,
      caminhoImagem: caminho,
      dataCaptura: DateTime(2026, 10, 25),
      classes: _classes,
      probabilidades: p,
      versaoModelo: versao,
      medicao: MedicaoInferencia(
          data: DateTime(2026, 10, 25), cultura: Cultura.milho, versaoModelo: versao, carregamentoModeloMs: 0,
          preProcessamentoMs: 50, inferenciaMs: 300, tempoTotalMs: 400, memoriaRssBytes: 0, memoriaMaxRssBytes: 0,
          tamanhoModeloBytes: 0, threads: 1),
    );

void main() {
  group('várias fotografias', () {
    test('a decisão é a média das probabilidades', () {
      // 1.ª foto: dúvida (55% gafanhoto); 2.ª: lagarta clara (90%).
      final r = _foto('a.jpg', [0.55, 0.40, 0.05]).juntar(_foto('b.jpg', [0.05, 0.90, 0.05]));
      expect(r.fotos, hasLength(2));
      expect(r.classe, 'lagarta_do_cartucho');
      expect(r.confianca, closeTo(0.65, 1e-9));
      expect(r.confiancaBaixa, isFalse);
      expect(r.caminhoImagem, 'b.jpg'); // a foto que mais mostra a classe final fica no diagnóstico
    });

    test('no máximo $maximoFotos fotografias', () {
      var r = _foto('a.jpg', [0.5, 0.4, 0.1]);
      expect(r.podeJuntarFoto, isTrue);
      r = r.juntar(_foto('b.jpg', [0.5, 0.4, 0.1])).juntar(_foto('c.jpg', [0.5, 0.4, 0.1]));
      expect(r.podeJuntarFoto, isFalse);
    });
  });

  group('seguimento do tratamento', () {
    Diagnostico base({Seguiu? seguiu, ResultadoTratamento? resultado, bool enviado = false}) => Diagnostico(
          id: 'x', utilizadorId: 1, data: DateTime(2026, 10, 10), cultura: Cultura.milho,
          classePrevista: 'lagarta_do_cartucho', confianca: 0.9,
          imagem: Imagem(caminhoFicheiro: 'x.jpg', dataCaptura: DateTime(2026, 10, 10)),
          versaoModelo: 1, tempoInferenciaMs: 300, tempoTotalMs: 400, estadoSinc: EstadoSinc.sincronizado,
          seguiu: seguiu, resultadoTratamento: resultado, seguimentoEnviado: enviado,
        );

    test('a resposta sobrevive à gravação no SQLite', () {
      final d = Diagnostico.fromMap(base(seguiu: Seguiu.parcial, resultado: ResultadoTratamento.melhorou).toMap());
      expect(d.seguiu, Seguiu.parcial);
      expect(d.resultadoTratamento, ResultadoTratamento.melhorou);
      expect(d.seguimentoRespondido, isTrue);
      expect(d.seguimentoEnviado, isFalse); // fica por enviar
    });

    test('linhas antigas (sem as colunas da versão 3) lêem-se sem resposta', () {
      final m = base().toMap()..remove('seguiu')..remove('resultado_tratamento')..remove('seguimento_enviado');
      final d = Diagnostico.fromMap(m);
      expect(d.seguimentoRespondido, isFalse);
    });

    test('respondido noutro telemóvel conta como respondido', () {
      expect(base(enviado: true).seguimentoRespondido, isTrue);
    });
  });

  test('o catálogo guarda sintomas, prevenção, validação e fotografias', () {
    final api = Patologia.daApi({
      'id': 5, 'cultura_id': 'milho', 'codigo': 'gafanhoto', 'nome_local': 'Gafanhoto', 'nome_cientifico': 'Acrididae',
      'tipo': 'PRAGA', 'recomendacao': 'Limpe as ervas.', 'sintomas': 'Bordos roídos.', 'prevencao': 'Lavrar cedo.',
      'validado_por_nome': 'Técnica de Boane',
      'fotos': [{'id': 3, 'legenda': 'Folha roída', 'url': '/fotos-referencia/3'}],
    });
    final local = Patologia.doCatalogo(Cultura.milho, 'gafanhoto', api.paraCatalogo());
    expect(local.sintomas, 'Bordos roídos.');
    expect(local.prevencao, 'Lavrar cedo.');
    expect(local.validado, isTrue);
    expect(local.fotos.single.url, '/fotos-referencia/3');
    expect(local.fotos.single.legenda, 'Folha roída');
  });
}
