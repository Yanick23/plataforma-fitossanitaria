import 'package:flutter/material.dart';

import '../models/calendario.dart';
import '../models/campanha.dart';
import '../models/cultura.dart';
import '../tema.dart';
import 'cartao.dart';
import 'formatacao.dart';

/// «Nesta altura…» (funcionalidade 10): o mês actual do calendário agrícola da província.
class CartaoCalendario extends StatelessWidget {
  const CartaoCalendario({super.key, required this.calendario, required this.mes, this.aoTocar});

  final Calendario calendario;
  final int mes; // 1 a 12
  final VoidCallback? aoTocar;

  @override
  Widget build(BuildContext context) {
    final m = calendario.mes(mes);
    return Cartao(
      aoTocar: aoTocar,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        CabecalhoCartao(
          icone: Icons.calendar_month_outlined,
          texto: 'Nesta altura · ${Calendario.nomesMeses[mes - 1]}',
          direita: const Icon(Icons.chevron_right, size: 20, color: Cores.textoTerciario),
        ),
        if (m.actividades.isNotEmpty) ...[
          const SizedBox(height: 10),
          Text(m.actividades.join(' · '), style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, height: 1.3)),
        ],
        for (final a in m.avisos.take(2)) ...[
          const SizedBox(height: 6),
          Text('${Cultura.nomeDe(a.culturaId)}: ${a.texto}',
              style: const TextStyle(fontSize: 14.5, height: 1.45, color: Cores.textoSecundario)),
        ],
        if (m.avisos.length > 2) ...[
          const SizedBox(height: 6),
          TextoMeta('E mais ${m.avisos.length - 2} no calendário.'),
        ],
        const SizedBox(height: 10),
        TextoMeta('Província de ${calendario.provincia}', icone: Icons.place_outlined),
      ]),
    );
  }
}

/// Pedido do técnico para fotografar as plantas da zona (funcionalidade 12).
class CartaoCampanha extends StatelessWidget {
  const CartaoCampanha({super.key, required this.campanha, this.aoResponder});

  final Campanha campanha;
  final VoidCallback? aoResponder;

  @override
  Widget build(BuildContext context) {
    final cultura = Cultura.talvez(campanha.culturaId);
    return Cartao(
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        CabecalhoCartao(
          icone: Icons.campaign_outlined,
          texto: 'Campanha de vigilância',
          direita: TextoMeta('até ${formatarData(campanha.fim)}'),
        ),
        const SizedBox(height: 10),
        Text(campanha.titulo, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, height: 1.3)),
        const SizedBox(height: 4),
        Text(campanha.mensagem,
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontSize: 14.5, height: 1.45, color: Cores.textoSecundario)),
        const SizedBox(height: 12),
        if (campanha.respondeu)
          const Row(children: [
            Icon(Icons.check_circle_outline, size: 18, color: Cores.marca),
            SizedBox(width: 6),
            Expanded(
              child: Text('Obrigado. Já enviou um diagnóstico para esta campanha.',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: Cores.marca)),
            ),
          ])
        else if (cultura != null)
          OutlinedButton.icon(
            onPressed: aoResponder,
            icon: const Icon(Icons.photo_camera_outlined, size: 18),
            label: Text('Fotografar ${cultura.nome.toLowerCase()}'),
            style: OutlinedButton.styleFrom(minimumSize: const Size(0, 44), foregroundColor: Cores.marca),
          ),
      ]),
    );
  }
}
