import 'package:flutter/material.dart';

import '../models/calendario.dart';
import '../models/cultura.dart';
import '../services/dados_zona.dart';
import '../tema.dart';

/// Calendário agrícola da província (funcionalidade 10): o ano todo, o mês actual primeiro,
/// com as fontes. Funciona sem rede (guardado na última sincronização).
class CalendarioScreen extends StatelessWidget {
  const CalendarioScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final c = CalendarioLocal.instancia.calendario;
    final actual = DateTime.now().month;
    return Scaffold(
      backgroundColor: Cores.fundo,
      appBar: AppBar(title: const Text('Calendário agrícola')),
      body: c == null
          ? const Center(
              child: Padding(
                padding: EdgeInsets.all(32),
                child: Text('O calendário chega na próxima sincronização.', textAlign: TextAlign.center),
              ),
            )
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text(
                  '${c.provincia} · região ${c.regiao}',
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
                ),
                if (c.sementeira != null) ...[
                  const SizedBox(height: 4),
                  Text('Sementeira habitual: ${c.sementeira}', style: const TextStyle(color: Cores.textoSecundario)),
                ],
                const SizedBox(height: 12),
                // Do mês actual até ao fim do ano agrícola: os próximos 12 meses.
                for (var i = 0; i < 12; i++) _Mes(mes: c.mes((actual - 1 + i) % 12 + 1), actual: i == 0),
                const SizedBox(height: 12),
                Text(c.aviso, style: const TextStyle(fontSize: 12, color: Cores.textoSecundario, height: 1.4)),
                const SizedBox(height: 8),
                const Text('Fontes', style: TextStyle(fontWeight: FontWeight.w600)),
                for (final f in c.fontes.values)
                  Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text('• $f', style: const TextStyle(fontSize: 12, color: Cores.textoSecundario)),
                  ),
              ],
            ),
    );
  }
}

class _Mes extends StatelessWidget {
  const _Mes({required this.mes, required this.actual});

  final MesCalendario mes;
  final bool actual;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: decoracaoCartao(
        cor: actual ? Cores.marcaSuave : Cores.cartao,
        borda: actual ? Cores.marca : Cores.linha,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            actual ? '${Calendario.nomesMeses[mes.mes - 1]} (este mês)' : Calendario.nomesMeses[mes.mes - 1],
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
          if (mes.actividades.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(mes.actividades.join(' · '), style: const TextStyle(fontSize: 14, color: Cores.textoSecundario)),
          ],
          for (final a in mes.avisos) ...[
            const SizedBox(height: 6),
            Text('${Cultura.nomeDe(a.culturaId)}: ${a.texto}', style: const TextStyle(fontSize: 14.5, height: 1.45)),
          ],
        ],
      ),
    );
  }
}
