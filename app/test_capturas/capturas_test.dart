// Gera capturas dos ecrãs da app (para rever o desenho e para a tese), sem telemóvel.
//
//   flutter test test_capturas --update-goldens
//
// As imagens ficam em test_capturas/capturas/. Usa as letras reais (IBM Plex Sans e os ícones
// Material), dados de exemplo e simula o armazenamento e a rede. Não corre com `flutter test`
// (fica fora de test/), porque depende das letras do SDK do Flutter desta máquina.
// ignore_for_file: depend_on_referenced_packages, invalid_use_of_visible_for_testing_member

import 'dart:io';
import 'dart:ui' show instantiateImageCodec;

import 'package:agrodiagnostico/main.dart';
import 'package:agrodiagnostico/models/alerta.dart';
import 'package:agrodiagnostico/models/calendario.dart';
import 'package:agrodiagnostico/models/campanha.dart';
import 'package:agrodiagnostico/models/cultura.dart';
import 'package:agrodiagnostico/models/diagnostico.dart';
import 'package:agrodiagnostico/models/medicao_inferencia.dart';
import 'package:agrodiagnostico/models/resultado_classificacao.dart';
import 'package:agrodiagnostico/models/utilizador.dart';
import 'package:agrodiagnostico/screens/alertas_screen.dart';
import 'package:agrodiagnostico/screens/cultura_screen.dart';
import 'package:agrodiagnostico/screens/definicoes_screen.dart';
import 'package:agrodiagnostico/screens/historial_screen.dart';
import 'package:agrodiagnostico/screens/inicio_screen.dart';
import 'package:agrodiagnostico/screens/login_screen.dart';
import 'package:agrodiagnostico/screens/resultado_screen.dart';
import 'package:agrodiagnostico/services/alertas_locais.dart';
import 'package:agrodiagnostico/services/catalogo.dart';
import 'package:agrodiagnostico/services/dados_zona.dart';
import 'package:agrodiagnostico/services/sessao.dart';
import 'package:agrodiagnostico/services/vozes_locais.dart';
import 'package:agrodiagnostico/tema.dart';
import 'package:connectivity_plus_platform_interface/connectivity_plus_platform_interface.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;
import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';
import 'package:plugin_platform_interface/plugin_platform_interface.dart';

final _pasta = Directory.systemTemp.createTempSync('capturas_app_');

class _Caminhos extends Fake with MockPlatformInterfaceMixin implements PathProviderPlatform {
  @override
  Future<String?> getApplicationDocumentsPath() async => _pasta.path;
  @override
  Future<String?> getTemporaryPath() async => _pasta.path;
  @override
  Future<String?> getApplicationSupportPath() async => _pasta.path;
}

class _Rede extends Fake with MockPlatformInterfaceMixin implements ConnectivityPlatform {
  @override
  Future<List<ConnectivityResult>> checkConnectivity() async => [ConnectivityResult.wifi];
  @override
  Stream<List<ConnectivityResult>> get onConnectivityChanged => const Stream.empty();
}

Future<void> _letra(String familia, List<String> ficheiros) async {
  final l = FontLoader(familia);
  for (final f in ficheiros) {
    l.addFont(File(f).readAsBytes().then((b) => ByteData.view(b.buffer)));
  }
  await l.load();
}

/// Uma «folha» de exemplo: verde com nervuras e manchas, só para ocupar o lugar da fotografia.
String _fotoExemplo(String nome, {bool manchas = true}) {
  final im = img.Image(width: 640, height: 400);
  for (var y = 0; y < 400; y++) {
    for (var x = 0; x < 640; x++) {
      final nervura = ((x - 320).abs() < 3 || ((x - 320).abs() - (y - 200).abs() ~/ 2).abs() < 2) ? 30 : 0;
      final mancha = manchas && ((x - 200) * (x - 200) + (y - 140) * (y - 140) < 900 ||
              (x - 430) * (x - 430) + (y - 260) * (y - 260) < 1400)
          ? 1
          : 0;
      im.setPixelRgb(x, y, mancha == 1 ? 150 : 60 + nervura + y ~/ 20, mancha == 1 ? 120 : 120 + nervura + x ~/ 30,
          mancha == 1 ? 50 : 40);
    }
  }
  final f = File('${_pasta.path}/$nome.jpg')..writeAsBytesSync(img.encodeJpg(im));
  return f.path;
}

ResultadoClassificacao _resultado(String classe, double confianca, String foto) {
  const classes = ['lagarta_do_cartucho', 'queima_da_folha', 'saudavel'];
  final p = [for (final c in classes) c == classe ? confianca : (1 - confianca) / 2];
  return ResultadoClassificacao(
    cultura: Cultura.milho,
    caminhoImagem: foto,
    dataCaptura: DateTime(2026, 11, 8, 9, 12),
    classes: classes,
    probabilidades: p,
    versaoModelo: 2,
    medicao: MedicaoInferencia(
      data: DateTime(2026, 11, 8, 9, 12),
      cultura: Cultura.milho,
      versaoModelo: 2,
      carregamentoModeloMs: 120,
      preProcessamentoMs: 40,
      inferenciaMs: 172,
      tempoTotalMs: 412,
      memoriaRssBytes: 0,
      memoriaMaxRssBytes: 0,
      tamanhoModeloBytes: 4560000,
      threads: 4,
    ),
  );
}

void main() {
  setUpAll(() async {
    PathProviderPlatform.instance = _Caminhos();
    ConnectivityPlatform.instance = _Rede();
    const sdk = '/home/yanick/Apps/flutter/bin/cache/artifacts/material_fonts';
    await _letra('IBMPlexSans', [
      for (final p in ['Regular', 'Medium', 'SemiBold', 'Bold', 'Italic']) 'assets/fonts/IBMPlexSans-$p.ttf',
    ]);
    await _letra('MaterialIcons', ['$sdk/MaterialIcons-Regular.otf']);
    await _letra('Roboto', [for (final p in ['Regular', 'Medium', 'Bold', 'Italic']) '$sdk/Roboto-$p.ttf']);

    Sessao.instancia.utilizador.value = const Utilizador(
        id: 3, nome: 'Ana Machava', telefone: '842000000', perfil: Perfil.agricultor, area: 'Boane', lingua: 'tso');
    await Catalogo.instancia.carregar();
    await VozesLocais.instancia.carregar();
    await AlertasLocais.instancia.actualizar([
      Alerta.fromJson({
        'id': 7,
        'titulo': 'Lagarta-do-funil nas machambas de Boane',
        'mensagem': 'Foram confirmados casos esta semana. Veja o funil das plantas novas e esmague as lagartas.',
        'nivel': 'URGENTE',
        'zona': 'Distrito de Boane',
        'criado_em': '2026-11-08T07:30:00Z',
        'cultura_id': 'milho',
        'patologia_codigo': 'lagarta_do_cartucho',
      }),
      Alerta.fromJson({
        'id': 6,
        'titulo': 'Chuvas fortes previstas',
        'mensagem': 'Evite aplicar produtos antes da chuva.',
        'nivel': 'INFORMACAO',
        'zona': 'Província de Maputo',
        'criado_em': '2026-11-05T10:00:00Z',
        'lido': true,
      }),
    ]);
    await CampanhasLocais.instancia.actualizar([
      Campanha.fromJson({
        'id': 2,
        'titulo': 'Vigilância da lagarta-do-funil',
        'mensagem': 'Fotografe 3 plantas de milho da sua machamba esta semana.',
        'cultura_id': 'milho',
        'zona': 'Distrito de Boane',
        'inicio': '2026-11-05',
        'fim': '2026-11-20',
        'patologia_codigo': 'lagarta_do_cartucho',
        'respondeu': false,
      }),
    ]);
    await CalendarioLocal.instancia.actualizar(Calendario.fromJson({
      'provincia_codigo': 'MZ-L',
      'provincia': 'Maputo',
      'regiao': 'Centro e Sul',
      'sementeira': '2.ª década de Novembro',
      'aviso': 'Calendário geral.',
      'meses': [
        for (var m = 1; m <= 12; m++)
          {
            'mes': m,
            'actividades': m == 11 ? ['Sementeira do milho', 'Sacha'] : <String>[],
            'avisos': m == 11
                ? [
                    {
                      'cultura_id': 'milho',
                      'classe': 'lagarta_do_cartucho',
                      'patologia_nome': 'Lagarta-do-funil',
                      'texto': 'Nas plantas novas, veja o funil duas vezes por semana.',
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
    }));
  });

  Future<void> capturar(WidgetTester tester, String nome, Widget ecra, {List<String> fotos = const []}) async {
    tester.view.physicalSize = const Size(412 * 2.5, 915 * 2.5);
    tester.view.devicePixelRatio = 2.5;
    addTearDown(tester.view.reset);
    // O FileImage não lê ficheiros no ambiente de teste: antes de desenhar, põe-se a imagem já
    // descodificada na cache, com as chaves que os ecrãs usam (inteira e reduzida nas miniaturas).
    await tester.runAsync(() async {
      for (final f in fotos) {
        final codec = await instantiateImageCodec(await File(f).readAsBytes());
        final quadro = await codec.getNextFrame();
        final original = FileImage(File(f));
        for (final chave in <Object>[original, for (final w in [112, 156, 256]) ResizeImage(original, width: w)]) {
          PaintingBinding.instance.imageCache
              .putIfAbsent(chave, () => OneFrameImageStreamCompleter(Future.value(ImageInfo(image: quadro.image.clone()))));
        }
      }
    });
    await tester.pumpWidget(MaterialApp(debugShowCheckedModeBanner: false, theme: criarTema(), home: ecra));
    for (var i = 0; i < 6; i++) {
      await tester.pump(const Duration(milliseconds: 200));
    }
    await expectLater(find.byType(MaterialApp), matchesGoldenFile('capturas/$nome.png'));
  }

  testWidgets('01 entrar', (t) => capturar(t, '01_entrar', const LoginScreen()));

  testWidgets('02 início', (t) => capturar(
      t,
      '02_inicio',
      Scaffold(
        body: const InicioScreen(),
        bottomNavigationBar: BarraNavegacao(aba: 0, aoEscolher: (_) {}),
      )));

  testWidgets('03 cultura', (t) => capturar(t, '03_cultura', const CulturaScreen()));

  testWidgets('04 resultado', (t) async {
    final foto = _fotoExemplo('folha');
    await capturar(t, '04_resultado', ResultadoScreen(resultado: _resultado('lagarta_do_cartucho', 0.87, foto)),
        fotos: [foto]);
  });

  testWidgets('05 resultado com dúvida', (t) async {
    final foto = _fotoExemplo('folha2', manchas: false);
    await capturar(t, '05_resultado_duvida', ResultadoScreen(resultado: _resultado('queima_da_folha', 0.48, foto)),
        fotos: [foto]);
  });

  testWidgets('06 historial', (t) async {
    final foto = _fotoExemplo('folha3');
    Diagnostico d(String id, String classe, double conf, int dias, {Validacao v = Validacao.pendente, bool sinc = true}) =>
        Diagnostico(
          id: id,
          utilizadorId: 3,
          data: DateTime(2026, 11, 8, 9).subtract(Duration(days: dias)),
          cultura: classe == 'mosaico' ? Cultura.mandioca : Cultura.milho,
          classePrevista: classe,
          confianca: conf,
          imagem: Imagem(caminhoFicheiro: foto, dataCaptura: DateTime(2026, 11, 8)),
          versaoModelo: 2,
          tempoInferenciaMs: 170,
          tempoTotalMs: 410,
          estadoSinc: sinc ? EstadoSinc.sincronizado : EstadoSinc.pendente,
          validacao: v,
        );
    await capturar(
        t,
        '06_historial',
        Scaffold(
          body: SafeArea(
            child: ListaHistorial(
              itens: [
                d('a', 'lagarta_do_cartucho', 0.87, 0, sinc: false),
                d('b', 'mosaico', 0.93, 2, v: Validacao.confirmado),
                d('c', 'queima_da_folha', 0.58, 5, v: Validacao.corrigido),
                d('d', 'saudavel', 0.97, 9),
              ],
            ),
          ),
          bottomNavigationBar: BarraNavegacao(aba: 1, aoEscolher: (_) {}),
        ),
        fotos: [foto]);
  });

  testWidgets('07 alertas', (t) => capturar(t, '07_alertas', const AlertasScreen()));

  testWidgets('08 definições', (t) => capturar(t, '08_definicoes', const DefinicoesScreen()));
}
