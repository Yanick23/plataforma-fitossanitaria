import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../models/cultura.dart';
import '../tema.dart';
import '../widgets/botoes.dart';
import 'processamento_screen.dart';

/// Ecrã 3 — Captura: fotografia com a câmara ou imagem da galeria (RF01).
class CapturaScreen extends StatefulWidget {
  const CapturaScreen({super.key, required this.cultura});

  final Cultura cultura;

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
      // RNF03: mede-se desde a confirmação da imagem até o resultado estar pronto.
      final cronometro = Stopwatch()..start();
      await Navigator.of(context).push(MaterialPageRoute(
        builder: (_) => ProcessamentoScreen(
          cultura: widget.cultura,
          caminhoImagem: foto.path,
          cronometro: cronometro,
          dataCaptura: DateTime.now(),
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

  @override
  Widget build(BuildContext context) {
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
              child: const Text(
                'Aponte a câmara para a folha afectada.\nUse luz natural e encha o enquadramento com a folha.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, height: 1.35),
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
