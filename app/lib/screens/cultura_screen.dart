import 'package:flutter/material.dart';

import '../models/cultura.dart';
import '../services/catalogo.dart';
import '../tema.dart';
import '../widgets/botoes.dart';
import '../widgets/cartao.dart';
import 'captura_screen.dart';

/// Escolha da cultura. A cultura escolhida define o modelo usado (RF02).
class CulturaScreen extends StatelessWidget {
  const CulturaScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          const CabecalhoEcra(titulo: 'Nova fotografia'),
          Expanded(
            child: ListView(padding: const EdgeInsets.fromLTRB(20, 8, 20, 24), children: [
              Text('Que planta quer diagnosticar?', style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 6),
              const Text('A app usa um modelo próprio para cada cultura.',
                  style: TextStyle(fontSize: 15, color: Cores.textoSecundario)),
              const SizedBox(height: 20),
              for (final (i, c) in Cultura.values.indexed) ...[
                if (i > 0) const SizedBox(height: 10),
                _CartaoCultura(cultura: c),
              ],
            ]),
          ),
        ]),
      ),
    );
  }
}

class _CartaoCultura extends StatelessWidget {
  const _CartaoCultura({required this.cultura});

  final Cultura cultura;

  @override
  Widget build(BuildContext context) {
    final cores = cultura == Cultura.milho ? Cores.milho : Cores.mandioca;
    final n = Catalogo.instancia.problemasDe(cultura).length;
    return Cartao(
      aoTocar: () => Navigator.of(context).push(MaterialPageRoute(
          settings: const RouteSettings(name: CapturaScreen.rota), builder: (_) => CapturaScreen(cultura: cultura))),
      child: Row(children: [
        Container(
          width: 52,
          height: 52,
          decoration: BoxDecoration(color: cores[0], borderRadius: BorderRadius.circular(10)),
          child: Icon(cultura == Cultura.milho ? Icons.grass : Icons.spa_outlined, color: cores[1], size: 26),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(cultura.nome, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),
            Text(cultura.nomeCientifico,
                style: const TextStyle(fontSize: 13.5, fontStyle: FontStyle.italic, color: Cores.textoSecundario)),
            if (n > 0) ...[
              const SizedBox(height: 4),
              Text('Reconhece $n pragas e doenças', style: const TextStyle(fontSize: 13, color: Cores.textoSecundario)),
            ],
          ]),
        ),
        const Icon(Icons.chevron_right, color: Cores.textoTerciario),
      ]),
    );
  }
}
