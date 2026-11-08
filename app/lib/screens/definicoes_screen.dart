import 'package:flutter/material.dart';

import '../models/audio.dart';
import '../models/cultura.dart';
import '../models/modelo_ml.dart';
import '../services/acompanhamento.dart';
import '../services/alertas_locais.dart';
import '../services/api_cliente.dart';
import '../services/catalogo.dart';
import '../services/dados_zona.dart';
import '../services/notificacoes_fundo.dart';
import '../services/visitas_locais.dart';
import '../services/vozes_locais.dart';
import '../services/gestor_modelos.dart';
import '../services/sessao.dart';
import '../services/sincronizacao.dart';
import '../tema.dart';
import '../widgets/botoes.dart';
import '../widgets/campos.dart';
import 'diagnostico_tecnico_screen.dart';

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

  bool _aMudarLingua = false;

  /// Muda a língua na conta (precisa de rede) e descarrega já as gravações dessa língua.
  Future<void> _mudarLingua(String? lingua) async {
    final mensageiro = ScaffoldMessenger.of(context);
    setState(() => _aMudarLingua = true);
    try {
      final u = await ApiCliente.instancia.mudarLingua(lingua);
      await Sessao.instancia.actualizarUtilizador(u);
      final novas = await VozesLocais.instancia.sincronizar(
          [...Catalogo.instancia.audios, for (final a in AlertasLocais.instancia.alertas) ...a.audios], lingua);
      mensageiro.showSnackBar(SnackBar(
          content: Text(lingua == null
              ? 'Mensagens só em texto'
              : 'Língua: ${Lingua.nomeDe(lingua)}. ${novas == 0 ? 'Ainda não há gravações novas nesta língua.' : '$novas gravação(ões) descarregada(s).'}')));
    } on ErroApi catch (e) {
      mensageiro.showSnackBar(SnackBar(content: Text('Não foi possível mudar a língua: ${e.mensagem}')));
    } finally {
      if (mounted) setState(() => _aMudarLingua = false);
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
      appBar: AppBar(title: const Text('Definições', style: TextStyle(fontWeight: FontWeight.w600))),
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
          const SizedBox(height: 20),
          _seccao('Conta', [
            _linha('Nome', utilizador.nome),
            _linha('Telefone', utilizador.telefone),
            _linha('Perfil', utilizador.perfil.nome),
            if (utilizador.area != null) _linha('Distrito', utilizador.area!),
          ]),
          const SizedBox(height: 20),
          _seccao('Ouvir as mensagens', [
            const Text('As recomendações e os alertas podem ter uma gravação na sua língua. '
                'Toque em «Ouvir» para a escutar, mesmo sem rede.',
                style: TextStyle(color: Cores.textoSecundario, height: 1.35)),
            const SizedBox(height: 10),
            DropdownButtonFormField<String?>(
              initialValue: utilizador.lingua,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Língua', prefixIcon: Icon(Icons.record_voice_over_outlined)),
              items: [
                const DropdownMenuItem<String?>(value: null, child: Text('Só texto (sem áudio)')),
                for (final l in Lingua.todas) DropdownMenuItem<String?>(value: l.codigo, child: Text(l.nome)),
              ],
              onChanged: _aMudarLingua ? null : _mudarLingua,
            ),
            if (_aMudarLingua) const Padding(padding: EdgeInsets.only(top: 8), child: LinearProgressIndicator()),
          ]),
          const SizedBox(height: 20),
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
          const SizedBox(height: 20),
          _seccao('Avançado', [
            Material(
              color: Colors.transparent,
              child: ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.speed_outlined),
                title: const Text('Desempenho no telemóvel'),
                subtitle: const Text('Tempo e memória do modelo neste aparelho'),
                trailing: const Icon(Icons.chevron_right, color: Cores.textoTerciario),
                onTap: () => Navigator.of(context)
                    .push(MaterialPageRoute(builder: (_) => const DiagnosticoTecnicoScreen())),
              ),
            ),
          ]),
          const SizedBox(height: 24),
          OutlinedButton.icon(
            icon: const Icon(Icons.logout, size: 20),
            label: const Text('Terminar sessão'),
            style: OutlinedButton.styleFrom(foregroundColor: Cores.criticoTexto),
            onPressed: () async {
              Navigator.of(context).popUntil((r) => r.isFirst);
              await Sessao.instancia.terminar();
              // Alertas e visitas pertencem à conta (e à zona) que saiu.
              await AlertasLocais.instancia.limpar();
              await VisitasLocais.instancia.limpar();
              await CampanhasLocais.instancia.limpar();
              await CalendarioLocal.instancia.limpar();
              await NotificacoesFundo.parar();
              Acompanhamento.instancia.limpar();
            },
          ),
        ],
      ]),
    );
  }

  Widget _seccao(String titulo, List<Widget> filhos) => Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        TituloSeccao(titulo),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: decoracaoCartao(),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [...filhos]),
        ),
      ]);

  Widget _linha(String rotulo, String valor) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 5),
        child: Row(children: [
          Expanded(child: Text(rotulo, style: const TextStyle(color: Cores.textoSecundario))),
          Text(valor, style: const TextStyle(fontWeight: FontWeight.w500)),
        ]),
      );
}
