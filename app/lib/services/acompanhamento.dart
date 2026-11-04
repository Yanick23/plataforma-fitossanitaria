import 'package:flutter/foundation.dart';

import '../models/diagnostico.dart';
import '../models/patologia.dart';
import 'catalogo.dart';
import 'historial_db.dart';
import 'sessao.dart';

/// Seguimento do tratamento (entrega 2c): [diasSeguimento] dias depois de um diagnóstico de praga
/// ou doença, a app pergunta se o agricultor seguiu a recomendação e se a planta melhorou.
/// As respostas vão para a API na sincronização e alimentam a eficácia das recomendações no painel.
class Acompanhamento extends ChangeNotifier {
  Acompanhamento._();
  static final instancia = Acompanhamento._();

  List<Diagnostico> _porResponder = const [];
  final Set<String> _adiados = {}; // «Agora não»: só até a app fechar

  /// Diagnósticos à espera de resposta, o mais antigo primeiro.
  List<Diagnostico> get porResponder => _porResponder.where((d) => !_adiados.contains(d.id)).toList();

  /// Pode responder-se a este diagnóstico? (no detalhe, sem esperar pelos 7 dias)
  static bool elegivel(Diagnostico d) =>
      d.estadoSinc == EstadoSinc.sincronizado &&
      Catalogo.instancia.patologia(d.cultura, d.classeFinal).tipo != TipoPatologia.saudavel;

  static bool _naAltura(Diagnostico d, DateTime agora) {
    final dias = agora.difference(d.data).inDays;
    return dias >= diasSeguimento && dias <= diasSeguimentoMaximo;
  }

  Future<void> actualizar() async {
    final u = Sessao.instancia.utilizador.value;
    if (u == null) {
      _porResponder = const [];
    } else {
      final agora = DateTime.now();
      _porResponder = (await HistorialDb.instancia.listar(u.id))
          .where((d) => elegivel(d) && !d.seguimentoRespondido && _naAltura(d, agora))
          .toList()
        ..sort((a, b) => a.data.compareTo(b.data));
    }
    notifyListeners();
  }

  Future<void> responder(Diagnostico d, Seguiu seguiu, ResultadoTratamento resultado) async {
    await HistorialDb.instancia.responderSeguimento(d.id, seguiu, resultado);
    await actualizar();
  }

  void adiar(Diagnostico d) {
    _adiados.add(d.id);
    notifyListeners();
  }

  void limpar() {
    _porResponder = const [];
    _adiados.clear();
    notifyListeners();
  }
}
