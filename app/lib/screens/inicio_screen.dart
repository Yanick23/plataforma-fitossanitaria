import 'package:flutter/material.dart';

import '../main.dart';
import '../models/calendario.dart';
import '../models/cultura.dart';
import '../models/diagnostico.dart';
import '../services/acompanhamento.dart';
import '../services/alertas_locais.dart';
import '../services/dados_zona.dart';
import '../services/historial_db.dart';
import '../services/sessao.dart';
import '../tema.dart';
import '../widgets/cartao.dart';
import '../widgets/cartao_alerta.dart';
import '../widgets/cartoes_zona.dart';
import '../widgets/ecra_escuro.dart';
import '../widgets/seguimento.dart';
import 'calendario_screen.dart';
import 'cultura_screen.dart';
import 'historial_screen.dart';

/// Ecrã inicial: resumo dos diagnósticos, atalhos, o que a zona pede agora, os últimos
/// diagnósticos e o mês do calendário. A câmara está no botão redondo da barra inferior.
class InicioScreen extends StatelessWidget {
  const InicioScreen({super.key, this.diagnosticos});

  /// Diagnósticos já lidos (para pré-visualizações); sem eles, lê-se a base de dados.
  final List<Diagnostico>? diagnosticos;

  void _abrir(BuildContext context, Widget ecra) =>
      Navigator.of(context).push(MaterialPageRoute(builder: (_) => ecra));

  @override
  Widget build(BuildContext context) {
    final u = Sessao.instancia.utilizador.value;
    final nome = u?.nome.trim().split(RegExp(r'\s+')).first ?? '';
    return ValueListenableBuilder<int>(
      valueListenable: NavegacaoPrincipal.versaoHistorial,
      builder: (context, versao, _) => FutureBuilder<List<Diagnostico>>(
        key: ValueKey(versao),
        future: diagnosticos != null || u == null ? Future.value(diagnosticos ?? []) : HistorialDb.instancia.listar(u.id),
        initialData: diagnosticos,
        builder: (context, s) {
          final itens = s.data ?? const <Diagnostico>[];
          return EcraEscuro(
            local: u?.area,
            titulo: nome.isEmpty ? 'Como estão as suas plantas?' : 'Olá $nome, como estão as suas plantas?',
            direita: u == null ? null : AvatarIniciais(u.nome),
            filhos: [
              const Text('Resumo', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
              const SizedBox(height: 14),
              _CartaoResumo(itens: itens),
              const SizedBox(height: 22),
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                for (final c in Cultura.values)
                  _Atalho(
                    icone: c == Cultura.milho ? Icons.grass : Icons.spa_outlined,
                    nome: c.nome,
                    aoTocar: () => abrirCaptura(context, c),
                  ),
                _Atalho(
                  icone: Icons.calendar_month_outlined,
                  nome: 'Calendário',
                  aoTocar: () => _abrir(context, const CalendarioScreen()),
                ),
                _Atalho(
                  icone: Icons.notifications_none,
                  nome: 'Alertas',
                  aoTocar: () => NavegacaoPrincipal.abaActual.value = 2,
                ),
              ]),
              const SizedBox(height: 24),
              const Divider(),
              // O que a zona pede agora: alerta por ler, pedido do técnico, seguimento.
              ListenableBuilder(
                listenable: Listenable.merge([AlertasLocais.instancia, CampanhasLocais.instancia, Acompanhamento.instancia]),
                builder: (context, _) {
                  final alerta = AlertasLocais.instancia.ultimoNaoLido;
                  final campanhas = CampanhasLocais.instancia.activas;
                  final seguimento = Acompanhamento.instancia.porResponder;
                  final cartoes = <Widget>[
                    if (alerta != null)
                      CartaoAlerta(alerta: alerta, aoTocar: () => NavegacaoPrincipal.abaActual.value = 2),
                    if (campanhas.isNotEmpty)
                      CartaoCampanha(
                        campanha: campanhas.first,
                        aoResponder: () {
                          final c = Cultura.talvez(campanhas.first.culturaId);
                          c == null ? _abrir(context, const CulturaScreen()) : abrirCaptura(context, c);
                        },
                      ),
                    if (seguimento.isNotEmpty) CartaoSeguimento(diagnostico: seguimento.first),
                  ];
                  if (cartoes.isEmpty) return const SizedBox.shrink();
                  return Padding(
                    padding: const EdgeInsets.only(top: 24),
                    child: Seccao(
                      titulo: 'Na sua zona',
                      accao: LigacaoTitulo('Ver alertas', aoTocar: () => NavegacaoPrincipal.abaActual.value = 2),
                      filhos: cartoes,
                    ),
                  );
                },
              ),
              const SizedBox(height: 28),
              Seccao(
                titulo: 'Últimos diagnósticos',
                accao: itens.length > 3
                    ? LigacaoTitulo('Ver todos', aoTocar: () => NavegacaoPrincipal.abaActual.value = 1)
                    : null,
                espaco: 4,
                filhos: itens.isEmpty
                    ? [
                        const Text(
                            'Ainda não fotografou nenhuma planta. Quando encontrar uma folha com manchas, furos ou '
                                'lagartas, toque no botão verde da câmara, em baixo.',
                            style: TextStyle(fontSize: 15, height: 1.5, color: Cores.textoSecundario)),
                      ]
                    : [for (final d in itens.take(3)) LinhaDiagnostico(d)],
              ),
              ListenableBuilder(
                listenable: CalendarioLocal.instancia,
                builder: (context, _) {
                  final c = CalendarioLocal.instancia.calendario;
                  if (c == null) return const SizedBox.shrink();
                  final mes = DateTime.now().month;
                  return Padding(
                    padding: const EdgeInsets.only(top: 28),
                    child: Seccao(
                      titulo: 'Em ${Calendario.nomesMeses[mes - 1].toLowerCase()}',
                      accao: LigacaoTitulo('Calendário', aoTocar: () => _abrir(context, const CalendarioScreen())),
                      filhos: [
                        CartaoCalendario(calendario: c, mes: mes, aoTocar: () => _abrir(context, const CalendarioScreen())),
                      ],
                    ),
                  );
                },
              ),
            ],
          );
        },
      ),
    );
  }
}

/// Cartão verde-lima com os números dos diagnósticos do agricultor.
class _CartaoResumo extends StatelessWidget {
  const _CartaoResumo({required this.itens});

  final List<Diagnostico> itens;

  @override
  Widget build(BuildContext context) {
    final porEnviar = itens.where((d) => d.estadoSinc == EstadoSinc.pendente).length;
    final confirmados = itens.where((d) => d.validacao == Validacao.confirmado).length;
    final semana = itens.where((d) => DateTime.now().difference(d.data).inDays < 7).length;
    Widget numero(IconData icone, String rotulo, int valor) => Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(8)),
                child: Icon(icone, size: 18, color: Cores.sobreLima),
              ),
              const SizedBox(width: 8),
              Flexible(child: Text(rotulo, style: const TextStyle(fontSize: 14.5, color: Cores.marca))),
            ]),
            const SizedBox(height: 8),
            Text('$valor', style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700, color: Cores.sobreLima)),
          ]),
        );
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 18, 20, 20),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        gradient: const LinearGradient(
            colors: [Color(0xFFB4EE85), Cores.limaForte], begin: Alignment.topLeft, end: Alignment.bottomRight),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Diagnósticos', style: TextStyle(fontSize: 15, color: Cores.marca)),
              const SizedBox(height: 2),
              Text('${itens.length}', style: const TextStyle(fontSize: 30, fontWeight: FontWeight.w700, color: Cores.sobreLima)),
            ]),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
            child: Text(semana == 1 ? '1 esta semana' : '$semana esta semana',
                style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600, color: Cores.sobreLima)),
          ),
        ]),
        const SizedBox(height: 16),
        Row(children: [
          numero(Icons.schedule, 'Por enviar', porEnviar),
          const SizedBox(width: 12),
          numero(Icons.verified_outlined, 'Confirmados', confirmados),
        ]),
      ]),
    );
  }
}

/// Atalho: círculo verde-escuro com ícone e o nome por baixo.
class _Atalho extends StatelessWidget {
  const _Atalho({required this.icone, required this.nome, required this.aoTocar});

  final IconData icone;
  final String nome;
  final VoidCallback aoTocar;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: nome,
      excludeSemantics: true,
      child: InkResponse(
        onTap: aoTocar,
        radius: 44,
        child: SizedBox(
          width: 78,
          child: Column(children: [
            CirculoIcone(icone, tamanho: 60),
            const SizedBox(height: 8),
            Text(nome, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 14.5)),
          ]),
        ),
      ),
    );
  }
}
