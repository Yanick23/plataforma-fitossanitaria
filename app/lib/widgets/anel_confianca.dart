import 'package:flutter/material.dart';

import '../tema.dart';

/// Anel com a percentagem de confiança (verde ≥ 60%, laranja abaixo).
class AnelConfianca extends StatelessWidget {
  const AnelConfianca({super.key, required this.confianca, required this.baixa});

  final double confianca; // 0..1
  final bool baixa;

  @override
  Widget build(BuildContext context) {
    final cor = baixa ? Cores.laranjaEscuro : Cores.verde;
    return Semantics(
      label: 'Confiança ${(confianca * 100).round()} por cento',
      child: SizedBox(
        width: 112,
        height: 112,
        child: Stack(fit: StackFit.expand, children: [
          CircularProgressIndicator(
            value: confianca,
            strokeWidth: 11,
            strokeCap: StrokeCap.round,
            backgroundColor: cor.withValues(alpha: 0.15),
            valueColor: AlwaysStoppedAnimation(cor),
          ),
          Center(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Text('${(confianca * 100).round()}%',
                  style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800)),
              const Text('certeza', style: TextStyle(fontSize: 12, color: Cores.textoSecundario)),
            ]),
          ),
        ]),
      ),
    );
  }
}
