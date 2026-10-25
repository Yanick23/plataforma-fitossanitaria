import 'package:flutter/material.dart';

import '../main.dart';
import '../services/alertas_locais.dart';
import '../tema.dart';
import '../widgets/botoes.dart';
import '../widgets/cartao_alerta.dart';
import '../widgets/estado_ligacao.dart';
import 'alertas_screen.dart';
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
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
        child: Column(children: [
          Row(children: [
            IconButton(
              tooltip: 'Diagnóstico técnico (desempenho)',
              icon: const Icon(Icons.speed_outlined, color: Cores.textoSecundario),
              onPressed: () => Navigator.of(context)
                  .push(MaterialPageRoute(builder: (_) => const DiagnosticoTecnicoScreen())),
            ),
            IconButton(
              tooltip: 'Definições',
              icon: const Icon(Icons.settings_outlined, color: Cores.textoSecundario),
              onPressed: () => Navigator.of(context)
                  .push(MaterialPageRoute(builder: (_) => const DefinicoesScreen())),
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
          ]),
          const Spacer(flex: 2),
          Container(
            width: 84,
            height: 84,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                  begin: Alignment.topLeft, end: Alignment.bottomRight, colors: [Cores.verde, Cores.verdeEscuro]),
              borderRadius: BorderRadius.circular(24),
              boxShadow: [BoxShadow(color: Cores.verde.withValues(alpha: 0.35), blurRadius: 20, offset: const Offset(0, 8))],
            ),
            child: const Icon(Icons.eco, color: Colors.white, size: 44),
          ),
          const SizedBox(height: 22),
          const Text('Diagnóstico de culturas', textAlign: TextAlign.center, style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800)),
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
          BotaoPrincipal(
            texto: 'Diagnosticar Planta',
            icone: Icons.photo_camera,
            aoPremir: () => Navigator.of(context)
                .push(MaterialPageRoute(builder: (_) => const CulturaScreen())),
          ),
          const SizedBox(height: 12),
          BotaoSecundario(
            texto: 'Ver Historial',
            aoPremir: () => NavegacaoPrincipal.abaActual.value = 1,
          ),
        ]),
      ),
    );
  }
}
