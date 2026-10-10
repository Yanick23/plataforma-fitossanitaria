import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../models/utilizador.dart';

/// Endereço por omissão da API: o PC na mesma rede Wi-Fi (porta 8000).
/// Muda-se no ecrã de login ou nas definições.
const urlApiPorOmissao = 'http://192.168.1.100:8000';

/// Sessão do utilizador (RF10). O token JWT e os dados do utilizador ficam no
/// armazenamento seguro do Android (Keystore), por isso a app continua a
/// funcionar sem rede depois do primeiro login (RNF01).
class Sessao {
  Sessao._();
  static final instancia = Sessao._();

  static const _armazem = FlutterSecureStorage();
  static const _chaveToken = 'token';
  static const _chaveUtilizador = 'utilizador';
  static const _chaveUrl = 'url_api';

  String? token;
  String urlApi = urlApiPorOmissao;

  /// Utilizador com sessão iniciada (null = mostrar o login).
  final utilizador = ValueNotifier<Utilizador?>(null);

  Future<void> carregar() async {
    urlApi = await _armazem.read(key: _chaveUrl) ?? urlApiPorOmissao;
    token = await _armazem.read(key: _chaveToken);
    final json = await _armazem.read(key: _chaveUtilizador);
    if (token != null && json != null) {
      utilizador.value = Utilizador.fromJson(jsonDecode(json) as Map<String, dynamic>);
    }
  }

  Future<void> iniciar(String novoToken, Utilizador u) async {
    token = novoToken;
    await _armazem.write(key: _chaveToken, value: novoToken);
    await _armazem.write(key: _chaveUtilizador, value: jsonEncode(u.toJson()));
    utilizador.value = u;
  }

  /// Guarda o token renovado em cada sincronização (secção 4.4.5).
  Future<void> renovarToken(String novoToken) async {
    token = novoToken;
    await _armazem.write(key: _chaveToken, value: novoToken);
  }

  Future<void> definirUrl(String url) async {
    urlApi = url.trim().replaceAll(RegExp(r'/+$'), '');
    await _armazem.write(key: _chaveUrl, value: urlApi);
  }

  Future<void> terminar() async {
    token = null;
    await _armazem.delete(key: _chaveToken);
    await _armazem.delete(key: _chaveUtilizador);
    utilizador.value = null;
  }
}
