import 'package:connectivity_plus/connectivity_plus.dart';

/// Indica se o telemóvel tem ligação de rede (Wi-Fi ou dados móveis).
/// Serve só para informar o utilizador: o diagnóstico funciona sempre offline.
class Conectividade {
  Conectividade._();
  static final instancia = Conectividade._();

  final _connectivity = Connectivity();

  static bool _temRede(List<ConnectivityResult> r) =>
      r.any((e) => e != ConnectivityResult.none);

  Future<bool> online() async => _temRede(await _connectivity.checkConnectivity());

  Stream<bool> get alteracoes => _connectivity.onConnectivityChanged.map(_temRede);
}
