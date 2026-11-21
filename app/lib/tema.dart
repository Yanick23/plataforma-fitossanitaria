import 'package:flutter/material.dart';

/// Cores da app. Cabeçalhos verde-escuros com um brilho suave, folhas brancas por cima, e um
/// verde-lima só para a acção principal (botões, botão da câmara, progresso).
abstract final class Cores {
  // Cabeçalho escuro e o seu brilho (canto superior esquerdo).
  static const escuro = Color(0xFF042F2B);
  static const escuroBrilho = Color(0xFF22503F);
  static const escuroSuave = Color(0xFF15433B); // botões redondos sobre o escuro

  // Acção principal
  static const lima = Color(0xFFA3E86C);
  static const limaForte = Color(0xFF7DD44A);
  static const limaSuave = Color(0xFFEEF9E4);
  static const sobreLima = Color(0xFF0E1F14); // texto em cima do lima

  // Marca (texto de destaque, ícones em círculo escuro)
  static const marca = Color(0xFF0B4A3F);
  static const marcaForte = Color(0xFF042F2B);
  static const marcaSuave = Color(0xFFEAF6EC);
  static const verdeOk = Color(0xFF1F9D4A); // confirmações (visto verde)

  // Superfícies e contornos
  static const fundo = Color(0xFFFFFFFF);
  static const cartao = Color(0xFFFFFFFF);
  static const superficie2 = Color(0xFFF3F4F3);
  static const linha = Color(0xFFE7E9E8);
  static const linhaForte = Color(0xFFD4D8D6);

  // Texto (contraste ≥ 4,5:1 sobre o branco)
  static const texto = Color(0xFF0F1A18);
  static const textoSecundario = Color(0xFF656D6A);
  static const textoTerciario = Color(0xFF7D8582);
  static const sobreEscuro = Color(0xFFFFFFFF);
  static const sobreEscuroSecundario = Color(0xFFB9C7C2);

  // Estados
  static const aviso = Color(0xFFE08A1E);
  static const avisoFundo = Color(0xFFFFF3E0);
  static const avisoTexto = Color(0xFF8A4B00);
  static const critico = Color(0xFFE5322D);
  static const criticoFundo = Color(0xFFFDECEC);
  static const criticoTexto = Color(0xFFB3261E);
  static const info = Color(0xFF1C5CAB);
  static const infoFundo = Color(0xFFE3EEFB);

  /// Culturas: [fundo, ícone].
  static const milho = [Color(0xFFFFF4D6), Color(0xFF8A5A00)];
  static const mandioca = [Color(0xFFF3E9DC), Color(0xFF6E4A2A)];

  /// Fundo do ecrã da câmara.
  static const captura = Color(0xFF021F1C);

  // Nomes anteriores, mantidos para os ecrãs que ainda os usam.
  static const verde = verdeOk;
  static const verdeEscuro = marca;
  static const verdeClaro = marcaSuave;
  static const laranja = aviso;
  static const laranjaEscuro = avisoTexto;
}

const letra = 'IBMPlexSans';

/// Cartão branco de cantos grandes e contorno fino.
BoxDecoration decoracaoCartao({Color cor = Cores.cartao, Color borda = Cores.linha, double raio = 24}) =>
    BoxDecoration(color: cor, borderRadius: BorderRadius.circular(raio), border: Border.all(color: borda));

/// Fundo dos cabeçalhos e ecrãs escuros: verde-escuro com um brilho no canto superior esquerdo.
const fundoEscuro = BoxDecoration(
  color: Cores.escuro,
  gradient: RadialGradient(
    center: Alignment(-1.0, -1.0),
    radius: 1.4,
    colors: [Cores.escuroBrilho, Cores.escuro],
    stops: [0.0, 0.75],
  ),
);

ThemeData criarTema() {
  final esquema = ColorScheme.fromSeed(seedColor: Cores.escuro).copyWith(
    primary: Cores.escuro,
    onPrimary: Colors.white,
    primaryContainer: Cores.limaSuave,
    onPrimaryContainer: Cores.escuro,
    secondary: Cores.lima,
    onSecondary: Cores.sobreLima,
    secondaryContainer: Cores.limaSuave,
    onSecondaryContainer: Cores.escuro,
    surface: Cores.cartao,
    onSurface: Cores.texto,
    onSurfaceVariant: Cores.textoSecundario,
    surfaceContainerLowest: Cores.cartao,
    surfaceContainerLow: Cores.cartao,
    surfaceContainer: Cores.cartao,
    surfaceContainerHigh: Cores.cartao,
    surfaceContainerHighest: Cores.superficie2,
    surfaceTint: Colors.transparent,
    outline: Cores.linhaForte,
    outlineVariant: Cores.linha,
    error: Cores.criticoTexto,
    errorContainer: Cores.criticoFundo,
  );
  final base = ThemeData(useMaterial3: true, colorScheme: esquema, fontFamily: letra, scaffoldBackgroundColor: Cores.fundo);
  final t = base.textTheme;
  final textos = t
      .copyWith(
        headlineLarge: t.headlineLarge?.copyWith(fontSize: 32, fontWeight: FontWeight.w700, height: 1.15, letterSpacing: -0.5),
        headlineMedium: t.headlineMedium?.copyWith(fontSize: 28, fontWeight: FontWeight.w700, height: 1.2, letterSpacing: -0.4),
        headlineSmall: t.headlineSmall?.copyWith(fontSize: 22, fontWeight: FontWeight.w700, height: 1.25),
        titleLarge: t.titleLarge?.copyWith(fontSize: 20, fontWeight: FontWeight.w600, height: 1.3),
        titleMedium: t.titleMedium?.copyWith(fontSize: 16, fontWeight: FontWeight.w600, height: 1.35),
        bodyLarge: t.bodyLarge?.copyWith(fontSize: 16, height: 1.5),
        bodyMedium: t.bodyMedium?.copyWith(fontSize: 15, height: 1.45),
        bodySmall: t.bodySmall?.copyWith(fontSize: 13, height: 1.4, color: Cores.textoSecundario),
        labelLarge: t.labelLarge?.copyWith(fontSize: 15, fontWeight: FontWeight.w600),
      )
      .apply(bodyColor: Cores.texto, displayColor: Cores.texto, fontFamily: letra);

  const pilula = StadiumBorder();
  const textoBotao = TextStyle(fontFamily: letra, fontSize: 16, fontWeight: FontWeight.w700, letterSpacing: 0.6);
  OutlineInputBorder contorno(Color cor, [double largura = 1]) =>
      OutlineInputBorder(borderRadius: BorderRadius.circular(30), borderSide: BorderSide(color: cor, width: largura));

  return base.copyWith(
    textTheme: textos,
    appBarTheme: const AppBarTheme(
      backgroundColor: Cores.fundo,
      foregroundColor: Cores.texto,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(fontFamily: letra, fontSize: 18, fontWeight: FontWeight.w600, color: Cores.texto),
    ),
    // Botão principal: pílula verde-lima com texto escuro.
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: Cores.lima,
        foregroundColor: Cores.sobreLima,
        disabledBackgroundColor: Cores.superficie2,
        disabledForegroundColor: Cores.textoTerciario,
        minimumSize: const Size(0, 56),
        padding: const EdgeInsets.symmetric(horizontal: 24),
        shape: pilula,
        textStyle: textoBotao,
        elevation: 0,
      ),
    ),
    // Secundário: pílula branca com contorno verde-lima.
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: Cores.texto,
        backgroundColor: Cores.cartao,
        minimumSize: const Size(0, 56),
        padding: const EdgeInsets.symmetric(horizontal: 24),
        side: const BorderSide(color: Cores.lima, width: 1.5),
        shape: pilula,
        textStyle: textoBotao,
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: Cores.marca,
        minimumSize: const Size(0, 44),
        textStyle: const TextStyle(
            fontFamily: letra, fontSize: 15, fontWeight: FontWeight.w600, decoration: TextDecoration.underline),
      ),
    ),
    iconButtonTheme: IconButtonThemeData(
      style: IconButton.styleFrom(foregroundColor: Cores.texto, minimumSize: const Size(44, 44)),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Cores.cartao,
      contentPadding: const EdgeInsets.symmetric(horizontal: 22, vertical: 18),
      border: contorno(Cores.linhaForte),
      enabledBorder: contorno(Cores.linhaForte),
      disabledBorder: contorno(Cores.linha),
      focusedBorder: contorno(Cores.escuro, 1.5),
      errorBorder: contorno(Cores.criticoTexto),
      focusedErrorBorder: contorno(Cores.criticoTexto, 1.5),
      labelStyle: const TextStyle(color: Cores.textoSecundario),
      floatingLabelStyle: const TextStyle(color: Cores.escuro, fontWeight: FontWeight.w500),
      hintStyle: const TextStyle(color: Cores.textoTerciario),
      helperStyle: const TextStyle(color: Cores.textoSecundario, fontSize: 12.5, height: 1.35),
      errorStyle: const TextStyle(color: Cores.criticoTexto, fontSize: 12.5),
      prefixIconColor: Cores.texto,
    ),
    cardTheme: CardThemeData(
      color: Cores.cartao,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24), side: const BorderSide(color: Cores.linha)),
    ),
    dividerTheme: const DividerThemeData(color: Cores.linha, thickness: 1, space: 1),
    snackBarTheme: SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      backgroundColor: Cores.escuro,
      contentTextStyle: const TextStyle(fontFamily: letra, fontSize: 14, color: Colors.white, height: 1.35),
      actionTextColor: Cores.lima,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
    progressIndicatorTheme: const ProgressIndicatorThemeData(
      color: Cores.limaForte,
      linearTrackColor: Cores.linha,
      circularTrackColor: Colors.transparent,
    ),
    bottomSheetTheme: const BottomSheetThemeData(
      backgroundColor: Cores.cartao,
      surfaceTintColor: Colors.transparent,
      showDragHandle: true,
      dragHandleColor: Cores.linhaForte,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(32))),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: Cores.cartao,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(32)),
      titleTextStyle: const TextStyle(fontFamily: letra, fontSize: 22, fontWeight: FontWeight.w700, color: Cores.texto),
    ),
    listTileTheme: const ListTileThemeData(
      iconColor: Cores.texto,
      titleTextStyle: TextStyle(fontFamily: letra, fontSize: 16, fontWeight: FontWeight.w500, color: Cores.texto),
      subtitleTextStyle: TextStyle(fontFamily: letra, fontSize: 13.5, color: Cores.textoSecundario, height: 1.35),
      contentPadding: EdgeInsets.symmetric(horizontal: 20),
      minVerticalPadding: 12,
    ),
    badgeTheme: const BadgeThemeData(backgroundColor: Cores.critico, textColor: Colors.white),
    checkboxTheme: CheckboxThemeData(
      fillColor: WidgetStateProperty.resolveWith((s) => s.contains(WidgetState.selected) ? Cores.escuro : null),
      side: const BorderSide(color: Cores.escuro, width: 1.5),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
    ),
    radioTheme: RadioThemeData(
      fillColor: WidgetStateProperty.resolveWith((s) => s.contains(WidgetState.selected) ? Cores.limaForte : Cores.texto),
    ),
    segmentedButtonTheme: SegmentedButtonThemeData(
      style: SegmentedButton.styleFrom(
        selectedBackgroundColor: Cores.limaSuave,
        selectedForegroundColor: Cores.escuro,
        side: const BorderSide(color: Cores.linhaForte),
        textStyle: const TextStyle(fontFamily: letra, fontWeight: FontWeight.w500),
      ),
    ),
  );
}
