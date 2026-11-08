import 'package:flutter/material.dart';

import '../tema.dart';

/// Marca da app: símbolo discreto e nome (sem gradientes nem brilhos).
class MarcaApp extends StatelessWidget {
  const MarcaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      Container(
        width: 44,
        height: 44,
        decoration: BoxDecoration(color: Cores.marca, borderRadius: BorderRadius.circular(10)),
        child: const Icon(Icons.eco_outlined, color: Colors.white, size: 24),
      ),
      const SizedBox(width: 12),
      const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Diagnóstico de culturas', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600, height: 1.2)),
        SizedBox(height: 2),
        Text('Milho e mandioca · Moçambique', style: TextStyle(fontSize: 13, color: Cores.textoSecundario)),
      ]),
    ]);
  }
}

/// Mensagem de erro de um formulário (ícone e texto a vermelho).
class MensagemErro extends StatelessWidget {
  const MensagemErro(this.texto, {super.key});

  final String texto;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: decoracaoCartao(cor: Cores.criticoFundo, borda: const Color(0xFFF2C4C2), raio: 10),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Icon(Icons.error_outline, size: 18, color: Cores.criticoTexto),
        const SizedBox(width: 8),
        Expanded(child: Text(texto, style: const TextStyle(color: Cores.criticoTexto, height: 1.4))),
      ]),
    );
  }
}
