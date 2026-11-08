import 'dart:async';

import 'package:flutter/material.dart';
import 'package:just_audio/just_audio.dart';

import '../models/audio.dart';
import '../services/sessao.dart';
import '../services/vozes_locais.dart';
import '../tema.dart';

/// «Ouvir em Xichangana»: toca, sem rede, a gravação na língua escolhida pelo agricultor
/// (ou em português, se ainda não houver na língua dele). Sem gravação no telemóvel, não aparece.
class BotaoOuvir extends StatefulWidget {
  const BotaoOuvir({super.key, required this.audios});

  final List<AudioVoz> audios;

  @override
  State<BotaoOuvir> createState() => _BotaoOuvirState();
}

class _BotaoOuvirState extends State<BotaoOuvir> {
  AudioPlayer? _leitor;
  StreamSubscription<PlayerState>? _estado;
  bool _aTocar = false;
  String? _erro;

  @override
  void dispose() {
    _estado?.cancel();
    _leitor?.dispose();
    super.dispose();
  }

  Future<void> _alternar(AudioVoz audio) async {
    final leitor = _leitor ??= AudioPlayer();
    if (_aTocar) {
      await leitor.stop();
      return;
    }
    final ficheiro = VozesLocais.instancia.ficheiro(audio);
    if (ficheiro == null) return;
    _estado ??= leitor.playerStateStream.listen((s) {
      final aTocar = s.playing && s.processingState != ProcessingState.completed;
      if (s.processingState == ProcessingState.completed) leitor.stop();
      if (mounted && aTocar != _aTocar) setState(() => _aTocar = aTocar);
    });
    try {
      setState(() => _erro = null);
      await leitor.setFilePath(ficheiro.path);
      unawaited(VozesLocais.instancia.ouvida(audio));
      await leitor.play();
    } catch (_) {
      if (mounted) setState(() => _erro = 'Não foi possível tocar a gravação.');
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: VozesLocais.instancia,
      builder: (context, _) {
        final audio = VozesLocais.instancia.paraOuvir(widget.audios, Sessao.instancia.utilizador.value?.lingua);
        if (audio == null) return const SizedBox.shrink();
        return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Semantics(
            button: true,
            label: _aTocar ? 'Parar a gravação' : 'Ouvir em ${audio.nomeLingua}',
            excludeSemantics: true,
            child: OutlinedButton.icon(
              onPressed: () => _alternar(audio),
              icon: Icon(_aTocar ? Icons.stop_circle_outlined : Icons.volume_up_rounded),
              label: Text(_aTocar ? 'Parar' : 'Ouvir em ${audio.nomeLingua}'),
              style: OutlinedButton.styleFrom(
                foregroundColor: Cores.verdeEscuro,
                side: const BorderSide(color: Cores.verdeEscuro),
                minimumSize: const Size(0, 48), // alvo de toque grande
                textStyle: const TextStyle(fontWeight: FontWeight.w600),
              ),
            ),
          ),
          if (_erro != null)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(_erro!, style: const TextStyle(fontSize: 12, color: Cores.avisoTexto)),
            ),
        ]);
      },
    );
  }
}
