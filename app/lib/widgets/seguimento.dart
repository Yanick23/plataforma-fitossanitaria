import 'package:flutter/material.dart';

import '../models/diagnostico.dart';
import '../services/acompanhamento.dart';
import '../services/catalogo.dart';
import '../services/sincronizacao.dart';
import '../tema.dart';
import 'botoes.dart';

/// Abre as duas perguntas do seguimento. Devolve true se o agricultor respondeu.
Future<bool> perguntarSeguimento(BuildContext context, Diagnostico d) async {
  final respondeu = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    builder: (_) => _PerguntasSeguimento(diagnostico: d),
  );
  if (respondeu == true) Sincronizacao.instancia.sincronizar(); // envia já, se houver rede
  return respondeu == true;
}

/// Cartão no ecrã inicial: «Como está a sua planta?» para o diagnóstico mais antigo por responder.
class CartaoSeguimento extends StatelessWidget {
  const CartaoSeguimento({super.key, required this.diagnostico});

  final Diagnostico diagnostico;

  @override
  Widget build(BuildContext context) {
    final pat = Catalogo.instancia.patologia(diagnostico.cultura, diagnostico.classeFinal);
    final dias = DateTime.now().difference(diagnostico.data).inDays;
    return Material(
      color: Cores.cartao,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => perguntarSeguimento(context, diagnostico),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: const Border(left: BorderSide(color: Cores.verdeEscuro, width: 4)),
          ),
          child: Row(children: [
            const Icon(Icons.eco_outlined, color: Cores.verdeEscuro),
            const SizedBox(width: 12),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('Como está a sua planta?', style: TextStyle(fontWeight: FontWeight.w800)),
                const SizedBox(height: 2),
                Text('Há $dias dias a app encontrou ${pat.nomeLocal} no ${diagnostico.cultura.nome.toLowerCase()}. '
                    'Conte-nos se o tratamento resultou.',
                    style: const TextStyle(fontSize: 13, color: Cores.textoSecundario, height: 1.3)),
              ]),
            ),
            IconButton(
              tooltip: 'Agora não',
              icon: const Icon(Icons.close, size: 18, color: Cores.textoSecundario),
              onPressed: () => Acompanhamento.instancia.adiar(diagnostico),
            ),
          ]),
        ),
      ),
    );
  }
}

class _PerguntasSeguimento extends StatefulWidget {
  const _PerguntasSeguimento({required this.diagnostico});

  final Diagnostico diagnostico;

  @override
  State<_PerguntasSeguimento> createState() => _PerguntasSeguimentoState();
}

class _PerguntasSeguimentoState extends State<_PerguntasSeguimento> {
  Seguiu? _seguiu;
  ResultadoTratamento? _resultado;
  bool _aGuardar = false;

  Future<void> _guardar() async {
    setState(() => _aGuardar = true);
    await Acompanhamento.instancia.responder(widget.diagnostico, _seguiu!, _resultado!);
    if (mounted) Navigator.of(context).pop(true);
  }

  Widget _opcoes<T>(List<T> valores, T? escolhido, String Function(T) rotulo, ValueChanged<T> aoEscolher) => Wrap(
        spacing: 8,
        runSpacing: 8,
        children: [
          for (final v in valores)
            ChoiceChip(
              label: Text(rotulo(v)),
              selected: v == escolhido,
              onSelected: (_) => aoEscolher(v),
              selectedColor: Cores.verdeClaro,
              labelStyle: TextStyle(fontWeight: v == escolhido ? FontWeight.w700 : FontWeight.w500),
            ),
        ],
      );

  @override
  Widget build(BuildContext context) {
    final d = widget.diagnostico;
    final pat = Catalogo.instancia.patologia(d.cultura, d.classeFinal);
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.fromLTRB(24, 20, 24, 20 + MediaQuery.viewInsetsOf(context).bottom),
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(pat.nomeLocal, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
          Text('${d.cultura.nome} · diagnóstico de ${d.data.day}/${d.data.month}/${d.data.year}',
              style: const TextStyle(color: Cores.textoSecundario)),
          const SizedBox(height: 18),
          const Text('Seguiu a recomendação?', style: TextStyle(fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          _opcoes(Seguiu.values, _seguiu, (s) => s.rotulo, (s) => setState(() => _seguiu = s)),
          const SizedBox(height: 18),
          const Text('Como está a planta agora?', style: TextStyle(fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          _opcoes(ResultadoTratamento.values, _resultado, (r) => r.rotulo, (r) => setState(() => _resultado = r)),
          const SizedBox(height: 22),
          BotaoPrincipal(
            texto: _aGuardar ? 'A guardar...' : 'Enviar Resposta',
            aoPremir: _seguiu != null && _resultado != null && !_aGuardar ? _guardar : null,
          ),
          const SizedBox(height: 6),
          const Text('A resposta ajuda os técnicos a saber que recomendações funcionam na sua zona.',
              textAlign: TextAlign.center, style: TextStyle(fontSize: 12, color: Cores.textoSecundario)),
        ]),
      ),
    );
  }
}
