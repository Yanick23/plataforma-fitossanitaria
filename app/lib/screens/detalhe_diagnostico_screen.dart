import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../models/diagnostico.dart';
import '../services/api_cliente.dart';
import '../services/catalogo.dart';
import '../services/conectividade.dart';
import '../tema.dart';
import '../widgets/anel_confianca.dart';
import '../widgets/botoes.dart';
import '../widgets/formatacao.dart';
import '../models/resultado_classificacao.dart' show limiarConfianca;

/// Detalhe de um diagnóstico do historial, com o Grad-CAM gerado na API
/// ("Ver onde o modelo olhou", secção 4.6.6).
class DetalheDiagnosticoScreen extends StatefulWidget {
  const DetalheDiagnosticoScreen({super.key, required this.diagnostico});

  final Diagnostico diagnostico;

  @override
  State<DetalheDiagnosticoScreen> createState() => _DetalheDiagnosticoScreenState();
}

class _DetalheDiagnosticoScreenState extends State<DetalheDiagnosticoScreen> {
  bool _online = false;
  bool _aCarregar = false;
  Uint8List? _gradcam;
  String? _erro;

  Diagnostico get _d => widget.diagnostico;

  @override
  void initState() {
    super.initState();
    Conectividade.instancia.online().then((v) {
      if (mounted) setState(() => _online = v);
    });
  }

  Future<void> _verGradcam() async {
    setState(() {
      _aCarregar = true;
      _erro = null;
    });
    try {
      final png = await ApiCliente.instancia.gradcam(_d.id);
      if (mounted) setState(() => _gradcam = png);
    } on ErroApi catch (e) {
      if (mounted) setState(() => _erro = e.mensagem);
    } finally {
      if (mounted) setState(() => _aCarregar = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final pat = Catalogo.instancia.patologia(_d.cultura, _d.classePrevista);
    final sincronizado = _d.estadoSinc == EstadoSinc.sincronizado;
    final podeGradcam = sincronizado && _online;

    return Scaffold(
      body: SafeArea(
        child: ListView(padding: const EdgeInsets.fromLTRB(20, 12, 20, 24), children: [
          Row(children: [
            const BotaoVoltar(),
            const SizedBox(width: 12),
            Text(formatarDataHora(_d.data), style: const TextStyle(color: Cores.textoSecundario)),
          ]),
          const SizedBox(height: 16),
          ClipRRect(
            borderRadius: BorderRadius.circular(18),
            child: AspectRatio(
              aspectRatio: 16 / 10,
              child: _gradcam != null
                  ? Image.memory(_gradcam!, fit: BoxFit.cover)
                  : Image.file(File(_d.imagem.caminhoFicheiro), fit: BoxFit.cover,
                      errorBuilder: (_, _, _) => Container(color: Cores.verdeClaro)),
            ),
          ),
          if (_gradcam != null)
            const Padding(
              padding: EdgeInsets.only(top: 6),
              child: Text('Zonas a vermelho: as que mais pesaram na decisão do modelo (Grad-CAM).',
                  style: TextStyle(fontSize: 12, color: Cores.textoSecundario)),
            ),
          const SizedBox(height: 16),
          Text(pat.nomeLocal, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800)),
          Text(pat.nomeCientifico, style: const TextStyle(fontStyle: FontStyle.italic, color: Cores.textoSecundario)),
          const SizedBox(height: 16),
          Center(child: AnelConfianca(confianca: _d.confianca, baixa: _d.confianca < limiarConfianca)),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(color: Cores.verdeClaro, borderRadius: BorderRadius.circular(16)),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Recomendação', style: TextStyle(fontWeight: FontWeight.w800, color: Cores.verdeEscuro)),
              const SizedBox(height: 6),
              Text(pat.recomendacao, style: const TextStyle(height: 1.4)),
            ]),
          ),
          const SizedBox(height: 18),
          if (_gradcam == null)
            BotaoPrincipal(
              texto: _aCarregar ? 'A gerar...' : 'Ver onde o modelo olhou',
              icone: Icons.visibility_outlined,
              aoPremir: podeGradcam && !_aCarregar ? _verGradcam : null,
            ),
          if (!podeGradcam && _gradcam == null)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(
                !sincronizado
                    ? 'Disponível depois de o diagnóstico ser sincronizado com o servidor.'
                    : 'Precisa de ligação à rede.',
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 12, color: Cores.textoSecundario),
              ),
            ),
          if (_erro != null)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(_erro!, textAlign: TextAlign.center, style: const TextStyle(color: Cores.laranjaEscuro)),
            ),
          const SizedBox(height: 14),
          Text(
            '${_d.cultura.nome} · modelo v${_d.versaoModelo} · inferência ${_d.tempoInferenciaMs} ms · '
            '${sincronizado ? 'sincronizado' : 'pendente'}',
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 11, color: Cores.textoSecundario),
          ),
        ]),
      ),
    );
  }
}
