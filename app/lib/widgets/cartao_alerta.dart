import 'package:flutter/material.dart';

import '../models/alerta.dart';
import '../tema.dart';
import 'botao_ouvir.dart';
import 'cartao.dart';
import 'formatacao.dart';

/// Cor do nível (o nível é sempre dito também por escrito).
Color corNivel(NivelAlerta n) => switch (n) {
      NivelAlerta.urgente => Cores.criticoTexto,
      NivelAlerta.aviso => Cores.avisoTexto,
      NivelAlerta.informacao => Cores.info,
    };

/// Um alerta numa lista: na primeira linha o nível e quando chegou; depois o título e a mensagem.
/// Por ler: título mais forte e um ponto à direita.
class CartaoAlerta extends StatelessWidget {
  const CartaoAlerta({super.key, required this.alerta, this.aoTocar, this.completo = false});

  final Alerta alerta;
  final VoidCallback? aoTocar;

  /// true = mensagem inteira e gravação de voz (alerta aberto).
  final bool completo;

  @override
  Widget build(BuildContext context) {
    final conteudo = Padding(
      padding: completo ? const EdgeInsets.fromLTRB(20, 4, 20, 8) : EdgeInsets.zero,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Text(alerta.nivel.nome,
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: corNivel(alerta.nivel))),
          Text(' · ${quando(alerta.criadoEm)}', style: const TextStyle(fontSize: 13, color: Cores.textoSecundario)),
          const Spacer(),
          if (!alerta.lido && !completo)
            Semantics(
              label: 'por ler',
              child: Container(
                  width: 10, height: 10, decoration: const BoxDecoration(color: Cores.limaForte, shape: BoxShape.circle)),
            ),
        ]),
        const SizedBox(height: 4),
        Text(alerta.titulo,
            style: TextStyle(
                fontSize: completo ? 22 : 17, fontWeight: alerta.lido ? FontWeight.w500 : FontWeight.w600, height: 1.3)),
        const SizedBox(height: 4),
        Text(
          alerta.mensagem,
          maxLines: completo ? null : 2,
          overflow: completo ? null : TextOverflow.ellipsis,
          style: TextStyle(fontSize: completo ? 16 : 14.5, height: 1.45, color: completo ? Cores.texto : Cores.textoSecundario),
        ),
        if (completo && alerta.audios.isNotEmpty) ...[const SizedBox(height: 14), BotaoOuvir(audios: alerta.audios)],
        const SizedBox(height: 8),
        Text(
          alerta.expiraEm == null ? alerta.zona : '${alerta.zona} · até ${dataCurta(alerta.expiraEm!)}',
          style: const TextStyle(fontSize: 13, color: Cores.textoTerciario),
        ),
      ]),
    );
    if (completo) return conteudo;
    return CartaoArredondado(aoTocar: aoTocar, child: conteudo);
  }
}
