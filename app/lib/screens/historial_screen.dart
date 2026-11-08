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
    return SafeArea(
      child: ValueListenableBuilder<int>(
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
        ? null
        : '${itens.length == 1 ? '1 diagnóstico' : '${itens.length} diagnósticos'}'
            '${pendentes == 0 ? ' · todos enviados' : ' · $pendentes por enviar'}';
    return RefreshIndicator(
      onRefresh: aoSincronizar ?? () async {},
      child: CustomScrollView(physics: const AlwaysScrollableScrollPhysics(), slivers: [
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(20, 18, 12, 14),
          sliver: SliverToBoxAdapter(
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('Historial', style: Theme.of(context).textTheme.headlineSmall),
                  if (resumo != null) ...[
                    const SizedBox(height: 4),
                    Text(resumo,
                        style: TextStyle(fontSize: 13.5, color: pendentes > 0 ? Cores.avisoTexto : Cores.textoSecundario)),
                  ],
                ]),
              ),
              ListenableBuilder(
                listenable: Sincronizacao.instancia,
                builder: (context, _) => Sincronizacao.instancia.emCurso
                    ? const Padding(
                        padding: EdgeInsets.all(12),
                        child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2.2)))
                    : IconButton(tooltip: 'Enviar e actualizar agora', icon: const Icon(Icons.sync), onPressed: aoSincronizar),
              ),
            ]),
          ),
        ),
        if (erro != null)
          SliverFillRemaining(child: Center(child: Text('Erro ao ler o historial: $erro')))
        else if (itens == null)
          const SliverFillRemaining(child: Center(child: CircularProgressIndicator()))
        else if (itens.isEmpty)
          const SliverFillRemaining(child: _HistorialVazio())
        else
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
            sliver: SliverToBoxAdapter(
              child: Material(
                color: Cores.cartao,
                clipBehavior: Clip.antiAlias,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12), side: const BorderSide(color: Cores.linha)),
                child: Column(children: [
                  for (final (i, d) in itens.indexed) ...[
                    if (i > 0) const Divider(indent: 80),
                    _ItemHistorial(d),
                  ],
                ]),
              ),
            ),
          ),
      ]),
    );
  }
}

class _ItemHistorial extends StatelessWidget {
  const _ItemHistorial(this.d);

  final Diagnostico d;

  @override
  Widget build(BuildContext context) {
    final pat = Catalogo.instancia.patologia(d.cultura, d.classeFinal);
    final pendente = d.estadoSinc == EstadoSinc.pendente;
    final baixa = d.confianca < limiarConfianca;
    return InkWell(
      onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => DetalheDiagnosticoScreen(diagnostico: d))),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: Image.file(
              File(d.imagem.caminhoFicheiro),
              width: 52,
              height: 52,
              fit: BoxFit.cover,
              cacheWidth: 156,
              errorBuilder: (_, _, _) => Container(
                  width: 52, height: 52, color: Cores.superficie2,
                  child: const Icon(Icons.image_not_supported_outlined, color: Cores.textoTerciario)),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(pat.nomeLocal, style: const TextStyle(fontSize: 15.5, fontWeight: FontWeight.w600, height: 1.3)),
              const SizedBox(height: 2),
              Text('${d.cultura.nome} · ${formatarDataHora(d.data)}',
                  style: const TextStyle(fontSize: 13, color: Cores.textoSecundario)),
              const SizedBox(height: 6),
              Wrap(spacing: 12, runSpacing: 4, children: [
                _Estado(
                  icone: pendente ? Icons.schedule : Icons.cloud_done_outlined,
                  texto: pendente ? 'Por enviar' : 'Enviado',
                  cor: pendente ? Cores.avisoTexto : Cores.textoSecundario,
                ),
                if (d.validacao != Validacao.pendente) _MarcaValidacao(d.validacao),
              ]),
            ]),
          ),
          const SizedBox(width: 8),
          Text('${(d.confianca * 100).round()}%',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: baixa ? Cores.avisoTexto : Cores.texto)),
        ]),
      ),
    );
  }
}

class _Estado extends StatelessWidget {
  const _Estado({required this.icone, required this.texto, required this.cor});

  final IconData icone;
  final String texto;
  final Color cor;

  @override
  Widget build(BuildContext context) => Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icone, size: 14, color: cor),
        const SizedBox(width: 4),
        Text(texto, style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.w500, color: cor)),
      ]);
}

/// «Confirmado pelo técnico» (verde) ou «Corrigido pelo técnico» (laranja).
class _MarcaValidacao extends StatelessWidget {
  const _MarcaValidacao(this.v);

  final Validacao v;

  @override
  Widget build(BuildContext context) {
    final confirmado = v == Validacao.confirmado;
    final cor = confirmado ? Cores.marca : Cores.avisoTexto;
    return Row(mainAxisSize: MainAxisSize.min, children: [
      Icon(confirmado ? Icons.verified_outlined : Icons.edit_note, size: 14, color: cor),
      const SizedBox(width: 4),
      Text(confirmado ? 'Confirmado pelo técnico' : 'Corrigido pelo técnico',
          style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.w500, color: cor)),
    ]);
  }
}

class _HistorialVazio extends StatelessWidget {
  const _HistorialVazio();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.fromLTRB(40, 0, 40, 80),
      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        Icon(Icons.photo_library_outlined, size: 36, color: Cores.textoTerciario),
        SizedBox(height: 14),
        Text('Ainda sem diagnósticos', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),
        SizedBox(height: 6),
        Text('Os diagnósticos que guardar aparecem aqui e são enviados ao técnico quando houver rede.',
            textAlign: TextAlign.center, style: TextStyle(fontSize: 14.5, color: Cores.textoSecundario, height: 1.45)),
      ]),
    );
  }
}
