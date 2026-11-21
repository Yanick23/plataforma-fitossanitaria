import 'package:flutter/material.dart';

import '../models/cultura.dart';
import '../tema.dart';
import '../widgets/ecra_escuro.dart';
import '../widgets/cartao.dart';
import 'captura_screen.dart';

void abrirCaptura(BuildContext context, Cultura cultura) => Navigator.of(context).push(MaterialPageRoute(
    settings: const RouteSettings(name: CapturaScreen.rota), builder: (_) => CapturaScreen(cultura: cultura)));

/// «Que planta vai fotografar?» num painel que sobe de baixo; ao escolher, abre a câmara.
/// A cultura define o modelo usado (RF02).
Future<void> escolherCulturaEFotografar(BuildContext context) async {
  final cultura = await showModalBottomSheet<Cultura>(
    context: context,
    builder: (context) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 16),
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          const Text('Que planta vai fotografar?', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700)),
          const SizedBox(height: 6),
          const Text('Seleccione uma das opções. Cada cultura tem o seu modelo.',
              style: TextStyle(fontSize: 15, color: Cores.textoSecundario)),
          const SizedBox(height: 18),
          for (final (i, c) in Cultura.values.indexed) ...[
            if (i > 0) const SizedBox(height: 12),
            _LinhaCultura(cultura: c, aoTocar: () => Navigator.of(context).pop(c)),
          ],
        ]),
      ),
    ),
  );
  if (cultura != null && context.mounted) abrirCaptura(context, cultura);
}

class _LinhaCultura extends StatelessWidget {
  const _LinhaCultura({required this.cultura, required this.aoTocar});

  final Cultura cultura;
  final VoidCallback aoTocar;

  @override
  Widget build(BuildContext context) {
    final cores = cultura == Cultura.milho ? Cores.milho : Cores.mandioca;
    return CartaoArredondado(
      aoTocar: aoTocar,
      padding: const EdgeInsets.fromLTRB(16, 16, 12, 16),
      child: Row(children: [
        CirculoIcone(cultura == Cultura.milho ? Icons.grass : Icons.spa_outlined,
            tamanho: 52, cor: cores[0], corIcone: cores[1]),
        const SizedBox(width: 16),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(cultura.nome, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
            Text(cultura.nomeCientifico,
                style: const TextStyle(fontSize: 14.5, fontStyle: FontStyle.italic, color: Cores.textoSecundario)),
          ]),
        ),
        const Icon(Icons.chevron_right, color: Cores.texto),
      ]),
    );
  }
}

/// A mesma escolha como ecrã (usada quando se chega por um caminho sem painel, ex.: campanha
/// de uma cultura que a app não diagnostica).
class CulturaScreen extends StatelessWidget {
  const CulturaScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return EcraEscuro(
      titulo: 'Que planta vai fotografar?',
      subtitulo: 'Seleccione uma das opções. Cada cultura tem o seu modelo.',
      filhos: [
        for (final (i, c) in Cultura.values.indexed) ...[
          if (i > 0) const SizedBox(height: 12),
          _LinhaCultura(cultura: c, aoTocar: () => abrirCaptura(context, c)),
        ],
      ],
    );
  }
}
