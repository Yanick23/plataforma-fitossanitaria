import 'package:flutter/material.dart';

import '../services/conectividade.dart';
import '../tema.dart';

/// «Com rede» / «Sem rede» no ecrã inicial (só informa: o diagnóstico funciona sempre sem rede).
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
        final cor = online == null ? Cores.textoTerciario : (online ? Cores.marca : Cores.aviso);
        final texto = online == null ? '…' : (online ? 'Com rede' : 'Sem rede');
        return Semantics(
          label: online == null ? null : (online ? 'Com rede' : 'Sem rede: tudo funciona e é enviado depois'),
          excludeSemantics: true,
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            Container(width: 7, height: 7, decoration: BoxDecoration(color: cor, shape: BoxShape.circle)),
            const SizedBox(width: 5),
            Text(texto, style: const TextStyle(fontSize: 13.5, color: Cores.textoSecundario)),
          ]),
        );
      },
    );
  }
}
