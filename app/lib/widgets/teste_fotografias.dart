import 'dart:io';

import 'package:flutter/material.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../models/cultura.dart';
import '../screens/processamento_screen.dart';
import '../services/catalogo.dart';
import '../services/classificador.dart';
import '../services/registo_tecnico.dart';
import '../tema.dart';
import 'botoes.dart';

/// Resultado de uma fotografia do teste.
class _Linha {
  _Linha(this.ficheiro, this.cultura, this.esperado, this.previsto, this.confianca, this.totalMs, this.inferenciaMs);
  final File ficheiro;
  final Cultura cultura;
  final String? esperado;
  final String previsto;
  final double confianca;
  final int totalMs;
  final int inferenciaMs;
  bool? get acertou => esperado == null ? null : esperado == previsto;
}

/// Teste com fotografias reais (RNF03, RNF04 e acurácia no dispositivo).
///
/// Corre o pipeline completo da app (leitura, pré-processamento, inferência)
/// sobre as imagens de uma pasta da app, sem passar pelo selector de imagens.
/// Nome dos ficheiros: `<cultura>_<nn>_<classe>.jpg` (ex.: milho_03_gafanhoto.jpg);
/// a classe no nome é a resposta certa, usada para calcular a acurácia.
/// As imagens copiam-se com: `adb push pasta /sdcard/Android/data/mz.isutc.agrodiagnostico/files/teste/`
class TesteFotografias extends StatefulWidget {
  const TesteFotografias({super.key});

  @override
  State<TesteFotografias> createState() => _TesteFotografiasState();
}

class _TesteFotografiasState extends State<TesteFotografias> {
  Directory? _pasta;
  bool _aCorrer = false;
  String? _estado;
  final List<_Linha> _linhas = [];

  @override
  void initState() {
    super.initState();
    getExternalStorageDirectory().then((d) {
      if (mounted && d != null) setState(() => _pasta = Directory(p.join(d.path, 'teste')));
    });
  }

  static (Cultura, String?)? _interpretar(String nome) {
    final base = p.basenameWithoutExtension(nome).toLowerCase();
    for (final c in Cultura.values) {
      if (base.startsWith('${c.id}_')) {
        final resto = base.substring(c.id.length + 1).replaceFirst(RegExp(r'^\d+_'), '');
        return (c, resto.isEmpty ? null : resto);
      }
    }
    return null;
  }

  Future<void> _correr() async {
    final pasta = _pasta;
    if (pasta == null) return;
    final ficheiros = (await pasta.exists() ? pasta.listSync() : <FileSystemEntity>[])
        .whereType<File>()
        .where((f) => RegExp(r'\.(jpe?g|png)$', caseSensitive: false).hasMatch(f.path))
        .toList()
      ..sort((a, b) => a.path.compareTo(b.path));
    if (ficheiros.isEmpty) {
      setState(() => _estado = 'Não há imagens em ${pasta.path}');
      return;
    }
    setState(() {
      _aCorrer = true;
      _linhas.clear();
      _estado = null;
    });
    for (final (i, f) in ficheiros.indexed) {
      final info = _interpretar(p.basename(f.path));
      if (info == null) continue;
      final (cultura, esperado) = info;
      setState(() => _estado = 'A analisar ${i + 1} de ${ficheiros.length}…');
      try {
        final cronometro = Stopwatch()..start(); // como na app: a partir da imagem confirmada
        final r = await Classificador.instancia
            .classificar(cultura, f.path, cronometroTotal: cronometro, dataCaptura: DateTime.now());
        _linhas.add(_Linha(f, cultura, esperado, r.classe, r.confianca, r.medicao.tempoTotalMs, r.medicao.inferenciaMs));
      } on ErroModelo catch (e) {
        _estado = e.mensagem;
        break;
      }
      if (mounted) setState(() {});
    }
    final comResposta = _linhas.where((l) => l.acertou != null).toList();
    final acertos = comResposta.where((l) => l.acertou!).length;
    final total = Estatisticas(_linhas.map((l) => l.totalMs).toList());
    final inf = Estatisticas(_linhas.map((l) => l.inferenciaMs).toList());
    final resumo = 'teste com fotografias n=${_linhas.length} acertos=$acertos/${comResposta.length} '
        'total média=${total.media.toStringAsFixed(1)}ms (${total.minimo}–${total.maximo}) '
        'inferência média=${inf.media.toStringAsFixed(1)}ms (${inf.minimo}–${inf.maximo}) '
        'pico RSS=${(ProcessInfo.maxRss / 1048576).toStringAsFixed(1)}MB';
    RegistoTecnico.instancia.escrever(resumo);
    if (mounted) {
      setState(() {
        _aCorrer = false;
        _estado = null;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final comResposta = _linhas.where((l) => l.acertou != null).toList();
    final acertos = comResposta.where((l) => l.acertou!).length;
    final total = Estatisticas(_linhas.map((l) => l.totalMs).toList());
    final inf = Estatisticas(_linhas.map((l) => l.inferenciaMs).toList());
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Cores.cartao, borderRadius: BorderRadius.circular(16), boxShadow: sombraSuave),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('Teste com fotografias', style: TextStyle(fontWeight: FontWeight.w800)),
        const SizedBox(height: 4),
        Text(
          'Diagnostica todas as imagens da pasta de teste da app, com o pipeline completo. '
          'Pasta: ${_pasta?.path ?? '…'}',
          style: const TextStyle(fontSize: 12, color: Cores.textoSecundario),
        ),
        const SizedBox(height: 12),
        BotaoPrincipal(
          texto: _aCorrer ? 'A analisar...' : 'Executar com fotografias',
          icone: Icons.photo_library_outlined,
          aoPremir: _aCorrer ? null : _correr,
        ),
        if (_estado != null) ...[
          const SizedBox(height: 10),
          Text(_estado!, style: const TextStyle(color: Cores.textoSecundario)),
        ],
        if (_linhas.isNotEmpty) ...[
          const SizedBox(height: 12),
          _linha('Imagens analisadas', '${_linhas.length}'),
          if (comResposta.isNotEmpty)
            _linha('Acurácia no dispositivo',
                '$acertos/${comResposta.length} (${(100 * acertos / comResposta.length).toStringAsFixed(0)}%)'),
          _linha('Da confirmação ao resultado', '${total.media.toStringAsFixed(0)} ms (${total.minimo}–${total.maximo})'),
          _linha('Só inferência', '${inf.media.toStringAsFixed(0)} ms (${inf.minimo}–${inf.maximo})'),
          _linha('Pico de memória', '${(ProcessInfo.maxRss / 1048576).toStringAsFixed(1)} MB'),
          const SizedBox(height: 8),
          const Text('Toque numa imagem para a abrir no fluxo normal (processamento → resultado).',
              style: TextStyle(fontSize: 11, color: Cores.textoSecundario)),
          for (final l in _linhas)
            InkWell(
              onTap: () => Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => ProcessamentoScreen(
                  cultura: l.cultura,
                  caminhoImagem: l.ficheiro.path,
                  cronometro: Stopwatch()..start(),
                  dataCaptura: DateTime.now(),
                ),
              )),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Row(children: [
                  Icon(
                    l.acertou == null ? Icons.help_outline : (l.acertou! ? Icons.check_circle : Icons.cancel),
                    size: 18,
                    color: l.acertou == false ? Cores.laranjaEscuro : Cores.verdeEscuro,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '${p.basename(l.ficheiro.path)} → '
                      '${Catalogo.instancia.patologia(l.cultura, l.previsto).nomeLocal} '
                      '${(l.confianca * 100).round()}%',
                      style: const TextStyle(fontSize: 12),
                    ),
                  ),
                  Text('${l.totalMs} ms', style: const TextStyle(fontSize: 12, color: Cores.textoSecundario)),
                ]),
              ),
            ),
        ],
      ]),
    );
  }

  Widget _linha(String rotulo, String valor) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 3),
        child: Row(children: [
          Expanded(child: Text(rotulo, style: const TextStyle(color: Cores.textoSecundario, fontSize: 13))),
          Text(valor, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
        ]),
      );
}
