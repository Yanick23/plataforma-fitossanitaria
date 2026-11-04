import 'package:flutter/material.dart';

import '../models/cultura.dart';
import '../models/resultado_classificacao.dart';
import '../services/classificador.dart';
import '../tema.dart';
import '../widgets/botoes.dart';
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
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Center(child: _erro == null ? _aProcessar() : _comErro()),
        ),
      ),
    );
  }

  Widget _aProcessar() => const Column(mainAxisSize: MainAxisSize.min, children: [
        SizedBox(
          width: 64,
          height: 64,
          child: CircularProgressIndicator(strokeWidth: 6, strokeCap: StrokeCap.round, color: Cores.verde),
        ),
        SizedBox(height: 26),
        Text('A analisar imagem...', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
        SizedBox(height: 6),
        Text('Isto pode demorar alguns segundos', style: TextStyle(color: Cores.textoSecundario)),
      ]);

  Widget _comErro() => Column(mainAxisSize: MainAxisSize.min, children: [
        const Icon(Icons.error_outline, size: 56, color: Cores.laranjaEscuro),
        const SizedBox(height: 16),
        const Text('Não foi possível fazer o diagnóstico',
            textAlign: TextAlign.center, style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
        const SizedBox(height: 10),
        Text(_erro!, textAlign: TextAlign.center, style: const TextStyle(color: Cores.textoSecundario, height: 1.4)),
        const SizedBox(height: 28),
        BotaoSecundario(texto: 'Voltar', aoPremir: () => Navigator.of(context).pop()),
      ]);
}
