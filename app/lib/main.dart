import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'models/utilizador.dart';
import 'screens/alertas_screen.dart';
import 'screens/cultura_screen.dart';
import 'screens/definicoes_screen.dart';
import 'screens/historial_screen.dart';
import 'screens/inicio_screen.dart';
import 'screens/login_screen.dart';
import 'services/acompanhamento.dart';
import 'services/alertas_locais.dart';
import 'services/catalogo.dart';
import 'services/dados_zona.dart';
import 'services/notificacoes_fundo.dart';
import 'services/sessao.dart';
import 'services/sincronizacao.dart';
import 'services/visitas_locais.dart';
import 'services/vozes_locais.dart';
import 'tema.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  await Sessao.instancia.carregar();
  await Catalogo.instancia.carregar();
  await AlertasLocais.instancia.carregar();
  await VisitasLocais.instancia.carregar();
  await CampanhasLocais.instancia.carregar();
  await CalendarioLocal.instancia.carregar();
  await VozesLocais.instancia.carregar();
  await Acompanhamento.instancia.actualizar();
  runApp(const AgroDiagnosticoApp());
}

class AgroDiagnosticoApp extends StatelessWidget {
  const AgroDiagnosticoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Diagnóstico de culturas',
      debugShowCheckedModeBanner: false,
      theme: criarTema(),
      // Sem sessão → login (RF10). Com sessão guardada, entra directamente,
      // mesmo sem rede (RNF01).
      home: ValueListenableBuilder<Utilizador?>(
        valueListenable: Sessao.instancia.utilizador,
        builder: (context, utilizador, _) =>
            utilizador == null ? const LoginScreen() : const NavegacaoPrincipal(),
      ),
    );
  }
}

/// Navegação principal: Início, Historial, Alertas e Definições, com a câmara ao centro.
class NavegacaoPrincipal extends StatefulWidget {
  const NavegacaoPrincipal({super.key});

  /// Permite a outros ecrãs abrir o separador do historial (ex.: depois de guardar).
  static final abaActual = ValueNotifier<int>(0);

  /// Incrementado sempre que o historial muda, para o ecrã se actualizar.
  static final versaoHistorial = ValueNotifier<int>(0);

  @override
  State<NavegacaoPrincipal> createState() => _NavegacaoPrincipalState();
}

class _NavegacaoPrincipalState extends State<NavegacaoPrincipal> {
  @override
  void initState() {
    super.initState();
    NavegacaoPrincipal.abaActual.value = 0;
    // Sincroniza ao entrar e sempre que a rede voltar (RF09).
    Sincronizacao.instancia
      ..iniciarAutomatica()
      ..addListener(_aoSincronizar);
    Sincronizacao.instancia.sincronizar();
    // Notificações em segundo plano (alertas, validações, visitas, campanhas), sem Firebase.
    NotificacoesFundo.iniciar();
  }

  @override
  void dispose() {
    Sincronizacao.instancia.removeListener(_aoSincronizar);
    super.dispose();
  }

  void _aoSincronizar() {
    if (!Sincronizacao.instancia.emCurso) NavegacaoPrincipal.versaoHistorial.value++;
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<int>(
      valueListenable: NavegacaoPrincipal.abaActual,
      builder: (context, aba, _) => Scaffold(
        body: IndexedStack(
          index: aba,
          children: const [InicioScreen(), HistorialScreen(), AlertasScreen(), DefinicoesScreen()],
        ),
        bottomNavigationBar: BarraNavegacao(
          aba: aba,
          aoEscolher: (i) => NavegacaoPrincipal.abaActual.value = i,
          aoFotografar: () => escolherCulturaEFotografar(context),
        ),
      ),
    );
  }
}

/// Barra inferior: quatro separadores e, ao centro, o botão redondo da câmara (a acção principal).
class BarraNavegacao extends StatelessWidget {
  const BarraNavegacao({super.key, required this.aba, required this.aoEscolher, this.aoFotografar});

  final int aba;
  final ValueChanged<int> aoEscolher;
  final VoidCallback? aoFotografar;

  @override
  Widget build(BuildContext context) {
    Widget item(int i, IconData icone, IconData iconeActivo, String nome, {int contador = 0}) {
      final activo = aba == i;
      final cor = activo ? Cores.escuro : Cores.textoTerciario;
      return Expanded(
        child: Semantics(
          selected: activo,
          button: true,
          label: nome,
          excludeSemantics: true,
          child: InkResponse(
            onTap: () => aoEscolher(i),
            radius: 36,
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              // Traço curto por cima do separador activo.
              Container(
                width: 28,
                height: 3,
                decoration: BoxDecoration(
                  color: activo ? Cores.escuro : Colors.transparent,
                  borderRadius: const BorderRadius.vertical(bottom: Radius.circular(3)),
                ),
              ),
              const SizedBox(height: 10),
              Badge(
                isLabelVisible: contador > 0,
                label: Text('$contador'),
                child: Icon(activo ? iconeActivo : icone, color: cor, size: 26),
              ),
              const SizedBox(height: 4),
              Text(nome,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontSize: 12.5, fontWeight: activo ? FontWeight.w600 : FontWeight.w500, color: cor)),
              const SizedBox(height: 10),
            ]),
          ),
        ),
      );
    }

    return Container(
      decoration: const BoxDecoration(
        color: Cores.cartao,
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
        boxShadow: [BoxShadow(color: Color(0x14000000), blurRadius: 24, offset: Offset(0, -4))],
      ),
      child: SafeArea(
        top: false,
        child: ListenableBuilder(
          listenable: AlertasLocais.instancia,
          builder: (context, _) => Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
            item(0, Icons.grid_view_outlined, Icons.grid_view_rounded, 'Início'),
            item(1, Icons.history, Icons.history, 'Historial'),
            Padding(
              padding: const EdgeInsets.fromLTRB(4, 8, 4, 12),
              child: Semantics(
                button: true,
                label: 'Fotografar uma planta',
                excludeSemantics: true,
                child: Material(
                  color: Cores.lima,
                  shape: const CircleBorder(),
                  elevation: 0,
                  child: InkWell(
                    customBorder: const CircleBorder(),
                    onTap: aoFotografar,
                    child: const SizedBox(
                      width: 64,
                      height: 64,
                      child: Icon(Icons.photo_camera_outlined, color: Cores.sobreLima, size: 28),
                    ),
                  ),
                ),
              ),
            ),
            item(2, Icons.notifications_none, Icons.notifications, 'Alertas', contador: AlertasLocais.instancia.naoLidos),
            item(3, Icons.settings_outlined, Icons.settings, 'Definições'),
          ]),
        ),
      ),
    );
  }
}
