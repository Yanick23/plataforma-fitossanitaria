import 'package:flutter/material.dart';

import '../services/api_cliente.dart';
import '../services/sessao.dart';
import '../tema.dart';
import '../widgets/botoes.dart';
import '../widgets/campos.dart';
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
    return Scaffold(
      body: SafeArea(
        child: Form(
          key: _form,
          child: ListView(padding: const EdgeInsets.fromLTRB(24, 12, 24, 24), children: [
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: () => Navigator.of(context)
                    .push(MaterialPageRoute(builder: (_) => const DefinicoesScreen(apenasServidor: true))),
                icon: const Icon(Icons.dns_outlined, size: 18),
                label: const Text('Servidor'),
              ),
            ),
            const SizedBox(height: 24),
            Center(
              child: Container(
                width: 76,
                height: 76,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(colors: [Cores.verde, Cores.verdeEscuro]),
                  borderRadius: BorderRadius.circular(22),
                ),
                child: const Icon(Icons.eco, color: Colors.white, size: 40),
              ),
            ),
            const SizedBox(height: 18),
            const Text('AgroDiagnóstico',
                textAlign: TextAlign.center, style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800)),
            const SizedBox(height: 6),
            const Text('Entre com o seu número de telefone',
                textAlign: TextAlign.center, style: TextStyle(color: Cores.textoSecundario)),
            const SizedBox(height: 28),
            CampoTexto(
              controlador: _telefone,
              rotulo: 'Telefone',
              icone: Icons.phone_outlined,
              teclado: TextInputType.phone,
              validar: validarTelefone,
            ),
            const SizedBox(height: 12),
            CampoTexto(
              controlador: _palavraPasse,
              rotulo: 'Palavra-passe',
              icone: Icons.lock_outline,
              oculto: true,
              validar: validarPalavraPasse,
              accao: TextInputAction.done,
            ),
            if (_erro != null) ...[
              const SizedBox(height: 12),
              Text(_erro!, style: const TextStyle(color: Cores.laranjaEscuro, fontWeight: FontWeight.w600)),
            ],
            const SizedBox(height: 22),
            BotaoPrincipal(texto: _aEntrar ? 'A entrar...' : 'Entrar', aoPremir: _aEntrar ? null : _entrar),
            const SizedBox(height: 12),
            BotaoSecundario(
              texto: 'Criar conta',
              aoPremir: _aEntrar
                  ? null
                  : () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const RegistoScreen())),
            ),
            const SizedBox(height: 18),
            const Text(
              'Depois de entrar uma vez, a app funciona sem internet.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12, color: Cores.textoSecundario),
            ),
          ]),
        ),
      ),
    );
  }
}
