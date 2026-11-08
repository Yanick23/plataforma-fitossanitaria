import 'package:flutter/material.dart';

import '../models/alerta.dart';
import '../services/alertas_locais.dart';
import '../services/catalogo.dart';
import '../services/sincronizacao.dart';
import '../tema.dart';
import '../widgets/botoes.dart';
import '../widgets/cartao_alerta.dart';
import '../widgets/informacao_patologia.dart';
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
      builder: (context) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.7,
        maxChildSize: 0.95,
        builder: (context, rolagem) => ListView(controller: rolagem, padding: const EdgeInsets.fromLTRB(20, 0, 20, 28), children: [
          CartaoAlerta(alerta: a.comLido(true), completo: true),
          if (patologia != null) ...[
            const SizedBox(height: 14),
            Text('${patologia.nomeLocal} · ${Cultura.porId(a.culturaId!).nome}',
                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
            Text(patologia.nomeCientifico,
                style: const TextStyle(fontStyle: FontStyle.italic, color: Cores.textoSecundario, fontSize: 13.5)),
            const SizedBox(height: 10),
            CartaoRecomendacao(patologia: patologia),
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
              child: ListView(padding: const EdgeInsets.fromLTRB(20, 4, 20, 24), children: [
                // O ícone fica alinhado com o texto (o botão tem margem própria).
                Align(alignment: Alignment.centerLeft, child: Transform.translate(offset: const Offset(-12, 0), child: const BotaoVoltar())),
                const SizedBox(height: 8),
                Text('Alertas da zona', style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 6),
                const Text('Avisos dos técnicos para a sua zona. Puxe para baixo para actualizar.',
                    style: TextStyle(fontSize: 15, color: Cores.textoSecundario, height: 1.4)),
                const SizedBox(height: 20),
                if (alertas.isEmpty)
                  const Padding(
                    padding: EdgeInsets.only(top: 60),
                    child: Column(children: [
                      Icon(Icons.notifications_none, size: 36, color: Cores.textoTerciario),
                      SizedBox(height: 14),
                      Text('Sem alertas para a sua zona', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),
                      SizedBox(height: 6),
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
