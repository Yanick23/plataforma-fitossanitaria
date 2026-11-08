import 'package:flutter/material.dart';

import '../services/api_cliente.dart';
import '../services/sessao.dart';
import '../tema.dart';
import '../widgets/botoes.dart';
import '../widgets/campos.dart';
import '../widgets/marca.dart';
import 'definicoes_screen.dart';
import 'registo_screen.dart';

/// Login por telefone e palavra-passe (RF10). Só é preciso rede na primeira vez.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _form = GlobalKey<FormState>();
  final _telefone = TextEditingController();
  final _palavraPasse = TextEditingController();
  bool _aEntrar = false;
  String? _erro;

  @override
  void dispose() {
    _telefone.dispose();
    _palavraPasse.dispose();
    super.dispose();
  }

  Future<void> _entrar() async {
    if (!_form.currentState!.validate()) return;
    setState(() {
      _aEntrar = true;
      _erro = null;
    });
    try {
      final r = await ApiCliente.instancia.login(_telefone.text.replaceAll(' ', ''), _palavraPasse.text);
      await Sessao.instancia.iniciar(r.token, r.utilizador); // o main.dart muda para o ecrã inicial
    } on ErroApi catch (e) {
      if (mounted) setState(() => _erro = e.mensagem);
    } catch (e) {
      if (mounted) setState(() => _erro = 'Erro inesperado: $e');
    } finally {
      if (mounted) setState(() => _aEntrar = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final temas = Theme.of(context).textTheme;
    return Scaffold(
      body: SafeArea(
        child: Form(
          key: _form,
          child: ListView(padding: const EdgeInsets.fromLTRB(24, 8, 24, 24), children: [
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: () => Navigator.of(context)
                    .push(MaterialPageRoute(builder: (_) => const DefinicoesScreen(apenasServidor: true))),
                icon: const Icon(Icons.dns_outlined, size: 18),
                label: const Text('Servidor'),
                style: TextButton.styleFrom(foregroundColor: Cores.textoSecundario),
              ),
            ),
            const SizedBox(height: 16),
            const MarcaApp(),
            const SizedBox(height: 40),
            Text('Entrar', style: temas.headlineMedium),
            const SizedBox(height: 6),
            const Text('Use o número de telefone com que se registou.',
                style: TextStyle(fontSize: 15, color: Cores.textoSecundario, height: 1.4)),
            const SizedBox(height: 28),
            CampoTexto(
              controlador: _telefone,
              rotulo: 'Telefone',
              icone: Icons.phone_outlined,
              teclado: TextInputType.phone,
              validar: validarTelefone,
            ),
            const SizedBox(height: 14),
            CampoTexto(
              controlador: _palavraPasse,
              rotulo: 'Palavra-passe',
              icone: Icons.lock_outline,
              oculto: true,
              validar: validarPalavraPasse,
              accao: TextInputAction.done,
            ),
            if (_erro != null) ...[const SizedBox(height: 14), MensagemErro(_erro!)],
            const SizedBox(height: 24),
            BotaoPrincipal(texto: _aEntrar ? 'A entrar…' : 'Entrar', aoPremir: _aEntrar ? null : _entrar),
            const SizedBox(height: 16),
            Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              const Text('Ainda não tem conta?', style: TextStyle(color: Cores.textoSecundario)),
              TextButton(
                onPressed: _aEntrar
                    ? null
                    : () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const RegistoScreen())),
                child: const Text('Criar conta'),
              ),
            ]),
            const SizedBox(height: 32),
            const Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Icon(Icons.wifi_off_outlined, size: 16, color: Cores.textoTerciario),
              SizedBox(width: 8),
              Expanded(
                child: Text('Só precisa de internet para entrar a primeira vez. Depois, a app funciona sem rede.',
                    style: TextStyle(fontSize: 13, color: Cores.textoSecundario, height: 1.4)),
              ),
            ]),
          ]),
        ),
      ),
    );
  }
}
