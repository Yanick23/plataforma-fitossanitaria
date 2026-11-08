import 'package:flutter/material.dart';

/// Cores da app: as mesmas do painel web (admin/src/estilos/tokens.css), para os dois parecerem
/// um só produto. Superfícies claras com contornos finos em vez de sombras; o verde da marca
/// só para acções e estados positivos.
abstract final class Cores {
  // Marca
  static const marca = Color(0xFF13693B);
  static const marcaForte = Color(0xFF0D4F2C);
  static const marcaSuave = Color(0xFFE5F0E9);

  // Superfícies e contornos
  static const fundo = Color(0xFFF4F4F0);
  static const cartao = Color(0xFFFFFFFF);
  static const superficie2 = Color(0xFFF0EFEA);
  static const linha = Color(0xFFE1E0D9);
  static const linhaForte = Color(0xFFC3C2B7);

  // Texto (contraste ≥ 4,5:1 sobre o branco e sobre o fundo)
  static const texto = Color(0xFF161614);
  static const textoSecundario = Color(0xFF5C5B57);
  static const textoTerciario = Color(0xFF7C7B75);

  // Estados
  static const aviso = Color(0xFFB7791F);
  static const avisoFundo = Color(0xFFFDF1D5);
  static const avisoTexto = Color(0xFF7A5200);
  static const critico = Color(0xFFC53030);
  static const criticoFundo = Color(0xFFFBE6E5);
  static const criticoTexto = Color(0xFFA42626);
  static const info = Color(0xFF1C5CAB);
  static const infoFundo = Color(0xFFE3EEFB);

  /// Culturas: [fundo, ícone].
  static const milho = [Color(0xFFFBF0D2), Color(0xFF8A5A00)];
  static const mandioca = [Color(0xFFF1E7DA), Color(0xFF6E4A2A)];

  /// Fundo do ecrã da câmara.
  static const captura = Color(0xFF1C1F1D);

  // Nomes anteriores, mantidos para os ecrãs que ainda os usam.
  static const verde = marca;
  static const verdeEscuro = marca;
  static const verdeClaro = marcaSuave;
  static const laranja = aviso;
  static const laranjaEscuro = Color(0xFF9C5700);
}

const letra = 'IBMPlexSans';

/// Cartão: branco, contorno fino, cantos discretos.
BoxDecoration decoracaoCartao({Color cor = Cores.cartao, Color borda = Cores.linha, double raio = 12}) =>
    BoxDecoration(color: cor, borderRadius: BorderRadius.circular(raio), border: Border.all(color: borda));

/// Sem sombras: a separação faz-se pelo contorno (ver [decoracaoCartao]).
const sombraSuave = <BoxShadow>[];

ThemeData criarTema() {
  final esquema = ColorScheme.fromSeed(seedColor: Cores.marca).copyWith(
    primary: Cores.marca,
    onPrimary: Colors.white,
    primaryContainer: Cores.marcaSuave,
    onPrimaryContainer: Cores.marcaForte,
    secondary: Cores.marca,
    onSecondary: Colors.white,
    secondaryContainer: Cores.marcaSuave,
    onSecondaryContainer: Cores.marcaForte,
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
  final base = ThemeData(
    useMaterial3: true,
    colorScheme: esquema,
    fontFamily: letra,
    scaffoldBackgroundColor: Cores.fundo,
    visualDensity: VisualDensity.standard,
  );
  final t = base.textTheme;
  final textos = t
      .copyWith(
        headlineMedium: t.headlineMedium?.copyWith(fontSize: 26, fontWeight: FontWeight.w600, height: 1.2, letterSpacing: -0.3),
        headlineSmall: t.headlineSmall?.copyWith(fontSize: 22, fontWeight: FontWeight.w600, height: 1.25, letterSpacing: -0.2),
        titleLarge: t.titleLarge?.copyWith(fontSize: 19, fontWeight: FontWeight.w600, height: 1.3),
        titleMedium: t.titleMedium?.copyWith(fontSize: 16, fontWeight: FontWeight.w600, height: 1.35),
        titleSmall: t.titleSmall?.copyWith(fontSize: 14, fontWeight: FontWeight.w600, height: 1.35),
        bodyLarge: t.bodyLarge?.copyWith(fontSize: 16, height: 1.45),
        bodyMedium: t.bodyMedium?.copyWith(fontSize: 15, height: 1.45),
        bodySmall: t.bodySmall?.copyWith(fontSize: 13, height: 1.4, color: Cores.textoSecundario),
        labelLarge: t.labelLarge?.copyWith(fontSize: 15, fontWeight: FontWeight.w600),
        labelMedium: t.labelMedium?.copyWith(fontSize: 13, fontWeight: FontWeight.w500),
        labelSmall: t.labelSmall?.copyWith(fontSize: 12, fontWeight: FontWeight.w500, letterSpacing: 0.2),
      )
      .apply(bodyColor: Cores.texto, displayColor: Cores.texto, fontFamily: letra);

  final raio10 = RoundedRectangleBorder(borderRadius: BorderRadius.circular(10));
  const textoBotao = TextStyle(fontFamily: letra, fontSize: 16, fontWeight: FontWeight.w600);
  OutlineInputBorder contorno(Color cor, [double largura = 1]) =>
      OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide(color: cor, width: largura));

  return base.copyWith(
    textTheme: textos,
    appBarTheme: const AppBarTheme(
      backgroundColor: Cores.fundo,
      foregroundColor: Cores.texto,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
      titleSpacing: 4,
      titleTextStyle: TextStyle(fontFamily: letra, fontSize: 18, fontWeight: FontWeight.w600, color: Cores.texto),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: Cores.marca,
        foregroundColor: Colors.white,
        disabledBackgroundColor: Cores.superficie2,
        disabledForegroundColor: Cores.textoTerciario,
        minimumSize: const Size(0, 52),
        padding: const EdgeInsets.symmetric(horizontal: 20),
        shape: raio10,
        textStyle: textoBotao,
        elevation: 0,
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: Cores.texto,
        backgroundColor: Cores.cartao,
        minimumSize: const Size(0, 52),
        padding: const EdgeInsets.symmetric(horizontal: 20),
        side: const BorderSide(color: Cores.linhaForte),
        shape: raio10,
        textStyle: textoBotao,
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: Cores.marca,
        minimumSize: const Size(0, 44),
        shape: raio10,
        textStyle: const TextStyle(fontFamily: letra, fontSize: 15, fontWeight: FontWeight.w600),
      ),
    ),
    iconButtonTheme: IconButtonThemeData(
      style: IconButton.styleFrom(foregroundColor: Cores.texto, minimumSize: const Size(44, 44)),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Cores.cartao,
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 16),
      border: contorno(Cores.linhaForte),
      enabledBorder: contorno(Cores.linhaForte),
      disabledBorder: contorno(Cores.linha),
      focusedBorder: contorno(Cores.marca, 2),
      errorBorder: contorno(Cores.criticoTexto),
      focusedErrorBorder: contorno(Cores.criticoTexto, 2),
      labelStyle: const TextStyle(color: Cores.textoSecundario),
      floatingLabelStyle: const TextStyle(color: Cores.marca, fontWeight: FontWeight.w500),
      helperStyle: const TextStyle(color: Cores.textoSecundario, fontSize: 12.5, height: 1.35),
      errorStyle: const TextStyle(color: Cores.criticoTexto, fontSize: 12.5),
      prefixIconColor: Cores.textoSecundario,
    ),
    cardTheme: CardThemeData(
      color: Cores.cartao,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: const BorderSide(color: Cores.linha)),
    ),
    dividerTheme: const DividerThemeData(color: Cores.linha, thickness: 1, space: 1),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: Cores.cartao,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      height: 68,
      indicatorColor: Cores.marcaSuave,
      indicatorShape: const StadiumBorder(),
      labelTextStyle: WidgetStateProperty.resolveWith((s) => TextStyle(
            fontFamily: letra,
            fontSize: 12.5,
            fontWeight: s.contains(WidgetState.selected) ? FontWeight.w600 : FontWeight.w500,
            color: s.contains(WidgetState.selected) ? Cores.marcaForte : Cores.textoSecundario,
          )),
      iconTheme: WidgetStateProperty.resolveWith((s) =>
          IconThemeData(size: 24, color: s.contains(WidgetState.selected) ? Cores.marcaForte : Cores.textoSecundario)),
    ),
    snackBarTheme: SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      backgroundColor: const Color(0xFF242422),
      contentTextStyle: const TextStyle(fontFamily: letra, fontSize: 14, color: Colors.white, height: 1.35),
      actionTextColor: const Color(0xFF9FD8B4),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
    ),
    progressIndicatorTheme: const ProgressIndicatorThemeData(
      color: Cores.marca,
      linearTrackColor: Cores.marcaSuave,
      circularTrackColor: Colors.transparent,
    ),
    bottomSheetTheme: const BottomSheetThemeData(
      backgroundColor: Cores.cartao,
      surfaceTintColor: Colors.transparent,
      showDragHandle: true,
      dragHandleColor: Cores.linhaForte,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: Cores.cartao,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      titleTextStyle: const TextStyle(fontFamily: letra, fontSize: 19, fontWeight: FontWeight.w600, color: Cores.texto),
    ),
    listTileTheme: const ListTileThemeData(
      iconColor: Cores.textoSecundario,
      titleTextStyle: TextStyle(fontFamily: letra, fontSize: 15.5, fontWeight: FontWeight.w500, color: Cores.texto),
      subtitleTextStyle: TextStyle(fontFamily: letra, fontSize: 13, color: Cores.textoSecundario, height: 1.35),
      contentPadding: EdgeInsets.symmetric(horizontal: 16),
      minVerticalPadding: 12,
    ),
    badgeTheme: const BadgeThemeData(backgroundColor: Cores.critico, textColor: Colors.white),
    checkboxTheme: CheckboxThemeData(
      fillColor: WidgetStateProperty.resolveWith((s) => s.contains(WidgetState.selected) ? Cores.marca : null),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
    ),
    radioTheme: RadioThemeData(
      fillColor: WidgetStateProperty.resolveWith((s) => s.contains(WidgetState.selected) ? Cores.marca : Cores.linhaForte),
    ),
    segmentedButtonTheme: SegmentedButtonThemeData(
      style: SegmentedButton.styleFrom(
        selectedBackgroundColor: Cores.marcaSuave,
        selectedForegroundColor: Cores.marcaForte,
        side: const BorderSide(color: Cores.linhaForte),
        textStyle: const TextStyle(fontFamily: letra, fontWeight: FontWeight.w500),
      ),
    ),
  );
}
