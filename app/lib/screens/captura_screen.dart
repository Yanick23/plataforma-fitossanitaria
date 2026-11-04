import 'dart:isolate';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../models/cultura.dart';
import '../models/resultado_classificacao.dart';
import '../services/pre_processamento.dart';
import '../services/registo_tecnico.dart';
import '../tema.dart';
import '../widgets/botoes.dart';
import 'processamento_screen.dart';

/// Ecrã 3 — Captura: fotografia com a câmara ou imagem da galeria (RF01).
///
/// Antes de analisar, confirma se a foto está nítida e com luz suficiente. Com [anterior],
/// a nova fotografia junta-se ao resultado anterior (outra vista da mesma planta).
class CapturaScreen extends StatefulWidget {
  const CapturaScreen({super.key, required this.cultura, this.anterior});

  /// Nome da rota da primeira captura (para «Recomeçar» voltar aqui).
  static const rota = '/captura';

  final Cultura cultura;
  final ResultadoClassificacao? anterior;

  @override
  State<CapturaScreen> createState() => _CapturaScreenState();
}

class _CapturaScreenState extends State<CapturaScreen> {
  final _picker = ImagePicker();
  bool _ocupado = false;

  Future<void> _obterImagem(ImageSource origem) async {
    if (_ocupado) return;
    setState(() => _ocupado = true);
    try {
      // Reduz logo a fotografia: o modelo só precisa de 224×224 e assim a
      // descodificação é muito mais rápida em telemóveis de gama baixa.
      final foto = await _picker.pickImage(source: origem, maxWidth: 1024, maxHeight: 1024, imageQuality: 95);
      if (foto == null || !mounted) return;
      if (!await _qualidadeAceite(foto.path) || !mounted) return;
      // RNF03: mede-se desde a confirmação da imagem até o resultado estar pronto.
      final cronometro = Stopwatch()..start();
      await Navigator.of(context).push(MaterialPageRoute(
        builder: (_) => ProcessamentoScreen(
          cultura: widget.cultura,
          caminhoImagem: foto.path,
          cronometro: cronometro,
          dataCaptura: DateTime.now(),
          anterior: widget.anterior,
        ),
      ));
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Não foi possível obter a imagem: $e')));
      }
    } finally {
      if (mounted) setState(() => _ocupado = false);
    }
  }

  /// Mede a nitidez e o brilho; se houver problema, pergunta se quer tirar outra.
  Future<bool> _qualidadeAceite(String caminho) async {
    final QualidadeFoto q;
    final cronometro = Stopwatch()..start();
    try {
      q = await Isolate.run(() => avaliarQualidade(caminho));
    } on FormatException {
      return true; // a análise mostrará o erro de leitura
    }
    RegistoTecnico.instancia.escrever('qualidade da foto: nitidez ${q.nitidez.toStringAsFixed(1)}, '
        'brilho ${q.brilho.toStringAsFixed(1)}, ${cronometro.elapsedMilliseconds} ms'
        '${q.boa ? '' : ' — ${q.problemas.map((p) => p.name).join(', ')}'}');
    if (q.boa || !mounted) return true;
    final usar = await showModalBottomSheet<bool>(
      context: context,
      isDismissible: false,
      builder: (_) => _AvisoQualidade(problemas: q.problemas),
    );
    return usar ?? false;
  }

  @override
  Widget build(BuildContext context) {
    final anterior = widget.anterior;
    return Scaffold(
      backgroundColor: Cores.captura,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
          child: Column(children: [
            Row(children: [
              const BotaoVoltar(escuro: true),
              const Spacer(),
              Text(widget.cultura.nome,
                  style: const TextStyle(color: Colors.white70, fontWeight: FontWeight.w700)),
            ]),
            const Spacer(),
            const SizedBox(width: 190, height: 190, child: CustomPaint(painter: _MolduraEnquadramento())),
            const Spacer(),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              decoration: BoxDecoration(color: Colors.black45, borderRadius: BorderRadius.circular(14)),
              child: Text(
                anterior != null
                    ? 'Fotografe outra folha da mesma planta, ou a mesma folha de outro ângulo.\n'
                        'Foto ${anterior.fotos.length + 1} de $maximoFotos.'
                    : 'Aponte a câmara para a folha afectada.\nUse luz natural e encha o enquadramento com a folha.',
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, height: 1.35),
              ),
            ),
            const SizedBox(height: 24),
            Row(children: [
              const Expanded(child: SizedBox()),
              Semantics(
                button: true,
                label: 'Tirar fotografia',
                child: GestureDetector(
                  onTap: () => _obterImagem(ImageSource.camera),
                  child: Container(
                    width: 76,
                    height: 76,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: const LinearGradient(colors: [Cores.verde, Cores.verdeEscuro]),
                      border: Border.all(color: Colors.white70, width: 4),
                    ),
                    child: _ocupado
                        ? const Padding(
                            padding: EdgeInsets.all(22),
                            child: CircularProgressIndicator(color: Colors.white, strokeWidth: 3))
                        : const Icon(Icons.photo_camera, color: Colors.white, size: 30),
                  ),
                ),
              ),
              Expanded(
                child: Center(
                  child: TextButton(
                    onPressed: () => _obterImagem(ImageSource.gallery),
                    style: TextButton.styleFrom(foregroundColor: Colors.white),
                    child: const Column(mainAxisSize: MainAxisSize.min, children: [
                      Icon(Icons.photo_library_outlined),
                      SizedBox(height: 4),
                      Text('Galeria', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
                    ]),
                  ),
                ),
              ),
            ]),
          ]),
        ),
      ),
    );
  }
}

/// Explica o problema da foto e deixa escolher: tirar outra (recomendado) ou usar esta.
class _AvisoQualidade extends StatelessWidget {
  const _AvisoQualidade({required this.problemas});

  final List<ProblemaFoto> problemas;

  static const _textos = {
    ProblemaFoto.desfocada: (
      'A foto está desfocada',
      'Segure o telemóvel parado e toque no ecrã sobre a folha para focar antes de fotografar.'
    ),
    ProblemaFoto.escura: ('A foto está escura', 'Fotografe com luz do dia, sem a sombra do corpo sobre a folha.'),
    ProblemaFoto.clara: (
      'A foto tem luz a mais',
      'Evite o sol directo na folha: faça sombra com a mão ou mude de posição.'
    ),
  };

  @override
  Widget build(BuildContext context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 20, 24, 20),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Row(children: [
              Icon(Icons.warning_amber_rounded, color: Cores.laranjaEscuro),
              SizedBox(width: 8),
              Expanded(
                child: Text('Esta foto pode dar um resultado errado',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
              ),
            ]),
            const SizedBox(height: 12),
            for (final p in problemas) ...[
              Text(_textos[p]!.$1, style: const TextStyle(fontWeight: FontWeight.w700)),
              Text(_textos[p]!.$2, style: const TextStyle(color: Cores.textoSecundario, height: 1.35)),
              const SizedBox(height: 10),
            ],
            const SizedBox(height: 8),
            BotaoPrincipal(
                texto: 'Tirar Outra Foto', icone: Icons.photo_camera, aoPremir: () => Navigator.of(context).pop(false)),
            const SizedBox(height: 10),
            BotaoSecundario(texto: 'Usar Esta Foto', aoPremir: () => Navigator.of(context).pop(true)),
          ]),
        ),
      );
}

/// Os quatro cantos verdes do guia de enquadramento.
class _MolduraEnquadramento extends CustomPainter {
  const _MolduraEnquadramento();

  @override
  void paint(Canvas canvas, Size size) {
    final tinta = Paint()
      ..color = Cores.verde
      ..strokeWidth = 4
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;
    const l = 34.0;
    final w = size.width, h = size.height;
    final cantos = [
      [Offset(0, l), Offset.zero, const Offset(l, 0)],
      [Offset(w - l, 0), Offset(w, 0), Offset(w, l)],
      [Offset(0, h - l), Offset(0, h), Offset(l, h)],
      [Offset(w - l, h), Offset(w, h), Offset(w, h - l)],
    ];
    for (final c in cantos) {
      canvas.drawPath(Path()
        ..moveTo(c[0].dx, c[0].dy)
        ..lineTo(c[1].dx, c[1].dy)
        ..lineTo(c[2].dx, c[2].dy), tinta);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
