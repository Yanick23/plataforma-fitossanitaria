import 'package:flutter/material.dart';

import '../models/calendario.dart';
import '../models/cultura.dart';
import '../services/dados_zona.dart';
import '../tema.dart';
import '../widgets/ecra_escuro.dart';

/// Calendário agrícola da província (funcionalidade 10), como uma linha do tempo dos próximos
/// 12 meses, a começar no mês actual, com as fontes. Funciona sem rede.
class CalendarioScreen extends StatelessWidget {
  const CalendarioScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final c = CalendarioLocal.instancia.calendario;
    final actual = DateTime.now().month;
    if (c == null) {
      return const EcraEscuro(titulo: 'Calendário agrícola', filhos: [
        Padding(
          padding: EdgeInsets.all(24),
          child: Text('O calendário chega na próxima sincronização.',
              textAlign: TextAlign.center, style: TextStyle(fontSize: 15, color: Cores.textoSecundario)),
        ),
      ]);
    }
    final meses = [for (var i = 0; i < 12; i++) c.mes((actual - 1 + i) % 12 + 1)];
    return EcraEscuro(
      local: 'Província de ${c.provincia}',
      titulo: 'Calendário agrícola',
      subtitulo: c.sementeira == null ? 'Região ${c.regiao}' : 'Região ${c.regiao} · sementeira: ${c.sementeira}',
      filhos: [
        Container(
          padding: const EdgeInsets.fromLTRB(16, 20, 16, 8),
          decoration: decoracaoCartao(),
          child: Column(children: [
            for (final (i, m) in meses.indexed) _Mes(mes: m, actual: i == 0, ultimo: i == meses.length - 1),
          ]),
        ),
        const SizedBox(height: 20),
        Text(c.aviso, style: const TextStyle(fontSize: 13.5, color: Cores.textoSecundario, height: 1.45)),
        const SizedBox(height: 14),
        const Text('Fontes', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
        for (final f in c.fontes.values)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(f, style: const TextStyle(fontSize: 13.5, color: Cores.textoSecundario, height: 1.4)),
          ),
      ],
    );
  }
}

/// Um mês na linha do tempo: o ponto (grande e verde no mês actual), o nome e, em pílulas,
/// os trabalhos e o que vigiar.
class _Mes extends StatelessWidget {
  const _Mes({required this.mes, required this.actual, required this.ultimo});

  final MesCalendario mes;
  final bool actual;
  final bool ultimo;

  @override
  Widget build(BuildContext context) {
    final vazio = mes.actividades.isEmpty && mes.avisos.isEmpty;
    return IntrinsicHeight(
      child: Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        SizedBox(
          width: 44,
          child: Column(children: [
            actual
                ? Container(
                    width: 40,
                    height: 40,
                    decoration: const BoxDecoration(color: Cores.verdeOk, shape: BoxShape.circle),
                    child: const Icon(Icons.today_outlined, color: Colors.white, size: 20),
                  )
                : Container(
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    width: 22,
                    height: 22,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: vazio ? Cores.linhaForte : Cores.lima, width: 4),
                    ),
                  ),
            if (!ultimo)
              Expanded(child: Container(width: 3, color: actual ? Cores.verdeOk : Cores.linha)),
          ]),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Padding(
            padding: EdgeInsets.only(top: actual ? 8 : 4, bottom: 20),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(actual ? '${Calendario.nomesMeses[mes.mes - 1]} · este mês' : Calendario.nomesMeses[mes.mes - 1],
                  style: TextStyle(fontSize: actual ? 18 : 16.5, fontWeight: FontWeight.w600)),
              if (vazio)
                const Padding(
                  padding: EdgeInsets.only(top: 4),
                  child: Text('Nada marcado.', style: TextStyle(fontSize: 14, color: Cores.textoTerciario)),
                ),
              for (final a in mes.actividades) _Pilula(texto: a),
              for (final a in mes.avisos) _Pilula(texto: '${Cultura.nomeDe(a.culturaId)}: ${a.texto}', vigiar: true),
            ]),
          ),
        ),
      ]),
    );
  }
}

class _Pilula extends StatelessWidget {
  const _Pilula({required this.texto, this.vigiar = false});

  final String texto;
  final bool vigiar;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.fromLTRB(14, 10, 12, 10),
      decoration: BoxDecoration(borderRadius: BorderRadius.circular(16), border: Border.all(color: Cores.linha)),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Expanded(child: Text(texto, style: const TextStyle(fontSize: 14.5, height: 1.4))),
        const SizedBox(width: 8),
        Container(
          width: 22,
          height: 22,
          decoration: BoxDecoration(color: vigiar ? Cores.aviso : Cores.verdeOk, shape: BoxShape.circle),
          child: Icon(vigiar ? Icons.visibility_outlined : Icons.eco_outlined, color: Colors.white, size: 14),
        ),
      ]),
    );
  }
}
