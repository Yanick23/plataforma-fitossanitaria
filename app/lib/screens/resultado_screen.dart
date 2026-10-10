import 'dart:io';

import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';

import '../main.dart';
import '../models/diagnostico.dart';
import '../models/patologia.dart';
import '../models/resultado_classificacao.dart';
import '../services/catalogo.dart';
import '../services/historial_db.dart';
import '../services/sessao.dart';
import '../services/sincronizacao.dart';
import '../tema.dart';
import '../widgets/anel_confianca.dart';
import '../widgets/botoes.dart';

/// Ecrãs 5 e 6 — Resultado do diagnóstico.
/// Mostra a classe, a confiança, o nome local e científico (RF06) e a
/// recomendação (RF07). Com confiança < 60% mostra o aviso e sugere nova foto (RF05).
class ResultadoScreen extends StatefulWidget {
  const ResultadoScreen({super.key, required this.resultado});

  final ResultadoClassificacao resultado;

  @override
  State<ResultadoScreen> createState() => _ResultadoScreenState();
}

class _ResultadoScreenState extends State<ResultadoScreen> {
  bool _aGuardar = false;

  ResultadoClassificacao get _r => widget.resultado;

  Future<void> _guardar() async {
    setState(() => _aGuardar = true);
    try {
      final utilizador = Sessao.instancia.utilizador.value!;
      // UUID gerado no telemóvel: identifica o diagnóstico de forma única,
      // mesmo que seja enviado várias vezes à API (RNF07).
      final id = const Uuid().v4();
      final caminho = await HistorialDb.instancia.guardarImagem(_r.caminhoImagem, id);
      await HistorialDb.instancia.inserir(Diagnostico(
        id: id,
        utilizadorId: utilizador.id,
        data: DateTime.now(),
        cultura: _r.cultura,
        classePrevista: _r.classe,
        confianca: _r.confianca,
        imagem: Imagem(caminhoFicheiro: caminho, dataCaptura: _r.dataCaptura),
        versaoModelo: _r.versaoModelo,
        tempoInferenciaMs: _r.medicao.inferenciaMs,
        tempoTotalMs: _r.medicao.tempoTotalMs,
      ));
      Sincronizacao.instancia.sincronizar(); // envia já, se houver rede (RF09)
      if (!mounted) return;
      NavegacaoPrincipal.versaoHistorial.value++;
      NavegacaoPrincipal.abaActual.value = 1;
      final mensageiro = ScaffoldMessenger.of(context);
      Navigator.of(context).popUntil((rota) => rota.isFirst);
      mensageiro.showSnackBar(const SnackBar(content: Text('Diagnóstico guardado no historial')));
    } catch (e) {
      if (!mounted) return;
      setState(() => _aGuardar = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Não foi possível guardar: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final entrada = Catalogo.instancia.patologia(_r.cultura, _r.classe);
    final baixa = _r.confiancaBaixa;

    return Scaffold(
      body: SafeArea(
        child: ListView(padding: const EdgeInsets.fromLTRB(20, 12, 20, 24), children: [
          Row(children: [
            const BotaoVoltar(),
            const SizedBox(width: 12),
            const Text('Resultado do Diagnóstico',
                style: TextStyle(color: Cores.textoSecundario, fontWeight: FontWeight.w600)),
          ]),
          const SizedBox(height: 16),
          if (baixa) ...[_avisoBaixaConfianca(), const SizedBox(height: 14)],
          ClipRRect(
            borderRadius: BorderRadius.circular(18),
            child: AspectRatio(
              aspectRatio: 16 / 10,
              child: Image.file(File(_r.caminhoImagem), fit: BoxFit.cover),
            ),
          ),
          const SizedBox(height: 16),
          Row(children: [
            _etiqueta(_r.cultura.nome),
            const SizedBox(width: 8),
            Text(entrada.rotuloTipo, style: const TextStyle(color: Cores.textoSecundario, fontSize: 12)),
          ]),
          const SizedBox(height: 6),
          Text(
            baixa ? 'Possível: ${entrada.nomeLocal}' : entrada.nomeLocal,
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w800,
              color: baixa ? Cores.textoSecundario : Cores.texto,
            ),
          ),
          Text(entrada.nomeCientifico,
              style: const TextStyle(fontStyle: FontStyle.italic, color: Cores.textoSecundario)),
          const SizedBox(height: 18),
          Center(child: AnelConfianca(confianca: _r.confianca, baixa: baixa)),
          const SizedBox(height: 18),
          if (!baixa) ...[_cartaoRecomendacao(entrada), const SizedBox(height: 18)],
          if (baixa) ...[
            BotaoPrincipal(
              texto: 'Tirar Nova Foto',
              icone: Icons.photo_camera,
              cores: const [Cores.laranja, Cores.laranjaEscuro],
              aoPremir: _aGuardar ? null : () => Navigator.of(context).pop(),
            ),
            const SizedBox(height: 12),
            BotaoSecundario(texto: 'Guardar Mesmo Assim', aoPremir: _aGuardar ? null : _guardar),
          ] else
            BotaoPrincipal(texto: 'Guardar no Historial', aoPremir: _aGuardar ? null : _guardar),
          const SizedBox(height: 14),
          Text(
            'Resultado em ${_r.medicao.tempoTotalMs} ms (inferência ${_r.medicao.inferenciaMs} ms, modelo v${_r.versaoModelo}, no telemóvel)',
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 11, color: Cores.textoSecundario),
          ),
        ]),
      ),
    );
  }

  Widget _etiqueta(String texto) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(color: Cores.verdeClaro, borderRadius: BorderRadius.circular(8)),
        child: Text(texto,
            style: const TextStyle(color: Cores.verdeEscuro, fontWeight: FontWeight.w700, fontSize: 12)),
      );

  Widget _avisoBaixaConfianca() => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: Cores.avisoFundo, borderRadius: BorderRadius.circular(14)),
        child: const Row(children: [
          Icon(Icons.warning_amber_rounded, color: Cores.laranjaEscuro),
          SizedBox(width: 10),
          Expanded(
            child: Text(
              'Não temos certeza — tente tirar outra foto com melhor luz, com a folha a encher o enquadramento.',
              style: TextStyle(color: Cores.avisoTexto, fontWeight: FontWeight.w700, height: 1.3),
            ),
          ),
        ]),
      );

  Widget _cartaoRecomendacao(Patologia entrada) => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(color: Cores.verdeClaro, borderRadius: BorderRadius.circular(16)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Recomendação',
              style: TextStyle(fontWeight: FontWeight.w800, color: Cores.verdeEscuro)),
          const SizedBox(height: 6),
          Text(entrada.recomendacao, style: const TextStyle(height: 1.4)),
          const SizedBox(height: 10),
          Text(Catalogo.instancia.aviso,
              style: const TextStyle(fontSize: 11, color: Cores.textoSecundario, height: 1.3)),
        ]),
      );
}
