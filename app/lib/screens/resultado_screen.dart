import 'dart:io';

import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';

import '../main.dart';
import '../models/diagnostico.dart';
import '../models/patologia.dart';
import '../models/resultado_classificacao.dart';
import '../services/catalogo.dart';
import '../services/dados_zona.dart';
import '../services/historial_db.dart';
import '../services/sessao.dart';
import '../services/sincronizacao.dart';
import '../tema.dart';
import '../widgets/anel_confianca.dart';
import '../widgets/botoes.dart';
import '../widgets/ecra_escuro.dart';
import '../widgets/informacao_patologia.dart';
import 'captura_screen.dart';

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

  void _juntarFoto() => Navigator.of(context).push(MaterialPageRoute(
        builder: (_) => CapturaScreen(cultura: _r.cultura, anterior: _r),
      ));

  /// Volta à primeira captura e descarta as fotos analisadas.
  void _recomecar() =>
      Navigator.of(context).popUntil((rota) => rota.settings.name == CapturaScreen.rota || rota.isFirst);

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
      await CampanhasLocais.instancia.diagnosticoFeito(_r.cultura.id); // responde à campanha da zona, se houver
      Sincronizacao.instancia.sincronizar(); // envia já, se houver rede (RF09)
      if (!mounted) return;
      NavegacaoPrincipal.versaoHistorial.value++;
      NavegacaoPrincipal.abaActual.value = 1;
      final mensageiro = ScaffoldMessenger.of(context);
      Navigator.of(context).popUntil((rota) => rota.isFirst);
      mensageiro.showSnackBar(SnackBar(
          content: Text(_r.fotos.length > 1
              ? 'Diagnóstico guardado no historial (${_r.fotos.length} fotos combinadas)'
              : 'Diagnóstico guardado no historial')));
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

    final botoes = baixa
        ? Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            if (_r.podeJuntarFoto) ...[
              BotaoPrincipal(
                texto: 'Tirar outra fotografia',
                icone: Icons.add_a_photo_outlined,
                aoPremir: _aGuardar ? null : _juntarFoto,
              ),
              const SizedBox(height: 10),
            ],
            Row(children: [
              Expanded(child: BotaoSecundario(texto: 'Guardar', aoPremir: _aGuardar ? null : _guardar)),
              const SizedBox(width: 12),
              Expanded(child: BotaoSecundario(texto: 'Recomeçar', aoPremir: _aGuardar ? null : _recomecar)),
            ]),
          ])
        : BotaoPrincipal(texto: 'Guardar no historial', aoPremir: _aGuardar ? null : _guardar);

    return EcraEscuro(
      sobretitulo: '${_r.cultura.nome} · ${entrada.rotuloTipo.toLowerCase()}',
      titulo: baixa ? 'Talvez ${entrada.nomeLocal.toLowerCase()}' : entrada.nomeLocal,
      subtitulo: entrada.nomeCientifico,
      rodape: botoes,
      filhos: [
        if (baixa) ...[
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(color: Cores.avisoFundo, borderRadius: BorderRadius.circular(20)),
            child: const Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Icon(Icons.info_outline, color: Cores.avisoTexto),
              SizedBox(width: 12),
              Expanded(
                child: Text.rich(
                  TextSpan(children: [
                    TextSpan(text: 'A app não tem certeza. ', style: TextStyle(fontWeight: FontWeight.w600)),
                    TextSpan(text: 'Tire outra fotografia com boa luz, com a folha a encher o ecrã.'),
                  ]),
                  style: TextStyle(fontSize: 15, height: 1.45, color: Cores.avisoTexto),
                ),
              ),
            ]),
          ),
          const SizedBox(height: 16),
        ],
        ClipRRect(
          borderRadius: BorderRadius.circular(24),
          child: AspectRatio(aspectRatio: 4 / 3, child: Image.file(File(_r.caminhoImagem), fit: BoxFit.cover)),
        ),
        if (_r.fotos.length > 1) ...[const SizedBox(height: 12), _fotosCombinadas()],
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.fromLTRB(20, 18, 20, 18),
          decoration: decoracaoCartao(),
          child: MedidorConfianca(confianca: _r.confianca, baixa: baixa),
        ),
        if (!baixa) CartaoRecomendacao(patologia: entrada, aviso: Catalogo.instancia.aviso),
        // Com dúvida, os sintomas e as fotos ajudam a comparar; a recomendação só com confiança.
        if (entrada.tipo != TipoPatologia.saudavel) ComoReconhecer(patologia: entrada),
        if (!baixa) Prevencao(patologia: entrada),
        const SizedBox(height: 16),
        Text(
          'Analisado no telemóvel em ${_r.medicao.tempoTotalMs} ms, modelo v${_r.versaoModelo}.',
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 12.5, color: Cores.textoTerciario),
        ),
      ],
    );
  }

  /// Miniaturas das fotografias combinadas, com a confiança de cada uma na classe final.
  Widget _fotosCombinadas() {
    final k = _r.indicePrevisto;
    return Row(children: [
      for (final f in _r.fotos) ...[
        Column(children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: Container(
              decoration: BoxDecoration(
                border: Border.all(color: f.caminho == _r.caminhoImagem ? Cores.verdeEscuro : Colors.transparent, width: 2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Image.file(File(f.caminho), width: 56, height: 42, fit: BoxFit.cover, cacheWidth: 112),
            ),
          ),
          const SizedBox(height: 2),
          Text('${(f.probabilidades[k] * 100).round()}%', style: const TextStyle(fontSize: 11, color: Cores.textoSecundario)),
        ]),
        const SizedBox(width: 8),
      ],
      Expanded(
        child: Text('Resultado combinado de ${_r.fotos.length} fotos (média das probabilidades).',
            style: const TextStyle(fontSize: 12, color: Cores.textoSecundario, height: 1.3)),
      ),
    ]);
  }
}
