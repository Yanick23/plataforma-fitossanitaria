import 'package:flutter/material.dart';

import '../models/cultura.dart';
import '../models/modelo_ml.dart';
import '../services/acompanhamento.dart';
import '../services/alertas_locais.dart';
import '../services/visitas_locais.dart';
import '../services/gestor_modelos.dart';
import '../services/sessao.dart';
import '../services/sincronizacao.dart';
import '../tema.dart';
import '../widgets/botoes.dart';
import '../widgets/campos.dart';

/// Endereço da API, conta, versões dos modelos e sincronização manual.
class DefinicoesScreen extends StatefulWidget {
  const DefinicoesScreen({super.key, this.apenasServidor = false});

  /// No ecrã de login só se mostra o endereço do servidor.
  final bool apenasServidor;

  @override
  State<DefinicoesScreen> createState() => _DefinicoesScreenState();
}

class _DefinicoesScreenState extends State<DefinicoesScreen> {
  late final _url = TextEditingController(text: Sessao.instancia.urlApi);
  Future<List<ModeloML>>? _modelos;

  @override
  void initState() {
    super.initState();
    _carregarModelos();
  }

  void _carregarModelos() =>
      _modelos = Future.wait(Cultura.values.map(GestorModelos.instancia.modeloActual));

  @override
  void dispose() {
    _url.dispose();
    super.dispose();
  }

  Future<void> _guardarUrl() async {
    final url = _url.text.trim();
    if (!RegExp(r'^https?://[^\s/]+').hasMatch(url)) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Endereço inválido. Ex.: http://192.168.1.100:8000')));
      return;
    }
    await Sessao.instancia.definirUrl(url);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Endereço do servidor guardado')));
    }
  }

  Future<void> _sincronizar() async {
    final resumo = await Sincronizacao.instancia.sincronizar();
    if (!mounted) return;
    setState(_carregarModelos);
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(resumo.mensagem)));
  }

  @override
  Widget build(BuildContext context) {
    final utilizador = Sessao.instancia.utilizador.value;
    return Scaffold(
      appBar: AppBar(title: const Text('Definições', style: TextStyle(fontWeight: FontWeight.w800))),
      body: ListView(padding: const EdgeInsets.fromLTRB(16, 4, 16, 24), children: [
        _seccao('Servidor (API)', [
          CampoTexto(
            controlador: _url,
            rotulo: 'Endereço da API',
            icone: Icons.dns_outlined,
            teclado: TextInputType.url,
            dica: 'O IP do PC onde corre a API, na mesma rede Wi-Fi',
            accao: TextInputAction.done,
          ),
          const SizedBox(height: 10),
          BotaoSecundario(texto: 'Guardar endereço', aoPremir: _guardarUrl),
        ]),
        if (!widget.apenasServidor && utilizador != null) ...[
          const SizedBox(height: 12),
          _seccao('Conta', [
            _linha('Nome', utilizador.nome),
            _linha('Telefone', utilizador.telefone),
            _linha('Perfil', utilizador.perfil.nome),
            if (utilizador.area != null) _linha('Distrito', utilizador.area!),
          ]),
          const SizedBox(height: 12),
          _seccao('Modelos de classificação', [
            FutureBuilder<List<ModeloML>>(
              future: _modelos,
              builder: (context, s) => Column(children: [
                for (final m in s.data ?? const <ModeloML>[])
                  _linha(m.cultura.nome, 'versão ${m.versao}${m.embutido ? ' (embutida)' : m.piloto ? ' (piloto no seu distrito)' : ''}'),
              ]),
            ),
          ]),
          const SizedBox(height: 12),
          ListenableBuilder(
            listenable: Sincronizacao.instancia,
            builder: (context, _) {
              final s = Sincronizacao.instancia;
              return _seccao('Sincronização', [
                if (s.ultimo != null) Text(s.ultimo!.mensagem, style: const TextStyle(color: Cores.textoSecundario)),
                const SizedBox(height: 10),
                BotaoPrincipal(
                  texto: s.emCurso ? 'A sincronizar...' : 'Sincronizar agora',
                  icone: Icons.sync,
                  aoPremir: s.emCurso ? null : _sincronizar,
                ),
              ]);
            },
          ),
          const SizedBox(height: 12),
          BotaoSecundario(
            texto: 'Terminar sessão',
            aoPremir: () async {
              Navigator.of(context).popUntil((r) => r.isFirst);
              await Sessao.instancia.terminar();
              // Alertas e visitas pertencem à conta (e à zona) que saiu.
              await AlertasLocais.instancia.limpar();
              await VisitasLocais.instancia.limpar();
              Acompanhamento.instancia.limpar();
            },
          ),
        ],
      ]),
    );
  }

  Widget _seccao(String titulo, List<Widget> filhos) => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(color: Cores.cartao, borderRadius: BorderRadius.circular(16), boxShadow: sombraSuave),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Text(titulo, style: const TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 10),
          ...filhos,
        ]),
      );

  Widget _linha(String rotulo, String valor) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 3),
        child: Row(children: [
          Expanded(child: Text(rotulo, style: const TextStyle(color: Cores.textoSecundario))),
          Text(valor, style: const TextStyle(fontWeight: FontWeight.w700)),
        ]),
      );
}
