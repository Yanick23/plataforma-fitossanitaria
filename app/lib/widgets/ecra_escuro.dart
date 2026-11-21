import 'package:flutter/material.dart';

import '../tema.dart';

/// Ecrã com cabeçalho verde-escuro (título grande a branco) e uma folha branca de cantos
/// redondos por cima, onde fica o conteúdo. Em baixo, opcionalmente, os botões da acção.
class EcraEscuro extends StatelessWidget {
  const EcraEscuro({
    super.key,
    this.titulo,
    this.sobretitulo,
    this.subtitulo,
    this.local,
    this.passo,
    this.progresso,
    this.direita,
    this.cabecalho,
    required this.filhos,
    this.rodape,
    this.aoActualizar,
    this.paddingFolha = const EdgeInsets.fromLTRB(20, 28, 20, 24),
  });

  final String? titulo;

  /// Linha pequena por cima do título (ex.: «Milho · praga detectada»).
  final String? sobretitulo;
  final String? subtitulo;

  /// Zona do utilizador, com o ícone de localização.
  final String? local;

  /// Passo de um processo, ex.: (2, 5) mostra «2/5».
  final (int, int)? passo;

  /// Barra de progresso verde-lima no fim do cabeçalho (0..1).
  final double? progresso;

  /// À direita do título (ex.: avatar, botão de sincronizar).
  final Widget? direita;

  /// Cabeçalho próprio (substitui título, local e passo).
  final Widget? cabecalho;

  final List<Widget> filhos;
  final Widget? rodape;
  final Future<void> Function()? aoActualizar;
  final EdgeInsets paddingFolha;

  @override
  Widget build(BuildContext context) {
    final podeVoltar = ModalRoute.of(context)?.canPop ?? false;
    final lista = ListView(padding: paddingFolha, physics: const AlwaysScrollableScrollPhysics(), children: filhos);
    return Scaffold(
      backgroundColor: Cores.escuro,
      body: DecoratedBox(
        decoration: fundoEscuro,
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          SafeArea(
            bottom: false,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 4, 20, 28),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                if (podeVoltar)
                  Transform.translate(
                    offset: const Offset(-12, 0),
                    child: IconButton(
                      tooltip: 'Voltar',
                      onPressed: () => Navigator.of(context).maybePop(),
                      icon: const Icon(Icons.arrow_back, color: Colors.white, size: 26),
                    ),
                  )
                else
                  const SizedBox(height: 16),
                cabecalho ??
                    Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Expanded(
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          if (local != null) ...[
                            Row(children: [
                              const Icon(Icons.place_outlined, size: 18, color: Cores.sobreEscuroSecundario),
                              const SizedBox(width: 6),
                              Flexible(
                                child: Text(local!,
                                    overflow: TextOverflow.ellipsis,
                                    style: const TextStyle(fontSize: 15, color: Cores.sobreEscuroSecundario)),
                              ),
                            ]),
                            const SizedBox(height: 10),
                          ],
                          if (passo != null) ...[
                            Text.rich(TextSpan(children: [
                              TextSpan(text: '${passo!.$1}', style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w700)),
                              TextSpan(text: '/${passo!.$2}', style: const TextStyle(fontSize: 18)),
                            ]), style: const TextStyle(color: Colors.white)),
                            const SizedBox(height: 10),
                          ],
                          if (sobretitulo != null) ...[
                            Text(sobretitulo!, style: const TextStyle(fontSize: 15, color: Cores.sobreEscuroSecundario)),
                            const SizedBox(height: 6),
                          ],
                          if (titulo != null)
                            Text(titulo!,
                                style: const TextStyle(
                                    fontSize: 30, fontWeight: FontWeight.w700, color: Colors.white, height: 1.15, letterSpacing: -0.4)),
                          if (subtitulo != null) ...[
                            const SizedBox(height: 8),
                            Text(subtitulo!,
                                style: const TextStyle(fontSize: 15.5, color: Cores.sobreEscuroSecundario, height: 1.4)),
                          ],
                        ]),
                      ),
                      if (direita != null) ...[const SizedBox(width: 12), direita!],
                    ]),
                if (progresso != null) ...[
                  const SizedBox(height: 20),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(2),
                    child: LinearProgressIndicator(
                      value: progresso,
                      minHeight: 4,
                      color: Cores.lima,
                      backgroundColor: Colors.white.withValues(alpha: 0.12),
                    ),
                  ),
                ],
              ]),
            ),
          ),
          Expanded(
            child: DecoratedBox(
              decoration: const BoxDecoration(
                color: Cores.fundo,
                borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
              ),
              child: ClipRRect(
                borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
                child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                  Expanded(child: aoActualizar == null ? lista : RefreshIndicator(onRefresh: aoActualizar!, child: lista)),
                  if (rodape != null)
                    SafeArea(
                      top: false,
                      child: Padding(padding: const EdgeInsets.fromLTRB(20, 8, 20, 16), child: rodape),
                    ),
                ]),
              ),
            ),
          ),
        ]),
      ),
    );
  }
}

/// Avatar redondo com as iniciais do nome (sem fotografia), com anel escuro.
class AvatarIniciais extends StatelessWidget {
  const AvatarIniciais(this.nome, {super.key, this.tamanho = 56});

  final String nome;
  final double tamanho;

  @override
  Widget build(BuildContext context) {
    final partes = nome.trim().split(RegExp(r'\s+')).where((p) => p.isNotEmpty).toList();
    final iniciais = partes.isEmpty
        ? '?'
        : (partes.first[0] + (partes.length > 1 ? partes.last[0] : '')).toUpperCase();
    return Container(
      width: tamanho + 8,
      height: tamanho + 8,
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(shape: BoxShape.circle, border: Border.all(color: Cores.escuroSuave, width: 1.5)),
      child: Container(
        alignment: Alignment.center,
        decoration: const BoxDecoration(
          shape: BoxShape.circle,
          gradient: LinearGradient(colors: [Cores.lima, Cores.limaForte], begin: Alignment.topLeft, end: Alignment.bottomRight),
        ),
        child: Text(iniciais, style: TextStyle(fontSize: tamanho * 0.36, fontWeight: FontWeight.w700, color: Cores.sobreLima)),
      ),
    );
  }
}

/// Círculo verde-escuro com um ícone branco (atalhos, caixas de confirmação).
class CirculoIcone extends StatelessWidget {
  const CirculoIcone(this.icone, {super.key, this.tamanho = 60, this.cor = Cores.escuro, this.corIcone = Colors.white});

  final IconData icone;
  final double tamanho;
  final Color cor;
  final Color corIcone;

  @override
  Widget build(BuildContext context) => Container(
        width: tamanho,
        height: tamanho,
        decoration: BoxDecoration(color: cor, shape: BoxShape.circle),
        child: Icon(icone, color: corIcone, size: tamanho * 0.42),
      );
}
