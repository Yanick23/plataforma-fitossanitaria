import 'package:flutter/material.dart';

import '../models/alerta.dart';
import '../tema.dart';
import 'botao_ouvir.dart';
import 'cartao.dart';
import 'formatacao.dart';

/// Cores e ícone de cada nível (o nível é sempre dito também por escrito).
({Color fundo, Color texto, IconData icone}) estiloNivel(NivelAlerta n) => switch (n) {
      NivelAlerta.urgente => (fundo: Cores.criticoFundo, texto: Cores.criticoTexto, icone: Icons.error_outline),
      NivelAlerta.aviso => (fundo: Cores.avisoFundo, texto: Cores.avisoTexto, icone: Icons.warning_amber_rounded),
      NivelAlerta.informacao => (fundo: Cores.infoFundo, texto: Cores.info, icone: Icons.info_outline),
    };

class EtiquetaNivel extends StatelessWidget {
  const EtiquetaNivel(this.nivel, {super.key});

  final NivelAlerta nivel;

  @override
  Widget build(BuildContext context) {
    final e = estiloNivel(nivel);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
      decoration: BoxDecoration(color: e.fundo, borderRadius: BorderRadius.circular(6)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(e.icone, size: 14, color: e.texto),
        const SizedBox(width: 4),
        Text(nivel.nome, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: e.texto)),
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
    return Cartao(
      aoTocar: aoTocar,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          EtiquetaNivel(alerta.nivel),
          const SizedBox(width: 8),
          if (!alerta.lido)
            const Text('Novo', style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600, color: Cores.marca)),
          const Spacer(),
          TextoMeta(formatarDataHora(alerta.criadoEm)),
        ]),
        const SizedBox(height: 10),
        Text(alerta.titulo, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, height: 1.3)),
        const SizedBox(height: 4),
        Text(
          alerta.mensagem,
          maxLines: completo ? null : 2,
          overflow: completo ? null : TextOverflow.ellipsis,
          style: const TextStyle(fontSize: 14.5, height: 1.45, color: Cores.textoSecundario),
        ),
        // Mensagem de voz só com o alerta aberto (na lista, tocar abre-o).
        if (completo && alerta.audios.isNotEmpty) ...[const SizedBox(height: 12), BotaoOuvir(audios: alerta.audios)],
        const SizedBox(height: 10),
        TextoMeta(
          alerta.expiraEm == null ? alerta.zona : '${alerta.zona} · válido até ${formatarData(alerta.expiraEm!)}',
          icone: Icons.place_outlined,
        ),
      ]),
    );
  }
}
