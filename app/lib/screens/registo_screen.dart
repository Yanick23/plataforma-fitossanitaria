import 'package:flutter/material.dart';

import '../services/api_cliente.dart';
import '../services/sessao.dart';
import '../tema.dart';
import '../widgets/botoes.dart';
import '../widgets/campos.dart';

/// Criação de conta de agricultor (RF10). As contas de técnico são criadas
/// pelo administrador na API.
class RegistoScreen extends StatefulWidget {
  const RegistoScreen({super.key});

  @override
  State<RegistoScreen> createState() => _RegistoScreenState();
}

class _RegistoScreenState extends State<RegistoScreen> {
  final _form = GlobalKey<FormState>();
  final _nome = TextEditingController();
  final _telefone = TextEditingController();
  final _area = TextEditingController();
  final _palavraPasse = TextEditingController();
  final _confirmacao = TextEditingController();
  bool _aCriar = false;
  String? _erro;

  @override
  void dispose() {
    for (final c in [_nome, _telefone, _area, _palavraPasse, _confirmacao]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _criar() async {
    if (!_form.currentState!.validate()) return;
    setState(() {
      _aCriar = true;
      _erro = null;
    });
    try {
      final r = await ApiCliente.instancia.registar(
        nome: _nome.text.trim(),
        telefone: _telefone.text.replaceAll(' ', ''),
        palavraPasse: _palavraPasse.text,
        area: _area.text.trim().isEmpty ? null : _area.text.trim(),
      );
      if (!mounted) return;
      Navigator.of(context).pop();
      await Sessao.instancia.iniciar(r.token, r.utilizador);
    } on ErroApi catch (e) {
      if (mounted) setState(() => _erro = e.mensagem);
    } finally {
      if (mounted) setState(() => _aCriar = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Form(
          key: _form,
          child: ListView(padding: const EdgeInsets.fromLTRB(24, 12, 24, 24), children: [
            const Align(alignment: Alignment.centerLeft, child: BotaoVoltar()),
            const SizedBox(height: 20),
            const Text('Criar conta', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800)),
            const SizedBox(height: 4),
            const Text('Conta de agricultor', style: TextStyle(color: Cores.textoSecundario)),
            const SizedBox(height: 20),
            CampoTexto(
              controlador: _nome,
              rotulo: 'Nome',
              icone: Icons.person_outline,
              validar: (v) => (v ?? '').trim().length >= 2 ? null : 'Escreva o seu nome',
            ),
            const SizedBox(height: 12),
            CampoTexto(
              controlador: _telefone,
              rotulo: 'Telefone',
              icone: Icons.phone_outlined,
              teclado: TextInputType.phone,
              validar: validarTelefone,
            ),
            const SizedBox(height: 12),
            CampoTexto(
              controlador: _area,
              rotulo: 'Distrito (opcional)',
              icone: Icons.place_outlined,
              dica: 'Permite ao técnico da sua zona ver os seus diagnósticos',
            ),
            const SizedBox(height: 12),
            CampoTexto(
              controlador: _palavraPasse,
              rotulo: 'Palavra-passe',
              icone: Icons.lock_outline,
              oculto: true,
              validar: validarPalavraPasse,
            ),
            const SizedBox(height: 12),
            CampoTexto(
              controlador: _confirmacao,
              rotulo: 'Repita a palavra-passe',
              icone: Icons.lock_outline,
              oculto: true,
              accao: TextInputAction.done,
              validar: (v) => v == _palavraPasse.text ? null : 'As palavras-passe não coincidem',
            ),
            if (_erro != null) ...[
              const SizedBox(height: 12),
              Text(_erro!, style: const TextStyle(color: Cores.laranjaEscuro, fontWeight: FontWeight.w600)),
            ],
            const SizedBox(height: 22),
            BotaoPrincipal(texto: _aCriar ? 'A criar...' : 'Criar conta', aoPremir: _aCriar ? null : _criar),
          ]),
        ),
      ),
    );
  }
}
