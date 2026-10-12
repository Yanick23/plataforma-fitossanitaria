import 'package:flutter/material.dart';

import '../tema.dart';

/// Botão principal com gradiente (verde por omissão; laranja no aviso de baixa confiança).
class BotaoPrincipal extends StatelessWidget {
  const BotaoPrincipal({
    super.key,
    required this.texto,
    required this.aoPremir,
    this.icone,
    this.cores = const [Cores.verde, Cores.verdeEscuro],
  });

  final String texto;
  final VoidCallback? aoPremir;
  final IconData? icone;
  final List<Color> cores;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      enabled: aoPremir != null,
      label: texto,
      excludeSemantics: true,
      child: Opacity(
        opacity: aoPremir == null ? 0.5 : 1,
        child: Container(
          height: 56,
          decoration: BoxDecoration(
            gradient: LinearGradient(colors: cores),
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: cores.last.withValues(alpha: 0.35),
                blurRadius: 14,
                offset: const Offset(0, 6),
              ),
            ],
          ),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              borderRadius: BorderRadius.circular(16),
              onTap: aoPremir,
              child: Center(
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (icone != null) ...[
                      Icon(icone, color: Colors.white, size: 22),
                      const SizedBox(width: 10),
                    ],
                    Text(
                      texto,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 17,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Botão branco secundário ("Ver Historial", "Guardar Mesmo Assim").
class BotaoSecundario extends StatelessWidget {
  const BotaoSecundario({
    super.key,
    required this.texto,
    required this.aoPremir,
  });

  final String texto;
  final VoidCallback? aoPremir;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 52,
      width: double.infinity,
      child: TextButton(
        onPressed: aoPremir,
        style: TextButton.styleFrom(
          backgroundColor: Cores.cartao,
          foregroundColor: Cores.texto,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
        ),
        child: Text(texto),
      ),
    );
  }
}

/// Botão "voltar" quadrado e branco, como no protótipo.
class BotaoVoltar extends StatelessWidget {
  const BotaoVoltar({super.key, this.escuro = false});

  final bool escuro;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: escuro ? Colors.black38 : Cores.cartao,
      borderRadius: BorderRadius.circular(10),
      child: InkWell(
        borderRadius: BorderRadius.circular(10),
        onTap: () => Navigator.of(context).maybePop(),
        child: SizedBox(
          width: 36,
          height: 36,
          child: Icon(
            Icons.chevron_left,
            color: escuro ? Colors.white : Cores.texto,
          ),
        ),
      ),
    );
  }
}
