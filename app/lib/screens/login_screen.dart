import 'package:flutter/material.dart';

import '../services/api_cliente.dart';
import '../services/sessao.dart';
import '../tema.dart';
import '../widgets/botoes.dart';
import '../widgets/campos.dart';
import '../widgets/ecra_escuro.dart';
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
    return EcraEscuro(
      cabecalho: const Padding(
        padding: EdgeInsets.fromLTRB(0, 36, 0, 40),
        child: Center(child: MarcaApp()),
      ),
      filhos: [
        Form(
          key: _form,
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            const Text('Entrar', style: TextStyle(fontSize: 32, fontWeight: FontWeight.w700, letterSpacing: -0.4)),
            const SizedBox(height: 6),
            const Text('Insira o seu número de telefone para continuar.',
                style: TextStyle(fontSize: 16, color: Cores.textoSecundario)),
            const SizedBox(height: 24),
            CampoTexto(
              controlador: _telefone,
              rotulo: 'Número de telefone',
              icone: Icons.phone_in_talk_outlined,
              teclado: TextInputType.phone,
              exemplo: 'Ex.: 84 123 4567',
              validar: validarTelefone,
            ),
            const SizedBox(height: 16),
            CampoTexto(
              controlador: _palavraPasse,
              rotulo: 'Palavra-passe',
              icone: Icons.lock_outline,
              oculto: true,
              validar: validarPalavraPasse,
              accao: TextInputAction.done,
            ),
            if (_erro != null) ...[const SizedBox(height: 16), MensagemErro(_erro!)],
            const SizedBox(height: 24),
            BotaoPrincipal(texto: _aEntrar ? 'A entrar…' : 'Entrar', aoPremir: _aEntrar ? null : _entrar),
            const SizedBox(height: 12),
            Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              const Text('Ainda não tem conta?', style: TextStyle(fontSize: 15, color: Cores.textoSecundario)),
              TextButton(
                onPressed: _aEntrar
                    ? null
                    : () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const RegistoScreen())),
                style: TextButton.styleFrom(foregroundColor: Cores.texto),
                child: const Text('Criar conta'),
              ),
            ]),
            const SizedBox(height: 16),
            const Text('Só precisa de internet para entrar a primeira vez. Depois, a app funciona sem rede.',
                textAlign: TextAlign.center, style: TextStyle(fontSize: 13.5, color: Cores.textoSecundario, height: 1.4)),
            const SizedBox(height: 4),
            Center(
              child: TextButton(
                onPressed: () => Navigator.of(context)
                    .push(MaterialPageRoute(builder: (_) => const DefinicoesScreen(apenasServidor: true))),
                style: TextButton.styleFrom(foregroundColor: Cores.textoSecundario),
                child: const Text('Endereço do servidor'),
              ),
            ),
          ]),
        ),
      ],
    );
  }
}
