import 'package:flutter/material.dart';

import '../main.dart';
import '../models/cultura.dart';
import '../services/acompanhamento.dart';
import '../services/alertas_locais.dart';
import '../services/dados_zona.dart';
import '../services/sessao.dart';
import '../tema.dart';
import '../widgets/botoes.dart';
import '../widgets/cartao_alerta.dart';
import '../widgets/cartoes_zona.dart';
import '../widgets/estado_ligacao.dart';
import '../widgets/seguimento.dart';
import 'alertas_screen.dart';
import 'calendario_screen.dart';
import 'captura_screen.dart';
import 'cultura_screen.dart';
import 'definicoes_screen.dart';

/// Ecrã inicial: diagnosticar (a acção principal), o que a zona pede agora e o resto da app.
class InicioScreen extends StatelessWidget {
  const InicioScreen({super.key});

  static String saudacao(DateTime agora) =>
      agora.hour < 12 ? 'Bom dia' : (agora.hour < 18 ? 'Boa tarde' : 'Boa noite');

  void _abrir(BuildContext context, Widget ecra, {String? rota}) => Navigator.of(context)
      .push(MaterialPageRoute(settings: RouteSettings(name: rota), builder: (_) => ecra));

  void _fotografar(BuildContext context, Cultura c) =>
      _abrir(context, CapturaScreen(cultura: c), rota: CapturaScreen.rota);

  @override
  Widget build(BuildContext context) {
    final u = Sessao.instancia.utilizador.value;
    final nome = u?.nome.trim().split(RegExp(r'\s+')).first ?? '';
    return SafeArea(
      child: ListView(padding: const EdgeInsets.fromLTRB(20, 12, 12, 28), children: [
        // Topo: saudação, zona e ligação; alertas e definições.
        Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(nome.isEmpty ? saudacao(DateTime.now()) : '${saudacao(DateTime.now())}, $nome',
                    style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 6),
                Wrap(spacing: 10, runSpacing: 6, crossAxisAlignment: WrapCrossAlignment.center, children: [
                  if (u?.area != null)
                    Row(mainAxisSize: MainAxisSize.min, children: [
                      const Icon(Icons.place_outlined, size: 15, color: Cores.textoSecundario),
                      const SizedBox(width: 3),
                      Text(u!.area!, style: const TextStyle(fontSize: 13.5, color: Cores.textoSecundario)),
                    ]),
                  const EstadoLigacao(),
                ]),
              ]),
            ),
          ),
          ListenableBuilder(
            listenable: AlertasLocais.instancia,
            builder: (context, _) {
              final n = AlertasLocais.instancia.naoLidos;
              return IconButton(
                tooltip: n == 0 ? 'Alertas' : 'Alertas: $n por ler',
                icon: Badge(isLabelVisible: n > 0, label: Text('$n'), child: const Icon(Icons.notifications_none)),
                onPressed: () => _abrir(context, const AlertasScreen()),
              );
            },
          ),
          IconButton(
            tooltip: 'Definições',
            icon: const Icon(Icons.settings_outlined),
            onPressed: () => _abrir(context, const DefinicoesScreen()),
          ),
        ]),
        const SizedBox(height: 20),
        Padding(
          padding: const EdgeInsets.only(right: 8),
          child: _CartaoDiagnosticar(aoEscolher: (c) => _fotografar(context, c)),
        ),
        // «Para si»: alerta por ler, campanha, seguimento e o mês do calendário.
        Padding(
          padding: const EdgeInsets.only(right: 8),
          child: ListenableBuilder(
            listenable: Listenable.merge(
                [AlertasLocais.instancia, CampanhasLocais.instancia, CalendarioLocal.instancia, Acompanhamento.instancia]),
            builder: (context, _) {
              final alerta = AlertasLocais.instancia.ultimoNaoLido;
              final campanhas = CampanhasLocais.instancia.activas;
              final seguimento = Acompanhamento.instancia.porResponder;
              final calendario = CalendarioLocal.instancia.calendario;
              final cartoes = <Widget>[
                if (alerta != null) CartaoAlerta(alerta: alerta, aoTocar: () => _abrir(context, const AlertasScreen())),
                if (campanhas.isNotEmpty)
                  CartaoCampanha(
                    campanha: campanhas.first,
                    aoResponder: () {
                      final c = Cultura.talvez(campanhas.first.culturaId);
                      c == null ? _abrir(context, const CulturaScreen()) : _fotografar(context, c);
                    },
                  ),
                if (seguimento.isNotEmpty) CartaoSeguimento(diagnostico: seguimento.first),
                if (calendario != null)
                  CartaoCalendario(
                    calendario: calendario,
                    mes: DateTime.now().month,
                    aoTocar: () => _abrir(context, const CalendarioScreen()),
                  ),
              ];
              if (cartoes.isEmpty) return const SizedBox.shrink();
              return Padding(
                padding: const EdgeInsets.only(top: 28),
                child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                  const TituloSeccao('Para si'),
                  for (final (i, c) in cartoes.indexed) ...[if (i > 0) const SizedBox(height: 10), c],
                ]),
              );
            },
          ),
        ),
        const SizedBox(height: 28),
        const Padding(padding: EdgeInsets.only(right: 8), child: TituloSeccao('Mais')),
        Padding(
          padding: const EdgeInsets.only(right: 8),
          child: Material(
            color: Cores.cartao,
            clipBehavior: Clip.antiAlias,
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12), side: const BorderSide(color: Cores.linha)),
            child: Column(children: [
              _Linha(
                icone: Icons.history,
                titulo: 'Historial',
                subtitulo: 'Os seus diagnósticos e o envio ao técnico',
                aoTocar: () => NavegacaoPrincipal.abaActual.value = 1,
              ),
              const Divider(indent: 56),
              ListenableBuilder(
                listenable: AlertasLocais.instancia,
                builder: (context, _) {
                  final n = AlertasLocais.instancia.naoLidos;
                  return _Linha(
                    icone: Icons.notifications_none,
                    titulo: 'Alertas da zona',
                    subtitulo: n == 0 ? 'Nenhum por ler' : (n == 1 ? '1 por ler' : '$n por ler'),
                    aoTocar: () => _abrir(context, const AlertasScreen()),
                  );
                },
              ),
              const Divider(indent: 56),
              _Linha(
                icone: Icons.calendar_month_outlined,
                titulo: 'Calendário agrícola',
                subtitulo: 'O que fazer em cada mês na sua província',
                aoTocar: () => _abrir(context, const CalendarioScreen()),
              ),
            ]),
          ),
        ),
      ]),
    );
  }
}

/// A acção principal: fotografar uma folha. Escolhe-se logo a cultura (um toque a menos).
class _CartaoDiagnosticar extends StatelessWidget {
  const _CartaoDiagnosticar({required this.aoEscolher});

  final ValueChanged<Cultura> aoEscolher;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 18),
      decoration: BoxDecoration(color: Cores.marca, borderRadius: BorderRadius.circular(14)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(10)),
          child: const Icon(Icons.photo_camera_outlined, color: Colors.white, size: 22),
        ),
        const SizedBox(height: 14),
        const Text('Diagnosticar uma planta',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600, color: Colors.white, height: 1.25)),
        const SizedBox(height: 4),
        Text('Fotografe uma folha com sintomas. O resultado aparece em segundos, mesmo sem internet.',
            style: TextStyle(fontSize: 14.5, height: 1.45, color: Colors.white.withValues(alpha: 0.86))),
        const SizedBox(height: 16),
        Row(children: [
          for (final (i, c) in Cultura.values.indexed) ...[
            if (i > 0) const SizedBox(width: 10),
            Expanded(
              child: FilledButton(
                onPressed: () => aoEscolher(c),
                style: FilledButton.styleFrom(
                  backgroundColor: Colors.white,
                  foregroundColor: Cores.marcaForte,
                  minimumSize: const Size(0, 48),
                ),
                child: Text(c.nome),
              ),
            ),
          ],
        ]),
      ]),
    );
  }
}

class _Linha extends StatelessWidget {
  const _Linha({required this.icone, required this.titulo, required this.subtitulo, required this.aoTocar});

  final IconData icone;
  final String titulo;
  final String subtitulo;
  final VoidCallback aoTocar;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icone, color: Cores.textoSecundario),
      title: Text(titulo),
      subtitle: Text(subtitulo),
      trailing: const Icon(Icons.chevron_right, color: Cores.textoTerciario),
      onTap: aoTocar,
    );
  }
}
