import 'package:flutter/material.dart';

import '../models/alerta.dart';
import '../services/alertas_locais.dart';
import '../services/catalogo.dart';
import '../services/sincronizacao.dart';
import '../tema.dart';
import '../widgets/botoes.dart';
import '../widgets/cartao_alerta.dart';
import '../models/cultura.dart';

/// Alertas enviados pelo técnico ou pelo administrador para a zona do agricultor.
/// Funcionam sem rede: chegam na sincronização e ficam guardados no telemóvel.
class AlertasScreen extends StatelessWidget {
  const AlertasScreen({super.key});

  Future<void> _abrir(BuildContext context, Alerta a) async {
    await AlertasLocais.instancia.marcarLido(a.id);
    if (!context.mounted) return;
    final patologia = a.patologiaCodigo == null || a.culturaId == null
        ? null
        : Catalogo.instancia.patologia(Cultura.porId(a.culturaId!), a.patologiaCodigo!);
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Cores.fundo,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (context) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.7,
        maxChildSize: 0.95,
        builder: (context, rolagem) => ListView(controller: rolagem, padding: const EdgeInsets.fromLTRB(20, 12, 20, 28), children: [
          Center(
            child: Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.black26, borderRadius: BorderRadius.circular(2))),
          ),
          const SizedBox(height: 16),
          CartaoAlerta(alerta: a.comLido(true), completo: true),
          if (patologia != null) ...[
            const SizedBox(height: 14),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: Cores.verdeClaro, borderRadius: BorderRadius.circular(16)),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('${patologia.nomeLocal} (${Cultura.porId(a.culturaId!).nome.toLowerCase()})',
                    style: const TextStyle(fontWeight: FontWeight.w800, color: Cores.verdeEscuro)),
                Text(patologia.nomeCientifico, style: const TextStyle(fontStyle: FontStyle.italic, color: Cores.textoSecundario)),
                const SizedBox(height: 8),
                const Text('O que fazer', style: TextStyle(fontWeight: FontWeight.w700)),
                const SizedBox(height: 4),
                Text(patologia.recomendacao, style: const TextStyle(height: 1.4)),
              ]),
            ),
          ],
          const SizedBox(height: 18),
          BotaoSecundario(texto: 'Fechar', aoPremir: () => Navigator.of(context).pop()),
        ]),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: ListenableBuilder(
          listenable: AlertasLocais.instancia,
          builder: (context, _) {
            final alertas = AlertasLocais.instancia.alertas;
            return RefreshIndicator(
              onRefresh: () => Sincronizacao.instancia.sincronizar(),
              child: ListView(padding: const EdgeInsets.fromLTRB(20, 12, 20, 24), children: [
                const Align(alignment: Alignment.centerLeft, child: BotaoVoltar()),
                const SizedBox(height: 16),
                const Text('Alertas', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800)),
                const SizedBox(height: 4),
                const Text('Avisos dos técnicos para a sua zona. Puxe para baixo para actualizar.',
                    style: TextStyle(color: Cores.textoSecundario)),
                const SizedBox(height: 18),
                if (alertas.isEmpty)
                  const Padding(
                    padding: EdgeInsets.only(top: 60),
                    child: Column(children: [
                      Icon(Icons.notifications_none, size: 48, color: Cores.textoSecundario),
                      SizedBox(height: 10),
                      Text('Sem alertas para a sua zona', style: TextStyle(fontWeight: FontWeight.w700)),
                      SizedBox(height: 4),
                      Text('Quando um técnico enviar um aviso, aparece aqui.',
                          textAlign: TextAlign.center, style: TextStyle(color: Cores.textoSecundario)),
                    ]),
                  )
                else
                  for (final a in alertas) ...[
                    CartaoAlerta(alerta: a, aoTocar: () => _abrir(context, a)),
                    const SizedBox(height: 10),
                  ],
              ]),
            );
          },
        ),
      ),
    );
  }
}
