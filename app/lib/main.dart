import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'models/utilizador.dart';
import 'screens/historial_screen.dart';
import 'screens/inicio_screen.dart';
import 'screens/login_screen.dart';
import 'services/acompanhamento.dart';
import 'services/alertas_locais.dart';
import 'services/catalogo.dart';
import 'services/sessao.dart';
import 'services/sincronizacao.dart';
import 'services/visitas_locais.dart';
import 'tema.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  await Sessao.instancia.carregar();
  await Catalogo.instancia.carregar();
  await AlertasLocais.instancia.carregar();
  await VisitasLocais.instancia.carregar();
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

/// Barra inferior Início / Historial (Ecrãs 1 e 7 do protótipo).
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
        body: IndexedStack(index: aba, children: const [InicioScreen(), HistorialScreen()]),
        bottomNavigationBar: NavigationBar(
          selectedIndex: aba,
          backgroundColor: Cores.cartao,
          indicatorColor: Cores.verdeClaro,
          onDestinationSelected: (i) => NavegacaoPrincipal.abaActual.value = i,
          destinations: const [
            NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Início'),
            NavigationDestination(icon: Icon(Icons.history), label: 'Historial'),
          ],
        ),
      ),
    );
  }
}
