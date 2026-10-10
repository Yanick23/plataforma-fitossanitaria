import 'dart:io';

import 'package:flutter/material.dart';

import '../main.dart';
import '../models/diagnostico.dart';
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
          builder: (context, snapshot) {
            final itens = snapshot.data;
            final pendentes = itens?.where((d) => d.estadoSinc == EstadoSinc.pendente).length ?? 0;
            return RefreshIndicator(
              onRefresh: () => _sincronizar(context),
              child: CustomScrollView(physics: const AlwaysScrollableScrollPhysics(), slivers: [
                SliverPadding(
                  padding: const EdgeInsets.fromLTRB(20, 20, 12, 4),
                  sliver: SliverToBoxAdapter(
                    child: Row(children: [
                      const Expanded(
                          child: Text('Historial', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800))),
                      ListenableBuilder(
                        listenable: Sincronizacao.instancia,
                        builder: (context, _) => Sincronizacao.instancia.emCurso
                            ? const Padding(
                                padding: EdgeInsets.all(12),
                                child: SizedBox(
                                    width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2.5)))
                            : IconButton(
                                tooltip: 'Sincronizar agora',
                                icon: const Icon(Icons.sync),
                                onPressed: () => _sincronizar(context),
                              ),
                      ),
                    ]),
                  ),
                ),
                if (pendentes > 0)
                  SliverPadding(
                    padding: const EdgeInsets.fromLTRB(20, 0, 20, 8),
                    sliver: SliverToBoxAdapter(
                      child: Text('$pendentes por sincronizar',
                          style: const TextStyle(color: Cores.laranjaEscuro, fontWeight: FontWeight.w600)),
                    ),
                  ),
                if (snapshot.hasError)
                  SliverFillRemaining(child: Center(child: Text('Erro ao ler o historial: ${snapshot.error}')))
                else if (itens == null)
                  const SliverFillRemaining(child: Center(child: CircularProgressIndicator()))
                else if (itens.isEmpty)
                  const SliverFillRemaining(child: _HistorialVazio())
                else
                  SliverPadding(
                    padding: const EdgeInsets.fromLTRB(16, 4, 16, 20),
                    sliver: SliverList.separated(
                      itemCount: itens.length,
                      separatorBuilder: (_, _) => const SizedBox(height: 10),
                      itemBuilder: (_, i) => _ItemHistorial(itens[i]),
                    ),
                  ),
              ]),
            );
          },
        ),
      ),
    );
  }
}

class _ItemHistorial extends StatelessWidget {
  const _ItemHistorial(this.d);

  final Diagnostico d;

  @override
  Widget build(BuildContext context) {
    final pat = Catalogo.instancia.patologia(d.cultura, d.classePrevista);
    final pendente = d.estadoSinc == EstadoSinc.pendente;
    return Material(
      color: Cores.cartao,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => Navigator.of(context)
            .push(MaterialPageRoute(builder: (_) => DetalheDiagnosticoScreen(diagnostico: d))),
        child: Padding(
          padding: const EdgeInsets.all(10),
          child: Row(children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.file(
                File(d.imagem.caminhoFicheiro),
                width: 52,
                height: 52,
                fit: BoxFit.cover,
                cacheWidth: 156,
                errorBuilder: (_, _, _) => Container(
                    width: 52, height: 52, color: Cores.verdeClaro, child: const Icon(Icons.image_not_supported)),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(pat.nomeLocal, style: const TextStyle(fontWeight: FontWeight.w800)),
                const SizedBox(height: 2),
                Text('${d.cultura.nome} · ${formatarDataHora(d.data)} · ${(d.confianca * 100).round()}%',
                    style: const TextStyle(fontSize: 12, color: Cores.textoSecundario)),
              ]),
            ),
            Tooltip(
              message: pendente ? 'Pendente' : 'Sincronizado',
              child: Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  color: pendente ? Cores.avisoFundo : Cores.verdeClaro,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  pendente ? Icons.cloud_upload_outlined : Icons.cloud_done_outlined,
                  size: 18,
                  color: pendente ? Cores.laranjaEscuro : Cores.verdeEscuro,
                ),
              ),
            ),
          ]),
        ),
      ),
    );
  }
}

class _HistorialVazio extends StatelessWidget {
  const _HistorialVazio();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.all(32),
      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        Icon(Icons.history, size: 48, color: Cores.textoSecundario),
        SizedBox(height: 12),
        Text('Ainda não há diagnósticos guardados.',
            textAlign: TextAlign.center, style: TextStyle(color: Cores.textoSecundario)),
      ]),
    );
  }
}
