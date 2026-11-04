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
  final _palavraPasse = TextEditingController();
  final _confirmacao = TextEditingController();
  bool _aCriar = false;
  String? _erro;

  // Zona: províncias e distritos de Moçambique (da API; o registo já precisa de rede).
  List<Regiao>? _provincias;
  List<Regiao> _distritos = const [];
  String? _provincia;
  Regiao? _distrito;
  String? _erroRegioes;

  @override
  void initState() {
    super.initState();
    _carregarProvincias();
  }

  Future<void> _carregarProvincias() async {
    try {
      final p = await ApiCliente.instancia.provincias();
      if (mounted) setState(() => _provincias = p);
    } on ErroApi catch (e) {
      if (mounted) setState(() => _erroRegioes = e.mensagem);
    }
  }

  Future<void> _escolherProvincia(String? codigo) async {
    setState(() {
      _provincia = codigo;
      _distrito = null;
      _distritos = const [];
    });
    if (codigo == null) return;
    try {
      final d = await ApiCliente.instancia.distritos(codigo);
      if (mounted && _provincia == codigo) setState(() => _distritos = d);
    } on ErroApi catch (e) {
      if (mounted) setState(() => _erroRegioes = e.mensagem);
    }
  }

  @override
  void dispose() {
    for (final c in [_nome, _telefone, _palavraPasse, _confirmacao]) {
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
        area: _distrito?.nome,
        distritoId: _distrito == null ? null : int.parse(_distrito!.chave),
      );
      if (!mounted) return;
      Navigator.of(context).pop();
      await Sessao.instancia.iniciar(r.token, r.utilizador);
    } on ErroApi catch (e) {
      if (mounted) setState(() => _erro = e.mensagem);
    } catch (e) {
      if (mounted) setState(() => _erro = 'Erro inesperado: $e');
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
            _Lista<String>(
              rotulo: 'Província',
              icone: Icons.map_outlined,
              valor: _provincia,
              opcoes: [for (final p in _provincias ?? const <Regiao>[]) (p.chave, p.nome)],
              aoMudar: _escolherProvincia,
              aCarregar: _provincias == null && _erroRegioes == null,
            ),
            const SizedBox(height: 12),
            _Lista<String>(
              rotulo: 'Distrito',
              icone: Icons.place_outlined,
              valor: _distrito?.chave,
              opcoes: [for (final d in _distritos) (d.chave, d.nome)],
              aoMudar: (chave) => setState(() => _distrito = _distritos.where((d) => d.chave == chave).firstOrNull),
              dica: _erroRegioes ??
                  'Recebe os alertas do seu distrito e o técnico da zona pode ajudar com os seus diagnósticos',
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

/// Lista de escolha no mesmo estilo dos campos de texto.
class _Lista<T> extends StatelessWidget {
  const _Lista({
    required this.rotulo,
    required this.icone,
    required this.valor,
    required this.opcoes,
    required this.aoMudar,
    this.dica,
    this.aCarregar = false,
  });

  final String rotulo;
  final IconData icone;
  final T? valor;
  final List<(T, String)> opcoes;
  final ValueChanged<T?> aoMudar;
  final String? dica;
  final bool aCarregar;

  @override
  Widget build(BuildContext context) {
    final borda = OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide.none);
    return DropdownButtonFormField<T>(
      initialValue: valor,
      key: ValueKey('$rotulo-$valor-${opcoes.length}'),
      isExpanded: true,
      items: [for (final (v, nome) in opcoes) DropdownMenuItem(value: v, child: Text(nome))],
      onChanged: opcoes.isEmpty ? null : aoMudar,
      decoration: InputDecoration(
        labelText: aCarregar ? '$rotulo (a carregar…)' : rotulo,
        helperText: dica,
        helperMaxLines: 2,
        prefixIcon: Icon(icone, color: Cores.textoSecundario),
        filled: true,
        fillColor: Cores.cartao,
        border: borda,
        enabledBorder: borda,
        disabledBorder: borda,
        focusedBorder: borda.copyWith(borderSide: const BorderSide(color: Cores.verde, width: 2)),
      ),
    );
  }
}
