import 'package:flutter/material.dart';

import '../tema.dart';

/// Acção principal do ecrã: verde da marca, plano, a toda a largura.
class BotaoPrincipal extends StatelessWidget {
  const BotaoPrincipal({super.key, required this.texto, required this.aoPremir, this.icone});

  final String texto;
  final VoidCallback? aoPremir;
  final IconData? icone;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: icone == null
          ? FilledButton(onPressed: aoPremir, child: Text(texto))
          : FilledButton.icon(onPressed: aoPremir, icon: Icon(icone, size: 20), label: Text(texto)),
    );
  }
}

/// Acção secundária: branca, com contorno.
class BotaoSecundario extends StatelessWidget {
  const BotaoSecundario({super.key, required this.texto, required this.aoPremir, this.icone});

  final String texto;
  final VoidCallback? aoPremir;
  final IconData? icone;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: icone == null
          ? OutlinedButton(onPressed: aoPremir, child: Text(texto))
          : OutlinedButton.icon(onPressed: aoPremir, icon: Icon(icone, size: 20), label: Text(texto)),
    );
  }
}

/// Voltar ao ecrã anterior. Sobre a câmara ([escuro]) leva um fundo para se ver sobre a imagem.
class BotaoVoltar extends StatelessWidget {
  const BotaoVoltar({super.key, this.escuro = false});

  final bool escuro;

  @override
  Widget build(BuildContext context) {
    return IconButton(
      tooltip: 'Voltar',
      onPressed: () => Navigator.of(context).maybePop(),
      icon: Icon(Icons.arrow_back, color: escuro ? Colors.white : Cores.texto),
      style: escuro ? IconButton.styleFrom(backgroundColor: Colors.black45) : null,
    );
  }
}

/// Cabeçalho dos ecrãs sem barra de topo: voltar, título e (opcional) acções à direita.
class CabecalhoEcra extends StatelessWidget {
  const CabecalhoEcra({super.key, required this.titulo, this.accoes = const []});

  final String titulo;
  final List<Widget> accoes;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(4, 4, 8, 4),
      child: Row(children: [
        const BotaoVoltar(),
        const SizedBox(width: 4),
        Expanded(child: Text(titulo, style: Theme.of(context).textTheme.titleLarge)),
        ...accoes,
      ]),
    );
  }
}

/// Título de uma secção dentro de um ecrã («Para si», «Mais»).
class TituloSeccao extends StatelessWidget {
  const TituloSeccao(this.texto, {super.key});

  final String texto;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 8, left: 2),
        child: Text(texto,
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Cores.textoSecundario, letterSpacing: 0.2)),
      );
}
