import 'dart:io';

import 'package:flutter/material.dart';

import '../models/patologia.dart';
import '../services/catalogo.dart';
import '../tema.dart';

/// «Como reconhecer»: sintomas e fotografias de referência, para o agricultor comparar com a sua planta.
/// Não mostra nada se a patologia não tiver nem sintomas nem fotos descarregadas.
class ComoReconhecer extends StatelessWidget {
  const ComoReconhecer({super.key, required this.patologia});

  final Patologia patologia;

  @override
  Widget build(BuildContext context) {
    final fotos = [
      for (final f in patologia.fotos)
        if (Catalogo.instancia.ficheiroFoto(f) case final ficheiro?) (f, ficheiro),
    ];
    final sintomas = patologia.sintomas?.trim() ?? '';
    if (sintomas.isEmpty && fotos.isEmpty) return const SizedBox.shrink();

    return _Cartao(
      titulo: 'Como reconhecer',
      icone: Icons.search,
      filhos: [
        if (sintomas.isNotEmpty) Text(sintomas, style: const TextStyle(height: 1.4)),
        if (fotos.isNotEmpty) ...[
          if (sintomas.isNotEmpty) const SizedBox(height: 12),
          const Text('Compare com a sua planta:', style: TextStyle(fontSize: 12, color: Cores.textoSecundario)),
          const SizedBox(height: 6),
          SizedBox(
            height: 96,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: fotos.length,
              separatorBuilder: (_, _) => const SizedBox(width: 8),
              itemBuilder: (context, i) {
                final (foto, ficheiro) = fotos[i];
                return Semantics(
                  button: true,
                  label: foto.legenda ?? 'Fotografia de referência ${i + 1}',
                  child: GestureDetector(
                    onTap: () => _ampliar(context, fotos.map((e) => e.$2).toList(), fotos.map((e) => e.$1.legenda).toList(), i),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(10),
                      child: Image.file(ficheiro, width: 128, height: 96, fit: BoxFit.cover, cacheWidth: 256),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ],
    );
  }

  void _ampliar(BuildContext context, List<File> ficheiros, List<String?> legendas, int inicial) {
    Navigator.of(context).push(MaterialPageRoute(
      fullscreenDialog: true,
      builder: (_) => _GaleriaReferencia(ficheiros: ficheiros, legendas: legendas, inicial: inicial, titulo: patologia.nomeLocal),
    ));
  }
}

/// Prevenção: o que fazer na próxima campanha.
class Prevencao extends StatelessWidget {
  const Prevencao({super.key, required this.patologia});

  final Patologia patologia;

  @override
  Widget build(BuildContext context) {
    final texto = patologia.prevencao?.trim() ?? '';
    if (texto.isEmpty) return const SizedBox.shrink();
    return _Cartao(
      titulo: 'Para não voltar a acontecer',
      icone: Icons.shield_outlined,
      filhos: [Text(texto, style: const TextStyle(height: 1.4))],
    );
  }
}

class _Cartao extends StatelessWidget {
  const _Cartao({required this.titulo, required this.icone, required this.filhos});

  final String titulo;
  final IconData icone;
  final List<Widget> filhos;

  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(color: Cores.cartao, borderRadius: BorderRadius.circular(16), boxShadow: sombraSuave),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Icon(icone, size: 18, color: Cores.textoSecundario),
            const SizedBox(width: 6),
            Text(titulo, style: const TextStyle(fontWeight: FontWeight.w800)),
          ]),
          const SizedBox(height: 8),
          ...filhos,
        ]),
      );
}

class _GaleriaReferencia extends StatelessWidget {
  const _GaleriaReferencia({required this.ficheiros, required this.legendas, required this.inicial, required this.titulo});

  final List<File> ficheiros;
  final List<String?> legendas;
  final int inicial;
  final String titulo;

  @override
  Widget build(BuildContext context) => Scaffold(
        backgroundColor: Colors.black,
        appBar: AppBar(backgroundColor: Colors.black, foregroundColor: Colors.white, title: Text(titulo)),
        body: PageView.builder(
          controller: PageController(initialPage: inicial),
          itemCount: ficheiros.length,
          itemBuilder: (context, i) => Column(children: [
            Expanded(child: InteractiveViewer(child: Center(child: Image.file(ficheiros[i])))),
            if (legendas[i] != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
                child: Text(legendas[i]!, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, height: 1.4)),
              ),
          ]),
        ),
      );
}
