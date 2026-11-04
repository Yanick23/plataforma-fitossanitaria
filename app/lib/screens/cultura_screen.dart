import 'package:flutter/material.dart';

import '../models/cultura.dart';
import '../tema.dart';
import '../widgets/botoes.dart';
import 'captura_screen.dart';

/// Ecrã 2 — Selecção da cultura. A cultura escolhida define o modelo usado (RF02).
class CulturaScreen extends StatelessWidget {
  const CulturaScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const BotaoVoltar(),
            const SizedBox(height: 24),
            const Text('Escolha a Cultura', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800)),
            const SizedBox(height: 4),
            const Text('Que planta quer diagnosticar?', style: TextStyle(color: Cores.textoSecundario)),
            const SizedBox(height: 20),
            _CartaoCultura(cultura: Cultura.milho, cores: Cores.milho, icone: Icons.grass),
            const SizedBox(height: 14),
            _CartaoCultura(cultura: Cultura.mandioca, cores: Cores.mandioca, icone: Icons.spa),
          ]),
        ),
      ),
    );
  }
}

class _CartaoCultura extends StatelessWidget {
  const _CartaoCultura({required this.cultura, required this.cores, required this.icone});

  final Cultura cultura;
  final List<Color> cores;
  final IconData icone;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Cores.cartao,
      borderRadius: BorderRadius.circular(20),
      elevation: 0,
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: () => Navigator.of(context)
            .push(MaterialPageRoute(
                settings: const RouteSettings(name: CapturaScreen.rota), builder: (_) => CapturaScreen(cultura: cultura))),
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 22),
          decoration: BoxDecoration(borderRadius: BorderRadius.circular(20), boxShadow: sombraSuave),
          child: Column(children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                gradient: LinearGradient(begin: Alignment.topLeft, end: Alignment.bottomRight, colors: cores),
                borderRadius: BorderRadius.circular(18),
              ),
              child: Icon(icone, color: Colors.white, size: 32),
            ),
            const SizedBox(height: 12),
            Text(cultura.nome, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
          ]),
        ),
      ),
    );
  }
}
