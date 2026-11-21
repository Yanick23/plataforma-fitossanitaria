import 'package:flutter/material.dart';

import '../models/cultura.dart';
import '../models/resultado_classificacao.dart';
import '../services/classificador.dart';
import '../tema.dart';
import '../widgets/botoes.dart';
import '../widgets/ecra_escuro.dart';
import 'resultado_screen.dart';

/// Ecrã 4 — Processamento: executa a inferência e abre o resultado (RF02).
class ProcessamentoScreen extends StatefulWidget {
  const ProcessamentoScreen({
    super.key,
    required this.cultura,
    required this.caminhoImagem,
    required this.cronometro,
    required this.dataCaptura,
    this.anterior,
  });

  final Cultura cultura;
  final ResultadoClassificacao? anterior; // fotos já analisadas da mesma planta
  final String caminhoImagem;
  final Stopwatch cronometro;
  final DateTime dataCaptura;

  @override
  State<ProcessamentoScreen> createState() => _ProcessamentoScreenState();
}

class _ProcessamentoScreenState extends State<ProcessamentoScreen> {
  String? _erro;

  @override
  void initState() {
    super.initState();
    // Espera pelo primeiro frame para o indicador aparecer antes da inferência.
    WidgetsBinding.instance.addPostFrameCallback((_) => _executar());
  }

  Future<void> _executar() async {
    try {
      final resultado = await Classificador.instancia.classificar(
        widget.cultura,
        widget.caminhoImagem,
        cronometroTotal: widget.cronometro,
        dataCaptura: widget.dataCaptura,
      );
      if (!mounted) return;
      final anterior = widget.anterior;
      // Se o modelo mudou entretanto (sincronização a meio), não se misturam versões.
      final combinado =
          anterior != null && anterior.versaoModelo == resultado.versaoModelo ? anterior.juntar(resultado) : resultado;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => ResultadoScreen(resultado: combinado)),
      );
    } on ErroModelo catch (e) {
      if (mounted) setState(() => _erro = e.mensagem);
    } catch (e) {
      if (mounted) setState(() => _erro = 'Ocorreu um erro inesperado durante o diagnóstico.\n$e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Cores.escuro,
      body: DecoratedBox(
        decoration: fundoEscuro,
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: Center(child: _erro == null ? _aProcessar() : _comErro()),
          ),
        ),
      ),
    );
  }

  Widget _aProcessar() => Column(mainAxisSize: MainAxisSize.min, children: [
        Container(
          width: 96,
          height: 96,
          padding: const EdgeInsets.all(30),
          decoration: const BoxDecoration(
            shape: BoxShape.circle,
            gradient: LinearGradient(colors: [Color(0xFFC2F29A), Cores.limaForte], begin: Alignment.topLeft, end: Alignment.bottomRight),
          ),
          child: const CircularProgressIndicator(strokeWidth: 3.5, strokeCap: StrokeCap.round, color: Cores.escuro),
        ),
        const SizedBox(height: 28),
        const Text('A analisar…', style: TextStyle(fontSize: 30, fontWeight: FontWeight.w700, color: Colors.white)),
        const SizedBox(height: 8),
        const Text('A procurar sinais de pragas e doenças na folha.',
            textAlign: TextAlign.center, style: TextStyle(fontSize: 16, color: Cores.sobreEscuroSecundario, height: 1.4)),
      ]);

  Widget _comErro() => Column(mainAxisSize: MainAxisSize.min, children: [
        const CirculoIcone(Icons.error_outline, tamanho: 88, cor: Cores.escuroSuave, corIcone: Cores.lima),
        const SizedBox(height: 24),
        const Text('Não foi possível fazer o diagnóstico',
            textAlign: TextAlign.center, style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700, color: Colors.white)),
        const SizedBox(height: 10),
        Text(_erro!,
            textAlign: TextAlign.center, style: const TextStyle(fontSize: 15.5, color: Cores.sobreEscuroSecundario, height: 1.45)),
        const SizedBox(height: 32),
        BotaoPrincipal(texto: 'Voltar', aoPremir: () => Navigator.of(context).pop()),
      ]);
}
