import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart' show MediaType;

import '../models/cultura.dart';
import '../models/diagnostico.dart';
import '../models/patologia.dart';
import '../models/utilizador.dart';
import 'sessao.dart';

/// Erro da API com mensagem pronta a mostrar.
class ErroApi implements Exception {
  const ErroApi(this.mensagem, {this.codigo});
  final String mensagem;
  final int? codigo;
  bool get naoAutorizado => codigo == 401;
  @override
  String toString() => mensagem;
}

class RespostaLogin {
  const RespostaLogin(this.token, this.utilizador);
  final String token;
  final Utilizador utilizador;
}

class RespostaSincronizacao {
  const RespostaSincronizacao(this.confirmados, this.rejeitados);
  final Set<String> confirmados;
  final Set<String> rejeitados;
}

class InfoModelo {
  const InfoModelo({
    required this.versao,
    required this.classes,
    required this.urlFicheiro,
    required this.sha256,
    this.acuraciaTeste,
  });
  final int versao;
  final List<String> classes;
  final String urlFicheiro;
  final String sha256;
  final double? acuraciaTeste;
}

/// Cliente HTTP da API FastAPI (REST + JSON).
class ApiCliente {
  ApiCliente._();
  static final instancia = ApiCliente._();

  static const _tempoLimite = Duration(seconds: 12);
  final _http = http.Client();

  Uri _uri(String caminho, [Map<String, String>? query]) =>
      Uri.parse('${Sessao.instancia.urlApi}$caminho').replace(queryParameters: query);

  Map<String, String> get _cabecalhos => {
        'Content-Type': 'application/json',
        if (Sessao.instancia.token != null) 'Authorization': 'Bearer ${Sessao.instancia.token}',
      };

  Future<http.Response> _enviar(Future<http.Response> Function() pedido) async {
    try {
      final r = await pedido().timeout(_tempoLimite);
      if (r.statusCode >= 200 && r.statusCode < 300) return r;
      throw ErroApi(_detalhe(r), codigo: r.statusCode);
    } on TimeoutException {
      throw ErroApi('O servidor não respondeu (${Sessao.instancia.urlApi}).\n'
          'Confirme que a API está a correr no PC e que o endereço em "Servidor" está certo.');
    } on SocketException {
      throw ErroApi('Sem ligação ao servidor (${Sessao.instancia.urlApi}).\n'
          'Confirme que o telemóvel está na mesma rede Wi-Fi do PC e o endereço em "Servidor".');
    } on http.ClientException {
      throw ErroApi('Sem ligação ao servidor (${Sessao.instancia.urlApi}).\n'
          'Confirme que o telemóvel está na mesma rede Wi-Fi do PC e o endereço em "Servidor".');
    } on HttpException catch (e) {
      throw ErroApi('Erro de comunicação: ${e.message}');
    } on FormatException {
      throw const ErroApi('Endereço da API inválido.');
    }
  }

  static String _detalhe(http.Response r) {
    try {
      final detalhe = (jsonDecode(utf8.decode(r.bodyBytes)) as Map)['detail'];
      if (detalhe is String) return detalhe;
      if (detalhe is List && detalhe.isNotEmpty) return 'Dados inválidos: ${(detalhe.first as Map)['msg']}';
    } catch (_) {}
    return 'Erro ${r.statusCode} do servidor';
  }

  dynamic _json(http.Response r) => jsonDecode(utf8.decode(r.bodyBytes));

  RespostaLogin _login(http.Response r) {
    final j = _json(r) as Map<String, dynamic>;
    return RespostaLogin(
        j['access_token'] as String, Utilizador.fromJson(j['utilizador'] as Map<String, dynamic>));
  }

  // --- Autenticação (RF10) ---------------------------------------------------

  Future<RespostaLogin> login(String telefone, String palavraPasse) async => _login(await _enviar(() =>
      _http.post(_uri('/auth/login'),
          headers: _cabecalhos, body: jsonEncode({'telefone': telefone, 'palavra_passe': palavraPasse}))));

  Future<RespostaLogin> registar(
          {required String nome, required String telefone, required String palavraPasse, String? area}) async =>
      _login(await _enviar(() => _http.post(_uri('/auth/registar'),
          headers: _cabecalhos,
          body: jsonEncode({'nome': nome, 'telefone': telefone, 'palavra_passe': palavraPasse, 'area': area}))));

  Future<RespostaLogin> renovarToken() async =>
      _login(await _enviar(() => _http.post(_uri('/auth/renovar'), headers: _cabecalhos)));

  // --- Diagnósticos (RF09) ---------------------------------------------------

  Future<RespostaSincronizacao> enviarDiagnosticos(List<Diagnostico> lote) async {
    final r = await _enviar(() => _http.post(_uri('/diagnosticos'),
        headers: _cabecalhos, body: jsonEncode([for (final d in lote) d.paraApi()])));
    final j = _json(r) as Map<String, dynamic>;
    return RespostaSincronizacao(
      (j['confirmados'] as List).cast<String>().toSet(),
      (j['rejeitados'] as List).cast<String>().toSet(),
    );
  }

  Future<void> enviarImagem(String diagnosticoId, String caminho) async {
    final pedido = http.MultipartRequest('POST', _uri('/diagnosticos/$diagnosticoId/imagem'))
      ..headers['Authorization'] = 'Bearer ${Sessao.instancia.token}'
      ..files.add(await http.MultipartFile.fromPath('ficheiro', caminho,
          contentType: MediaType('image', caminho.toLowerCase().endsWith('.png') ? 'png' : 'jpeg')));
    await _enviar(() async => http.Response.fromStream(await _http.send(pedido)));
  }

  /// PNG com o mapa Grad-CAM gerado no servidor.
  Future<Uint8List> gradcam(String diagnosticoId) async =>
      (await _enviar(() => _http.get(_uri('/diagnosticos/$diagnosticoId/gradcam'), headers: _cabecalhos)))
          .bodyBytes;

  // --- Catálogo (RF06/RF07, actualizável) ------------------------------------

  Future<List<Patologia>> patologias() async {
    final lista = _json(await _enviar(() => _http.get(_uri('/patologias'), headers: _cabecalhos))) as List;
    return [
      for (final p in lista.cast<Map<String, dynamic>>())
        if (Cultura.values.any((c) => c.id == p['cultura_id'])) Patologia.daApi(p),
    ];
  }

  // --- Modelos (RF12) --------------------------------------------------------

  /// Devolve null se o servidor ainda não tiver modelos desta cultura.
  Future<InfoModelo?> ultimaVersaoModelo(Cultura cultura) async {
    try {
      final j = _json(await _enviar(
              () => _http.get(_uri('/modelos/${cultura.id}/ultima-versao'), headers: _cabecalhos)))
          as Map<String, dynamic>;
      return InfoModelo(
        versao: j['versao'] as int,
        classes: (j['classes'] as List).cast<String>(),
        urlFicheiro: j['url_ficheiro'] as String,
        sha256: j['sha256'] as String,
        acuraciaTeste: (j['acuracia_teste'] as num?)?.toDouble(),
      );
    } on ErroApi catch (e) {
      if (e.codigo == 404) return null;
      rethrow;
    }
  }

  Future<Uint8List> descarregar(String url) async {
    // O servidor devolve o URL absoluto que conhece; trocamos a origem pela
    // configurada na app, para funcionar atrás de qualquer endereço/IP.
    final caminho = Uri.parse(url).path;
    return (await _enviar(() => _http.get(_uri(caminho), headers: _cabecalhos).timeout(const Duration(minutes: 3))))
        .bodyBytes;
  }
}
