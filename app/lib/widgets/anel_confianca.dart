import 'package:flutter/material.dart';

import '../models/resultado_classificacao.dart' show limiarConfianca;
import '../tema.dart';

/// Certeza da app numa barra, com a marca do limiar (60 %): abaixo dele, a app diz que não tem
/// certeza e pede outra fotografia (RF05). Verde acima do limiar, âmbar abaixo.
class MedidorConfianca extends StatelessWidget {
  const MedidorConfianca({super.key, required this.confianca, required this.baixa});

  final double confianca; // 0..1
  final bool baixa;

  @override
  Widget build(BuildContext context) {
    final cor = baixa ? Cores.aviso : Cores.marca;
    final pct = (confianca * 100).round();
    return Semantics(
      label: 'Certeza da app: $pct por cento${baixa ? ', abaixo do limite' : ''}',
      excludeSemantics: true,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(crossAxisAlignment: CrossAxisAlignment.baseline, textBaseline: TextBaseline.alphabetic, children: [
          const Expanded(
            child: Text('Certeza da app', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: Cores.textoSecundario)),
          ),
          Text('$pct%', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600, color: baixa ? Cores.avisoTexto : Cores.texto)),
        ]),
        const SizedBox(height: 8),
        LayoutBuilder(builder: (context, l) {
          final largura = l.maxWidth;
          return SizedBox(
            height: 14,
            child: Stack(clipBehavior: Clip.none, children: [
              Positioned(
                left: 0,
                right: 0,
                top: 3,
                height: 8,
                child: DecoratedBox(decoration: BoxDecoration(color: Cores.superficie2, borderRadius: BorderRadius.circular(4))),
              ),
              Positioned(
                left: 0,
                top: 3,
                height: 8,
                width: largura * confianca.clamp(0.0, 1.0),
                child: DecoratedBox(decoration: BoxDecoration(color: cor, borderRadius: BorderRadius.circular(4))),
              ),
              // Marca do limiar
              Positioned(
                left: largura * limiarConfianca - 1,
                top: 0,
                width: 2,
                height: 14,
                child: const ColoredBox(color: Cores.texto),
              ),
            ]),
          );
        }),
        const SizedBox(height: 6),
        Text(
          baixa ? 'Abaixo de ${(limiarConfianca * 100).round()}%: a app não tem certeza.' : 'A marca indica o mínimo de ${(limiarConfianca * 100).round()}%.',
          style: const TextStyle(fontSize: 12.5, color: Cores.textoSecundario),
        ),
      ]),
    );
  }
}
