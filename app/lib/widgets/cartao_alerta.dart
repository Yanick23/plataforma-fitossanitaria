import 'package:flutter/material.dart';

import '../models/alerta.dart';
import '../tema.dart';
import 'formatacao.dart';

/// Cores e ícone de cada nível (o nível é sempre dito também por escrito).
({Color fundo, Color texto, IconData icone}) estiloNivel(NivelAlerta n) => switch (n) {
      NivelAlerta.urgente => (fundo: const Color(0xFFFDE8E8), texto: const Color(0xFFB91C1C), icone: Icons.error_outline),
      NivelAlerta.aviso => (fundo: Cores.avisoFundo, texto: Cores.avisoTexto, icone: Icons.warning_amber_rounded),
      NivelAlerta.informacao => (fundo: const Color(0xFFE3EEFB), texto: const Color(0xFF1D4ED8), icone: Icons.info_outline),
    };

class EtiquetaNivel extends StatelessWidget {
  const EtiquetaNivel(this.nivel, {super.key});

  final NivelAlerta nivel;

  @override
  Widget build(BuildContext context) {
    final e = estiloNivel(nivel);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(color: e.fundo, borderRadius: BorderRadius.circular(8)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(e.icone, size: 14, color: e.texto),
        const SizedBox(width: 4),
        Text(nivel.nome, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: e.texto)),
      ]),
    );
  }
}

/// Cartão de um alerta: título, zona, data e o início da mensagem.
class CartaoAlerta extends StatelessWidget {
  const CartaoAlerta({super.key, required this.alerta, this.aoTocar, this.completo = false});

  final Alerta alerta;
  final VoidCallback? aoTocar;

  /// true = mostra a mensagem inteira (ecrã de alertas, depois de aberto).
  final bool completo;

  @override
  Widget build(BuildContext context) {
    final e = estiloNivel(alerta.nivel);
    return Material(
      color: Cores.cartao,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: aoTocar,
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border(left: BorderSide(color: e.texto, width: alerta.lido ? 0 : 4)),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              EtiquetaNivel(alerta.nivel),
              const Spacer(),
              if (!alerta.lido)
                const Padding(
                  padding: EdgeInsets.only(right: 6),
                  child: Text('Novo', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: Cores.verdeEscuro)),
                ),
              Text(formatarDataHora(alerta.criadoEm), style: const TextStyle(fontSize: 11, color: Cores.textoSecundario)),
            ]),
            const SizedBox(height: 8),
            Text(alerta.titulo, style: TextStyle(fontSize: 16, fontWeight: alerta.lido ? FontWeight.w600 : FontWeight.w800)),
            const SizedBox(height: 4),
            Text(
              alerta.mensagem,
              maxLines: completo ? null : 2,
              overflow: completo ? null : TextOverflow.ellipsis,
              style: const TextStyle(height: 1.4, color: Cores.texto),
            ),
            const SizedBox(height: 8),
            Row(children: [
              const Icon(Icons.place_outlined, size: 14, color: Cores.textoSecundario),
              const SizedBox(width: 4),
              Expanded(
                child: Text(
                  alerta.expiraEm == null ? alerta.zona : '${alerta.zona} · válido até ${formatarData(alerta.expiraEm!)}',
                  style: const TextStyle(fontSize: 12, color: Cores.textoSecundario),
                ),
              ),
            ]),
          ]),
        ),
      ),
    );
  }
}
