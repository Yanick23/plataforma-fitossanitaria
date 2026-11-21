import 'package:flutter/material.dart';

import '../tema.dart';

/// Marca da app sobre o fundo escuro: círculo verde-lima com uma folha e o nome.
class MarcaApp extends StatelessWidget {
  const MarcaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(mainAxisSize: MainAxisSize.min, children: [
      Container(
        width: 64,
        height: 64,
        decoration: const BoxDecoration(
          shape: BoxShape.circle,
          gradient: LinearGradient(colors: [Color(0xFFC2F29A), Cores.limaForte], begin: Alignment.topLeft, end: Alignment.bottomRight),
        ),
        child: const Icon(Icons.eco, color: Cores.escuro, size: 34),
      ),
      const SizedBox(width: 14),
      const Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
        Text('Diagnóstico', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w700, color: Colors.white, height: 1.05)),
        Text('de culturas', style: TextStyle(fontSize: 18, color: Cores.sobreEscuroSecundario)),
      ]),
    ]);
  }
}

/// Mensagem de erro de um formulário.
class MensagemErro extends StatelessWidget {
  const MensagemErro(this.texto, {super.key});

  final String texto;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      decoration: BoxDecoration(color: Cores.criticoFundo, borderRadius: BorderRadius.circular(16)),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Icon(Icons.error_outline, size: 20, color: Cores.criticoTexto),
        const SizedBox(width: 10),
        Expanded(child: Text(texto, style: const TextStyle(color: Cores.criticoTexto, height: 1.4))),
      ]),
    );
  }
}
