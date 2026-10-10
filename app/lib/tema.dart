import 'package:flutter/material.dart';

/// Cores do protótipo (Ecrãs 1–7 do relatório, secção 5.4).
abstract final class Cores {
  static const verde = Color(0xFF22C55E);
  static const verdeEscuro = Color(0xFF16A34A);
  static const verdeClaro = Color(0xFFE6F6EC);
  static const laranja = Color(0xFFF5B523);
  static const laranjaEscuro = Color(0xFFD97706);
  static const avisoFundo = Color(0xFFFFEDC2);
  static const avisoTexto = Color(0xFF92400E);
  static const fundo = Color(0xFFF5F5EF);
  static const cartao = Colors.white;
  static const texto = Color(0xFF1B2B22);
  static const textoSecundario = Color(0xFF6B7280);
  static const captura = Color(0xFF26302A);
  static const milho = [Color(0xFFFCD34D), Color(0xFFF59E0B)];
  static const mandioca = [Color(0xFFC4A07A), Color(0xFF8B5E3C)];
}

ThemeData criarTema() {
  final base = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: Cores.verde,
      primary: Cores.verdeEscuro,
      surface: Cores.fundo,
    ),
    scaffoldBackgroundColor: Cores.fundo,
  );
  return base.copyWith(
    appBarTheme: const AppBarTheme(
      backgroundColor: Cores.fundo,
      foregroundColor: Cores.texto,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
    ),
    textTheme: base.textTheme.apply(bodyColor: Cores.texto, displayColor: Cores.texto),
    snackBarTheme: const SnackBarThemeData(behavior: SnackBarBehavior.floating),
  );
}

const sombraSuave = [BoxShadow(color: Color(0x14000000), blurRadius: 16, offset: Offset(0, 4))];
