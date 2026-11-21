import 'dart:io';

import 'package:flutter/material.dart';

import '../main.dart';
import '../models/diagnostico.dart';
import '../models/resultado_classificacao.dart' show limiarConfianca;
import '../services/catalogo.dart';
import '../services/historial_db.dart';
import '../services/sessao.dart';
import '../services/sincronizacao.dart';
import '../tema.dart';
import '../widgets/ecra_escuro.dart';
import '../widgets/formatacao.dart';
import 'detalhe_diagnostico_screen.dart';

/// Ecrã 7 — Historial de diagnósticos guardados em SQLite (RF08), com o
/// estado de sincronização de cada registo e sincronização manual (RF09).
class HistorialScreen extends StatelessWidget {
  const HistorialScreen({super.key});

  Future<void> _sincronizar(BuildContext context) async {
    final resumo = await Sincronizacao.instancia.sincronizar();
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(resumo.mensagem)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final utilizador = Sessao.instancia.utilizador.value;
    if (utilizador == null) return const SizedBox.shrink();
    return ValueListenableBuilder<int>(
        valueListenable: NavegacaoPrincipal.versaoHistorial,
        builder: (context, versao, _) => FutureBuilder<List<Diagnostico>>(
          key: ValueKey(versao),
          future: HistorialDb.instancia.listar(utilizador.id),
          builder: (context, snapshot) => ListaHistorial(
            itens: snapshot.data,
            erro: snapshot.error,
            aoSincronizar: () => _sincronizar(context),
          ),
      ),
    );
  }
}

/// A lista do historial (separada da leitura da base de dados, para se poder mostrar com dados de exemplo).
class ListaHistorial extends StatelessWidget {
  const ListaHistorial({super.key, required this.itens, this.erro, this.aoSincronizar});

  final List<Diagnostico>? itens; // nulo = a carregar
  final Object? erro;
  final Future<void> Function()? aoSincronizar;

  @override
  Widget build(BuildContext context) {
    final itens = this.itens;
    final pendentes = itens?.where((d) => d.estadoSinc == EstadoSinc.pendente).length ?? 0;
    final resumo = itens == null || itens.isEmpty
        ? 'Os diagnósticos que guardar aparecem aqui.'
        : pendentes == 0
            ? '${itens.length} ${itens.length == 1 ? 'diagnóstico' : 'diagnósticos'}, todos enviados ao técnico.'
            : '${itens.length} ${itens.length == 1 ? 'diagnóstico' : 'diagnósticos'}; '
                '$pendentes por enviar quando houver rede.';
    return EcraEscuro(
      titulo: 'Historial',
      subtitulo: resumo,
      aoActualizar: aoSincronizar,
      direita: ListenableBuilder(
        listenable: Sincronizacao.instancia,
        builder: (context, _) => Material(
          color: Cores.escuroSuave,
          shape: const CircleBorder(),
          child: Sincronizacao.instancia.emCurso
              ? const Padding(
                  padding: EdgeInsets.all(16),
                  child: SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2, color: Cores.lima)))
              : IconButton(
                  tooltip: 'Enviar e actualizar agora',
                  padding: const EdgeInsets.all(14),
                  icon: const Icon(Icons.sync, color: Colors.white),
                  onPressed: aoSincronizar,
                ),
        ),
      ),
      filhos: [
        if (erro != null)
          Text('Erro ao ler o historial: $erro')
        else if (itens == null)
          const Padding(padding: EdgeInsets.all(40), child: Center(child: CircularProgressIndicator()))
        else if (itens.isEmpty)
          const _HistorialVazio()
        else
          for (final d in itens) LinhaDiagnostico(d),
      ],
    );
  }
}

/// Um diagnóstico numa lista: fotografia redonda, o que a app encontrou, quando e o estado
/// (por enviar, confirmado ou corrigido pelo técnico); à direita, a certeza.
class LinhaDiagnostico extends StatelessWidget {
  const LinhaDiagnostico(this.d, {super.key});

  final Diagnostico d;

  @override
  Widget build(BuildContext context) {
    final pat = Catalogo.instancia.patologia(d.cultura, d.classeFinal);
    final pendente = d.estadoSinc == EstadoSinc.pendente;
    final baixa = d.confianca < limiarConfianca;
    final (estado, corEstado) = switch (d.validacao) {
      Validacao.confirmado => ('Confirmado pelo técnico', Cores.verdeOk),
      Validacao.corrigido => ('Corrigido pelo técnico', Cores.avisoTexto),
      Validacao.pendente => pendente ? ('Ainda não enviado', Cores.avisoTexto) : ('Enviado ao técnico', Cores.textoTerciario),
    };
    return InkWell(
      borderRadius: BorderRadius.circular(16),
      onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => DetalheDiagnosticoScreen(diagnostico: d))),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Row(children: [
          ClipOval(
            child: Image.file(
              File(d.imagem.caminhoFicheiro),
              width: 56,
              height: 56,
              fit: BoxFit.cover,
              cacheWidth: 168,
              errorBuilder: (_, _, _) => Container(width: 56, height: 56, color: Cores.superficie2),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(pat.nomeLocal, maxLines: 2, overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 16.5, fontWeight: FontWeight.w500, height: 1.3)),
              const SizedBox(height: 3),
              Text('${d.cultura.nome} · ${quando(d.data)}', style: const TextStyle(fontSize: 14, color: Cores.textoSecundario)),
              const SizedBox(height: 2),
              Text(estado, style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w500, color: corEstado)),
            ]),
          ),
          const SizedBox(width: 10),
          Text('${(d.confianca * 100).round()}%',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: baixa ? Cores.avisoTexto : Cores.texto)),
        ]),
      ),
    );
  }
}

class _HistorialVazio extends StatelessWidget {
  const _HistorialVazio();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.fromLTRB(16, 40, 16, 40),
      child: Column(children: [
        Text('Ainda não há diagnósticos', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),
        SizedBox(height: 6),
        Text('Quando guardar um diagnóstico, ele fica aqui e segue para o técnico assim que houver rede.',
            textAlign: TextAlign.center, style: TextStyle(fontSize: 14.5, color: Cores.textoSecundario, height: 1.45)),
      ]),
    );
  }
}
