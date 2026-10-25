import 'dart:async';

import 'package:flutter/foundation.dart';

import '../models/cultura.dart';
import '../models/diagnostico.dart';
import 'alertas_locais.dart';
import 'api_cliente.dart';
import 'catalogo.dart';
import 'conectividade.dart';
import 'gestor_modelos.dart';
import 'historial_db.dart';
import 'registo_tecnico.dart';
import 'sessao.dart';
import 'visitas_locais.dart';

class ResumoSincronizacao {
  const ResumoSincronizacao({
    this.enviados = 0,
    this.rejeitados = 0,
    this.modelosActualizados = const [],
    this.alertasNovos = 0,
    this.validacoesNovas = 0,
    this.visitasActualizadas = 0,
    this.erro,
  });

  final int enviados;
  final int rejeitados;
  final List<Cultura> modelosActualizados;
  final int alertasNovos;
  final int validacoesNovas;
  final int visitasActualizadas;
  final String? erro;

  String get mensagem {
    if (erro != null) return erro!;
    final partes = <String>[
      if (enviados > 0) '$enviados diagnóstico(s) sincronizado(s)',
      if (rejeitados > 0) '$rejeitados rejeitado(s) pelo servidor',
      if (alertasNovos > 0) '$alertasNovos alerta(s) novo(s)',
      if (validacoesNovas > 0) '$validacoesNovas diagnóstico(s) revisto(s) pelo técnico',
      if (visitasActualizadas > 0) '$visitasActualizadas visita(s) actualizada(s)',
      for (final c in modelosActualizados) 'modelo de ${c.nome.toLowerCase()} actualizado',
    ];
    return partes.isEmpty ? 'Tudo sincronizado' : partes.join(' · ');
  }
}

/// Sincronização com a API (RF09, RF12, secção 4.4.4).
///
/// Ordem: renova o token → envia os PENDENTE em lote → envia as imagens dos
/// confirmados → só então marca SINCRONIZADO → actualiza o catálogo e os modelos.
/// Se a rede cair a meio, o que não foi confirmado fica PENDENTE e é reenviado
/// na próxima vez; a API ignora os UUID repetidos, por isso nada se duplica (RNF07).
class Sincronizacao extends ChangeNotifier {
  Sincronizacao._();
  static final instancia = Sincronizacao._();

  bool emCurso = false;
  ResumoSincronizacao? ultimo;
  StreamSubscription<bool>? _escuta;

  /// Sincroniza sempre que a rede volta.
  void iniciarAutomatica() {
    _escuta ??= Conectividade.instancia.alteracoes.listen((online) {
      if (online) sincronizar();
    });
  }

  Future<ResumoSincronizacao> sincronizar() async {
    final utilizador = Sessao.instancia.utilizador.value;
    if (emCurso || utilizador == null) return ultimo ?? const ResumoSincronizacao();
    if (!await Conectividade.instancia.online()) {
      return ultimo = const ResumoSincronizacao(erro: 'Sem rede: os diagnósticos ficam pendentes.');
    }
    emCurso = true;
    notifyListeners();
    var enviados = 0, rejeitados = 0;
    final modelos = <Cultura>[];
    try {
      // 1. Renovar o token (4.4.5). Se tiver expirado, é preciso novo login.
      try {
        await Sessao.instancia.renovarToken((await ApiCliente.instancia.renovarToken()).token);
      } on ErroApi catch (e) {
        if (e.naoAutorizado) {
          return ultimo = const ResumoSincronizacao(erro: 'A sessão expirou. Termine a sessão e entre de novo.');
        }
        rethrow;
      }

      // 2. Diagnósticos pendentes.
      final db = HistorialDb.instancia;
      final pendentes = await db.pendentes(utilizador.id);
      if (pendentes.isNotEmpty) {
        final resposta = await ApiCliente.instancia.enviarDiagnosticos(pendentes);
        rejeitados = resposta.rejeitados.length;
        for (final d in pendentes.where((d) => resposta.confirmados.contains(d.id))) {
          if (!d.imagemEnviada) {
            await ApiCliente.instancia.enviarImagem(d.id, d.imagem.caminhoFicheiro);
            await db.marcarImagemEnviada(d.id);
          }
          await db.marcarSincronizado(d.id); // só depois da confirmação da API
          enviados++;
        }
        if (rejeitados > 0) {
          RegistoTecnico.instancia.escrever('sincronização: ${resposta.rejeitados} rejeitados pela API');
        }
      }

      // 3. Catálogo actualizável a partir da API (RF06/RF07, RF11).
      await Catalogo.instancia.actualizar(await ApiCliente.instancia.patologias());

      // 4. Novas versões do modelo (RF12).
      for (final c in Cultura.values) {
        if (await GestorModelos.instancia.actualizar(c)) modelos.add(c);
      }

      // 5. Validação pelo técnico: «Confirmado» ou «Corrigido» no historial.
      var validacoes = 0;
      for (final v in await ApiCliente.instancia.validacoes()) {
        if (await db.actualizarValidacao(
            v.diagnosticoId, Validacao.deTexto(v.estado), v.classeConfirmada, v.nota)) {
          validacoes++;
        }
      }

      // 6. Alertas da zona: primeiro as leituras feitas sem rede, depois os activos.
      final alertas = AlertasLocais.instancia;
      for (final id in alertas.lidosPorEnviar) {
        await ApiCliente.instancia.marcarAlertaLido(id);
        await alertas.leituraConfirmada(id);
      }
      final alertasNovos = await alertas.actualizar(await ApiCliente.instancia.alertas());

      // 7. Pedidos de visita (estado, data agendada e notas do técnico).
      final visitas = await VisitasLocais.instancia.actualizar(await ApiCliente.instancia.visitas());

      return ultimo = ResumoSincronizacao(
        enviados: enviados,
        rejeitados: rejeitados,
        modelosActualizados: modelos,
        alertasNovos: alertasNovos,
        validacoesNovas: validacoes,
        visitasActualizadas: visitas,
      );
    } on ErroApi catch (e) {
      return ultimo = ResumoSincronizacao(enviados: enviados, erro: e.mensagem);
    } catch (e) {
      return ultimo = ResumoSincronizacao(enviados: enviados, erro: 'Erro na sincronização: $e');
    } finally {
      emCurso = false;
      notifyListeners();
    }
  }
}
