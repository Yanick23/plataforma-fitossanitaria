import 'package:flutter/material.dart';

import '../tema.dart';

/// Cartão da app: branco, contorno fino, cantos de 12. Tocável quando tem [aoTocar].
class Cartao extends StatelessWidget {
  const Cartao({
    super.key,
    required this.child,
    this.aoTocar,
    this.padding = const EdgeInsets.all(16),
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
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: borda)),
      child: InkWell(onTap: aoTocar, child: Padding(padding: padding, child: child)),
    );
  }
}

/// Linha de cabeçalho de um cartão: o tipo (ícone e nome, na cor do estado) e, à direita, um dado curto.
class CabecalhoCartao extends StatelessWidget {
  const CabecalhoCartao({super.key, required this.icone, required this.texto, this.cor = Cores.marca, this.direita});

  final IconData icone;
  final String texto;
  final Color cor;
  final Widget? direita;

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      Icon(icone, size: 17, color: cor),
      const SizedBox(width: 6),
      Expanded(
        child: Text(texto,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: cor, letterSpacing: 0.1)),
      ),
      ?direita,
    ]);
  }
}

/// Texto pequeno e secundário (datas, zona, metadados).
class TextoMeta extends StatelessWidget {
  const TextoMeta(this.texto, {super.key, this.icone});

  final String texto;
  final IconData? icone;

  @override
  Widget build(BuildContext context) {
    final t = Text(texto, style: const TextStyle(fontSize: 12.5, color: Cores.textoSecundario));
    if (icone == null) return t;
    return Row(mainAxisSize: MainAxisSize.min, children: [
      Icon(icone, size: 14, color: Cores.textoSecundario),
      const SizedBox(width: 4),
      Flexible(child: t),
    ]);
  }
}

/// Caixa de aviso (fundo âmbar claro), para dizer ao agricultor que a app não tem certeza.
class CaixaAviso extends StatelessWidget {
  const CaixaAviso({super.key, required this.titulo, this.texto, this.icone = Icons.warning_amber_rounded});

  final String titulo;
  final String? texto;
  final IconData icone;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: decoracaoCartao(cor: Cores.avisoFundo, borda: const Color(0xFFF1D9A0), raio: 12),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(icone, color: Cores.avisoTexto, size: 20),
        const SizedBox(width: 10),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(titulo, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: Cores.avisoTexto, height: 1.3)),
            if (texto != null) ...[
              const SizedBox(height: 2),
              Text(texto!, style: const TextStyle(fontSize: 14, color: Cores.avisoTexto, height: 1.4)),
            ],
          ]),
        ),
      ]),
    );
  }
}
