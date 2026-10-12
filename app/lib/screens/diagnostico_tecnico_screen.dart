import 'dart:io';

import 'package:flutter/material.dart';

import '../models/cultura.dart';
import '../models/medicao_inferencia.dart';
import '../services/classificador.dart';
import '../services/registo_tecnico.dart';
import '../tema.dart';
import '../widgets/botoes.dart';
import '../widgets/formatacao.dart';
import '../widgets/teste_fotografias.dart';

/// Diagnóstico técnico: tempos de inferência e memória (RNF03, RNF04).
/// Os mesmos valores são escritos no log ("AgroDiagnostico/...").
class DiagnosticoTecnicoScreen extends StatefulWidget {
  const DiagnosticoTecnicoScreen({super.key});

  @override
  State<DiagnosticoTecnicoScreen> createState() => _DiagnosticoTecnicoScreenState();
}

class _DiagnosticoTecnicoScreenState extends State<DiagnosticoTecnicoScreen> {
  Cultura _cultura = Cultura.milho;
  bool _aTestar = false;
  List<int>? _tempos;
  String? _erro;

  Future<void> _testar() async {
    setState(() {
      _aTestar = true;
      _erro = null;
      _tempos = null;
    });
    try {
      final tempos = await Classificador.instancia.testarDesempenho(_cultura);
      if (mounted) setState(() => _tempos = tempos);
    } on ErroModelo catch (e) {
      if (mounted) setState(() => _erro = e.mensagem);
    } finally {
      if (mounted) setState(() => _aTestar = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Diagnóstico técnico', style: TextStyle(fontWeight: FontWeight.w800))),
      body: ListenableBuilder(
        listenable: RegistoTecnico.instancia,
        builder: (context, _) {
          final medicoes = RegistoTecnico.instancia.medicoes;
          return ListView(padding: const EdgeInsets.fromLTRB(16, 4, 16, 24), children: [
            _Cartao(titulo: 'Dispositivo e memória', linhas: [
              ('Sistema', '${Platform.operatingSystem} ${Platform.operatingSystemVersion}'),
              ('Processadores', '${Platform.numberOfProcessors}'),
              ('Threads do Interpreter', '${Classificador.threads}'),
              ('Memória residente actual', formatarMb(ProcessInfo.currentRss)),
              ('Pico de memória residente', formatarMb(ProcessInfo.maxRss)),
            ]),
            const SizedBox(height: 12),
            _cartaoTeste(),
            const SizedBox(height: 12),
            const TesteFotografias(),
            const SizedBox(height: 12),
            FutureBuilder(
              future: RegistoTecnico.instancia.ficheiroCsv(),
              builder: (context, s) => _Cartao(titulo: 'Registo permanente (CSV)', linhas: [
                ('Ficheiro', s.data?.path ?? '…'),
              ]),
            ),
            const SizedBox(height: 12),
            _Cartao(
              titulo: 'Inferências desta sessão (${medicoes.length})',
              linhas: medicoes.isEmpty
                  ? [('—', 'Faça um diagnóstico para ver as medições.')]
                  : [
                      ('Média da inferência',
                          '${Estatisticas(medicoes.map((m) => m.inferenciaMs).toList()).media.toStringAsFixed(1)} ms'),
                      ('Média da confirmação ao resultado',
                          '${Estatisticas(medicoes.map((m) => m.tempoTotalMs).toList()).media.toStringAsFixed(1)} ms'),
                    ],
            ),
            for (final m in medicoes) ...[const SizedBox(height: 8), _Medicao(m)],
          ]);
        },
      ),
    );
  }

  Widget _cartaoTeste() {
    final e = _tempos == null ? null : Estatisticas(_tempos!);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Cores.cartao, borderRadius: BorderRadius.circular(16), boxShadow: sombraSuave),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('Teste de desempenho', style: TextStyle(fontWeight: FontWeight.w800)),
        const SizedBox(height: 4),
        const Text('20 inferências seguidas com uma imagem sintética (a 1.ª, de aquecimento, é descartada).',
            style: TextStyle(fontSize: 12, color: Cores.textoSecundario)),
        const SizedBox(height: 10),
        SegmentedButton<Cultura>(
          segments: [for (final c in Cultura.values) ButtonSegment(value: c, label: Text(c.nome))],
          selected: {_cultura},
          onSelectionChanged: _aTestar ? null : (s) => setState(() => _cultura = s.first),
        ),
        const SizedBox(height: 12),
        BotaoPrincipal(
          texto: _aTestar ? 'A medir...' : 'Executar teste',
          icone: Icons.speed,
          aoPremir: _aTestar ? null : _testar,
        ),
        if (_erro != null) ...[
          const SizedBox(height: 10),
          Text(_erro!, style: const TextStyle(color: Cores.laranjaEscuro)),
        ],
        if (e != null) ...[
          const SizedBox(height: 12),
          _linha('Média', '${e.media.toStringAsFixed(1)} ms'),
          _linha('Mínimo / máximo', '${e.minimo} / ${e.maximo} ms'),
          _linha('Pico de memória', formatarMb(ProcessInfo.maxRss)),
        ],
      ]),
    );
  }
}

Widget _linha(String rotulo, String valor) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Expanded(child: Text(rotulo, style: const TextStyle(color: Cores.textoSecundario, fontSize: 13))),
        const SizedBox(width: 12),
        Flexible(
          child: Text(valor,
              textAlign: TextAlign.right,
              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13, fontFeatures: [FontFeature.tabularFigures()])),
        ),
      ]),
    );

class _Cartao extends StatelessWidget {
  const _Cartao({required this.titulo, required this.linhas});

  final String titulo;
  final List<(String, String)> linhas;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Cores.cartao, borderRadius: BorderRadius.circular(16), boxShadow: sombraSuave),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(titulo, style: const TextStyle(fontWeight: FontWeight.w800)),
        const SizedBox(height: 8),
        for (final (r, v) in linhas) _linha(r, v),
      ]),
    );
  }
}

class _Medicao extends StatelessWidget {
  const _Medicao(this.m);

  final MedicaoInferencia m;

  @override
  Widget build(BuildContext context) {
    return _Cartao(titulo: '${m.cultura.nome} · ${formatarDataHora(m.data)}', linhas: [
      ('Da confirmação ao resultado', '${m.tempoTotalMs} ms'),
      ('Inferência (Interpreter.run)', '${m.inferenciaMs} ms'),
      ('Pré-processamento', '${m.preProcessamentoMs} ms'),
      ('Carregamento do modelo', m.carregamentoModeloMs == 0 ? 'já em memória' : '${m.carregamentoModeloMs} ms'),
      ('Versão do modelo', 'v${m.versaoModelo}'),
      ('Memória residente', formatarMb(m.memoriaRssBytes)),
      ('Tamanho do modelo', formatarMb(m.tamanhoModeloBytes)),
    ]);
  }
}
