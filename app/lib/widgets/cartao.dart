import 'package:flutter/material.dart';

import '../tema.dart';

/// Secção de um ecrã: título grande e, à direita, uma ligação sublinhada («Ver todos»);
/// por baixo, os elementos com espaço entre eles.
class Seccao extends StatelessWidget {
  const Seccao({super.key, this.titulo, this.accao, required this.filhos, this.espaco = 12});

  final String? titulo;
  final Widget? accao;
  final List<Widget> filhos;
  final double espaco;

  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      if (titulo != null)
        Padding(
          padding: const EdgeInsets.only(bottom: 14),
          child: Row(children: [
            Expanded(child: Text(titulo!, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w600, height: 1.2))),
            ?accao,
          ]),
        ),
      for (final (i, f) in filhos.indexed) ...[if (i > 0) SizedBox(height: espaco), f],
    ]);
  }
}

/// Cartão branco de cantos grandes (24) e contorno fino; tocável quando tem [aoTocar].
class CartaoArredondado extends StatelessWidget {
  const CartaoArredondado({
    super.key,
    required this.child,
    this.aoTocar,
    this.padding = const EdgeInsets.all(20),
    this.cor = Cores.cartao,
    this.borda = Cores.linha,
  });

  final Widget child;
  final VoidCallback? aoTocar;
  final EdgeInsetsGeometry padding;
  final Color cor;
  final Color borda;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: cor,
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24), side: BorderSide(color: borda)),
      child: InkWell(onTap: aoTocar, child: Padding(padding: padding, child: child)),
    );
  }
}

/// «Ver todos», «Calendário»: ligação sublinhada à direita de um título.
class LigacaoTitulo extends StatelessWidget {
  const LigacaoTitulo(this.texto, {super.key, required this.aoTocar});

  final String texto;
  final VoidCallback aoTocar;

  @override
  Widget build(BuildContext context) => TextButton(
        onPressed: aoTocar,
        style: TextButton.styleFrom(foregroundColor: Cores.texto, padding: const EdgeInsets.symmetric(horizontal: 4)),
        child: Text(texto),
      );
}
