import 'package:flutter/material.dart';

import '../models/calendario.dart';
import '../models/campanha.dart';
import '../models/cultura.dart';
import '../tema.dart';
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
    return Material(
      color: Cores.cartao,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: aoTocar,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.calendar_month_outlined, size: 18, color: Cores.verdeEscuro),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      'Nesta altura · ${Calendario.nomesMeses[mes - 1]}, ${calendario.provincia}',
                      style: const TextStyle(fontWeight: FontWeight.w800, color: Cores.verdeEscuro),
                    ),
                  ),
                  const Icon(Icons.chevron_right, color: Cores.textoSecundario),
                ],
              ),
              if (m.actividades.isNotEmpty) ...[
                const SizedBox(height: 6),
                Text(m.actividades.join(' · '), style: const TextStyle(fontSize: 13, color: Cores.textoSecundario)),
              ],
              for (final a in m.avisos.take(2)) ...[
                const SizedBox(height: 8),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Padding(
                      padding: EdgeInsets.only(top: 2),
                      child: Icon(Icons.visibility_outlined, size: 16, color: Cores.texto),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        '${Cultura.nomeDe(a.culturaId)}: ${a.texto}',
                        style: const TextStyle(height: 1.35, color: Cores.texto),
                      ),
                    ),
                  ],
                ),
              ],
              if (m.avisos.length > 2)
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(
                    'E mais ${m.avisos.length - 2}. Toque para ver o calendário.',
                    style: const TextStyle(fontSize: 12, color: Cores.textoSecundario),
                  ),
                ),
            ],
          ),
        ),
      ),
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
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Cores.cartao,
        borderRadius: BorderRadius.circular(16),
        border: Border(
          left: BorderSide(color: Cores.verdeEscuro, width: campanha.respondeu ? 0 : 4),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.campaign_outlined, size: 18, color: Cores.verdeEscuro),
              const SizedBox(width: 6),
              const Text(
                'Campanha de vigilância',
                style: TextStyle(fontWeight: FontWeight.w700, color: Cores.verdeEscuro),
              ),
              const Spacer(),
              Text(
                'até ${formatarData(campanha.fim)}',
                style: const TextStyle(fontSize: 12, color: Cores.textoSecundario),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(campanha.titulo, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
          const SizedBox(height: 4),
          Text(
            campanha.mensagem,
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(height: 1.4, color: Cores.texto),
          ),
          const SizedBox(height: 10),
          if (campanha.respondeu)
            const Row(
              children: [
                Icon(Icons.check_circle, size: 18, color: Cores.verdeEscuro),
                SizedBox(width: 6),
                Expanded(
                  child: Text(
                    'Obrigado! Já enviou um diagnóstico para esta campanha.',
                    style: TextStyle(fontWeight: FontWeight.w600, color: Cores.verdeEscuro),
                  ),
                ),
              ],
            )
          else if (cultura != null)
            Align(
              alignment: Alignment.centerLeft,
              child: FilledButton.icon(
                onPressed: aoResponder,
                icon: const Icon(Icons.photo_camera, size: 18),
                label: Text('Fotografar ${cultura.nome.toLowerCase()}'),
              ),
            ),
        ],
      ),
    );
  }
}
