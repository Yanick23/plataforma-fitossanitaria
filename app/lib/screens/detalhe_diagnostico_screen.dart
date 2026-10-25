import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../models/diagnostico.dart';
import '../models/visita.dart';
import '../services/api_cliente.dart';
import '../services/catalogo.dart';
import '../services/conectividade.dart';
import '../services/visitas_locais.dart';
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
  bool _aPedir = false;
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

  Future<void> _pedirVisita() async {
    final mensagem = TextEditingController();
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Pedir visita do técnico'),
        content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('O técnico da sua zona recebe o pedido com este diagnóstico e combina a visita consigo.',
              style: TextStyle(color: Cores.textoSecundario)),
          const SizedBox(height: 12),
          TextField(
            controller: mensagem,
            maxLines: 3,
            maxLength: 300,
            decoration: const InputDecoration(
                hintText: 'Ex.: Muitas plantas atacadas desde ontem', border: OutlineInputBorder()),
          ),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.of(context).pop(true), child: const Text('Enviar pedido')),
        ],
      ),
    );
    if (confirmar != true || !mounted) return;
    setState(() => _aPedir = true);
    try {
      await VisitasLocais.instancia.pedir(_d.id, mensagem.text.trim().isEmpty ? null : mensagem.text.trim());
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('Pedido enviado ao técnico da sua zona')));
      }
    } on ErroApi catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.mensagem)));
    } finally {
      if (mounted) setState(() => _aPedir = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final pat = Catalogo.instancia.patologia(_d.cultura, _d.classeFinal);
    final prevista = Catalogo.instancia.patologia(_d.cultura, _d.classePrevista);
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
          if (_d.validacao != Validacao.pendente) ...[
            _CaixaValidacao(diagnostico: _d, nomePrevisto: prevista.nomeLocal),
            const SizedBox(height: 12),
          ],
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
          const SizedBox(height: 12),
          // Pedido de visita técnica: estado do pedido ou botão para pedir.
          ListenableBuilder(
            listenable: VisitasLocais.instancia,
            builder: (context, _) {
              final visita = VisitasLocais.instancia.doDiagnostico(_d.id);
              if (visita != null && visita.activa || visita?.estado == EstadoVisita.resolvida) {
                return _CaixaVisita(visita!);
              }
              return Column(children: [
                BotaoSecundario(
                  texto: _aPedir ? 'A enviar...' : 'Pedir visita do técnico',
                  aoPremir: sincronizado && _online && !_aPedir ? _pedirVisita : null,
                ),
                if (!(sincronizado && _online))
                  Padding(
                    padding: const EdgeInsets.only(top: 6),
                    child: Text(
                      !sincronizado ? 'Primeiro o diagnóstico tem de ser sincronizado.' : 'Precisa de ligação à rede.',
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 12, color: Cores.textoSecundario),
                    ),
                  ),
              ]);
            },
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

/// O que o técnico disse sobre o diagnóstico (validação feita no painel web).
class _CaixaValidacao extends StatelessWidget {
  const _CaixaValidacao({required this.diagnostico, required this.nomePrevisto});

  final Diagnostico diagnostico;
  final String nomePrevisto;

  @override
  Widget build(BuildContext context) {
    final confirmado = diagnostico.validacao == Validacao.confirmado;
    final cor = confirmado ? Cores.verdeEscuro : Cores.avisoTexto;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: confirmado ? Cores.verdeClaro : Cores.avisoFundo,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Icon(confirmado ? Icons.verified_outlined : Icons.edit_note, color: cor, size: 20),
          const SizedBox(width: 8),
          Expanded(
            child: Text(confirmado ? 'Confirmado pelo técnico' : 'Corrigido pelo técnico',
                style: TextStyle(fontWeight: FontWeight.w800, color: cor)),
          ),
        ]),
        if (!confirmado) ...[
          const SizedBox(height: 4),
          Text('A app indicou «$nomePrevisto». A recomendação abaixo já é a da correcção.',
              style: const TextStyle(height: 1.4)),
        ],
        if (diagnostico.notaTecnico != null) ...[
          const SizedBox(height: 6),
          Text('«${diagnostico.notaTecnico}»', style: const TextStyle(fontStyle: FontStyle.italic, height: 1.4)),
        ],
      ]),
    );
  }
}

/// Estado do pedido de visita técnica.
class _CaixaVisita extends StatelessWidget {
  const _CaixaVisita(this.visita);

  final Visita visita;

  @override
  Widget build(BuildContext context) {
    final resolvida = visita.estado == EstadoVisita.resolvida;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: Cores.cartao, borderRadius: BorderRadius.circular(16), boxShadow: sombraSuave),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Icon(resolvida ? Icons.task_alt : Icons.support_agent, color: Cores.verdeEscuro, size: 20),
          const SizedBox(width: 8),
          Text(visita.estado.nome, style: const TextStyle(fontWeight: FontWeight.w800)),
        ]),
        if (visita.dataAgendada != null && !resolvida) ...[
          const SizedBox(height: 6),
          Text('Dia ${formatarDataHora(visita.dataAgendada!)}${visita.tecnicoNome != null ? ' · ${visita.tecnicoNome}' : ''}',
              style: const TextStyle(fontWeight: FontWeight.w600)),
        ],
        if (visita.estado == EstadoVisita.pendente) ...[
          const SizedBox(height: 4),
          const Text('O técnico da sua zona vai combinar a visita consigo.',
              style: TextStyle(color: Cores.textoSecundario)),
        ],
        if (visita.notasTecnico != null) ...[
          const SizedBox(height: 6),
          Text('Notas do técnico: ${visita.notasTecnico}', style: const TextStyle(height: 1.4)),
        ],
      ]),
    );
  }
}
