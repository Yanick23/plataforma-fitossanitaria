import 'package:flutter/material.dart';

import '../models/alerta.dart';
import '../services/alertas_locais.dart';
import '../services/catalogo.dart';
import '../services/sincronizacao.dart';
import '../tema.dart';
import '../widgets/botoes.dart';
import '../widgets/ecra_escuro.dart';
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
      builder: (context) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.7,
        maxChildSize: 0.95,
        builder: (context, rolagem) => ListView(controller: rolagem, padding: const EdgeInsets.only(bottom: 20), children: [
          CartaoAlerta(alerta: a.comLido(true), completo: true),
          if (patologia != null) ...[
            CartaoRecomendacao(patologia: patologia),
          ],
          const Divider(),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: BotaoSecundario(texto: 'Fechar', aoPremir: () => Navigator.of(context).pop()),
          ),
        ]),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: AlertasLocais.instancia,
      builder: (context, _) {
        final alertas = AlertasLocais.instancia.alertas;
        final n = AlertasLocais.instancia.naoLidos;
        return EcraEscuro(
          titulo: 'Alertas da zona',
          subtitulo: n == 0
              ? 'Avisos que os técnicos mandaram para a sua zona.'
              : (n == 1 ? '1 alerta por ler.' : '$n alertas por ler.'),
          aoActualizar: () => Sincronizacao.instancia.sincronizar(),
          filhos: alertas.isEmpty
              ? [
                  const Padding(
                    padding: EdgeInsets.fromLTRB(16, 40, 16, 0),
                    child: Column(children: [
                      CirculoIcone(Icons.notifications_none, tamanho: 72),
                      SizedBox(height: 18),
                      Text('Sem alertas', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600)),
                      SizedBox(height: 6),
                      Text('Quando um técnico mandar um aviso para a sua zona, aparece aqui.',
                          textAlign: TextAlign.center,
                          style: TextStyle(fontSize: 15, color: Cores.textoSecundario, height: 1.45)),
                    ]),
                  ),
                ]
              : [
                  for (final (i, a) in alertas.indexed) ...[
                    if (i > 0) const SizedBox(height: 12),
                    CartaoAlerta(alerta: a, aoTocar: () => _abrir(context, a)),
                  ],
                ],
        );
      },
    );
  }
}
