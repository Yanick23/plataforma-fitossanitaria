import 'package:flutter/material.dart';

import '../main.dart';
import '../services/acompanhamento.dart';
import '../services/alertas_locais.dart';
import '../services/dados_zona.dart';
import '../tema.dart';
import '../widgets/botoes.dart';
import '../widgets/cartao_alerta.dart';
import '../widgets/cartoes_zona.dart';
import '../widgets/estado_ligacao.dart';
import '../widgets/seguimento.dart';
import 'alertas_screen.dart';
import 'calendario_screen.dart';
import 'cultura_screen.dart';
import 'definicoes_screen.dart';
import 'diagnostico_tecnico_screen.dart';

/// Ecrã 1 — Ecrã inicial: estado da ligação e acesso ao diagnóstico e ao historial.
class InicioScreen extends StatelessWidget {
  const InicioScreen({super.key});

  void _abrirAlertas(BuildContext context) =>
      Navigator.of(context).push(MaterialPageRoute(builder: (_) => const AlertasScreen()));

  @override
  Widget build(BuildContext context) {
    // Deslizável quando os cartões (alerta, campanha, calendário, seguimento) não cabem no ecrã;
    // quando cabem, os espaços flexíveis mantêm o aspecto original.
    return SafeArea(
      child: LayoutBuilder(
        builder: (context, limites) => SingleChildScrollView(
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: limites.maxHeight),
            child: IntrinsicHeight(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
                child: Column(
                  children: [
                    Row(
                      children: [
                        IconButton(
                          tooltip: 'Diagnóstico técnico (desempenho)',
                          icon: const Icon(Icons.speed_outlined, color: Cores.textoSecundario),
                          onPressed: () => Navigator.of(
                            context,
                          ).push(MaterialPageRoute(builder: (_) => const DiagnosticoTecnicoScreen())),
                        ),
                        IconButton(
                          tooltip: 'Definições',
                          icon: const Icon(Icons.settings_outlined, color: Cores.textoSecundario),
                          onPressed: () =>
                              Navigator.of(context).push(MaterialPageRoute(builder: (_) => const DefinicoesScreen())),
                        ),
                        ListenableBuilder(
                          listenable: AlertasLocais.instancia,
                          builder: (context, _) {
                            final n = AlertasLocais.instancia.naoLidos;
                            return IconButton(
                              tooltip: n == 0 ? 'Alertas' : 'Alertas: $n por ler',
                              icon: Badge(
                                isLabelVisible: n > 0,
                                label: Text('$n'),
                                child: const Icon(Icons.notifications_outlined, color: Cores.textoSecundario),
                              ),
                              onPressed: () => _abrirAlertas(context),
                            );
                          },
                        ),
                        const Spacer(),
                        const EstadoLigacao(),
                      ],
                    ),
                    const Spacer(flex: 2),
                    Container(
                      width: 84,
                      height: 84,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [Cores.verde, Cores.verdeEscuro],
                        ),
                        borderRadius: BorderRadius.circular(24),
                        boxShadow: [
                          BoxShadow(
                            color: Cores.verde.withValues(alpha: 0.35),
                            blurRadius: 20,
                            offset: const Offset(0, 8),
                          ),
                        ],
                      ),
                      child: const Icon(Icons.eco, color: Colors.white, size: 44),
                    ),
                    const SizedBox(height: 22),
                    const Text(
                      'Diagnóstico de culturas',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Tire uma foto e saiba na hora o que está a afectar a sua plantação',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 14, color: Cores.textoSecundario, height: 1.4),
                    ),
                    const Spacer(flex: 3),
                    // Último alerta por ler da zona do agricultor (chega na sincronização).
                    ListenableBuilder(
                      listenable: AlertasLocais.instancia,
                      builder: (context, _) {
                        final alerta = AlertasLocais.instancia.ultimoNaoLido;
                        if (alerta == null) return const SizedBox.shrink();
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 16),
                          child: CartaoAlerta(alerta: alerta, aoTocar: () => _abrirAlertas(context)),
                        );
                      },
                    ),
                    // Campanha de vigilância a decorrer na zona (a que ainda não teve resposta primeiro).
                    ListenableBuilder(
                      listenable: CampanhasLocais.instancia,
                      builder: (context, _) {
                        final campanhas = CampanhasLocais.instancia.activas;
                        if (campanhas.isEmpty) return const SizedBox.shrink();
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 16),
                          child: CartaoCampanha(
                            campanha: campanhas.first,
                            aoResponder: () =>
                                Navigator.of(context).push(MaterialPageRoute(builder: (_) => const CulturaScreen())),
                          ),
                        );
                      },
                    ),
                    // «Nesta altura…»: o mês actual do calendário agrícola da província.
                    ListenableBuilder(
                      listenable: CalendarioLocal.instancia,
                      builder: (context, _) {
                        final calendario = CalendarioLocal.instancia.calendario;
                        if (calendario == null) return const SizedBox.shrink();
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 16),
                          child: CartaoCalendario(
                            calendario: calendario,
                            mes: DateTime.now().month,
                            aoTocar: () =>
                                Navigator.of(context).push(MaterialPageRoute(builder: (_) => const CalendarioScreen())),
                          ),
                        );
                      },
                    ),
                    // Seguimento do tratamento: o diagnóstico mais antigo à espera de resposta.
                    ListenableBuilder(
                      listenable: Acompanhamento.instancia,
                      builder: (context, _) {
                        final pendentes = Acompanhamento.instancia.porResponder;
                        if (pendentes.isEmpty) return const SizedBox.shrink();
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 16),
                          child: CartaoSeguimento(diagnostico: pendentes.first),
                        );
                      },
                    ),
                    BotaoPrincipal(
                      texto: 'Diagnosticar Planta',
                      icone: Icons.photo_camera,
                      aoPremir: () =>
                          Navigator.of(context).push(MaterialPageRoute(builder: (_) => const CulturaScreen())),
                    ),
                    const SizedBox(height: 12),
                    BotaoSecundario(texto: 'Ver Historial', aoPremir: () => NavegacaoPrincipal.abaActual.value = 1),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
