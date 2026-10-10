import 'package:flutter/material.dart';

import '../services/conectividade.dart';
import '../tema.dart';

/// Indicador "Online/Offline" do ecrã inicial.
class EstadoLigacao extends StatefulWidget {
  const EstadoLigacao({super.key});

  @override
  State<EstadoLigacao> createState() => _EstadoLigacaoState();
}

class _EstadoLigacaoState extends State<EstadoLigacao> {
  bool? _online;

  @override
  void initState() {
    super.initState();
    Conectividade.instancia.online().then((v) {
      if (mounted) setState(() => _online = v);
    });
  }

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<bool>(
      stream: Conectividade.instancia.alteracoes,
      builder: (context, snapshot) {
        final online = snapshot.data ?? _online;
        final cor = online == null
            ? Cores.textoSecundario
            : online
                ? Cores.verde
                : Cores.laranjaEscuro;
        final texto = online == null ? '…' : (online ? 'Online' : 'Offline');
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: Cores.cartao,
            borderRadius: BorderRadius.circular(20),
            boxShadow: sombraSuave,
          ),
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            Container(width: 8, height: 8, decoration: BoxDecoration(color: cor, shape: BoxShape.circle)),
            const SizedBox(width: 6),
            Text(texto, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
          ]),
        );
      },
    );
  }
}
