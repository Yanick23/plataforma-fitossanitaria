import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/widgets.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:workmanager/workmanager.dart';

import 'api_cliente.dart';
import 'sessao.dart';

/// Notificações sem Firebase (funcionalidade 13b): a app consulta GET /novidades em segundo
/// plano e mostra notificações locais.
///
/// Limites do Android que ficam escritos: a tarefa periódica corre no mínimo de 15 em 15 minutos
/// e o sistema pode atrasá-la para poupar bateria; desde o Android 13 o agricultor tem de autorizar
/// as notificações; se a app for forçada a parar nas definições, a tarefa pára até a abrir de novo.
const tarefaNovidades = 'agro-novidades';
const _ficheiroEstado = 'novidades.json';

typedef NotificacaoLocal = ({int id, String titulo, String corpo});

String _dia(String iso) {
  final d = DateTime.parse(iso);
  return '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}';
}

/// Textos das notificações a partir da resposta de /novidades. Os ids separam os tipos, para uma
/// notificação nova do mesmo alerta substituir a anterior em vez de se acumular.
List<NotificacaoLocal> notificacoesDe(Map<String, dynamic> n) {
  final lista = <NotificacaoLocal>[];
  for (final a in (n['alertas'] as List? ?? []).cast<Map<String, dynamic>>()) {
    final urgente = a['nivel'] == 'URGENTE';
    lista.add((
      id: 100000 + (a['id'] as int),
      titulo: '${urgente ? 'Alerta urgente' : 'Alerta'}: ${a['titulo']}',
      corpo: 'Aviso do técnico para a sua zona. Toque para ler.',
    ));
  }
  final validacoes = (n['validacoes'] as List? ?? []).cast<Map<String, dynamic>>();
  if (validacoes.isNotEmpty) {
    final corrigidos = validacoes.where((v) => v['correcto'] != true).length;
    lista.add((
      id: 200000,
      titulo: validacoes.length == 1
          ? 'O técnico reviu o seu diagnóstico'
          : 'O técnico reviu ${validacoes.length} diagnósticos',
      corpo: corrigidos == 0
          ? 'Confirmado. Veja a nota no historial.'
          : '$corrigidos corrigido(s) pelo técnico. Veja o historial.',
    ));
  }
  for (final v in (n['visitas'] as List? ?? []).cast<Map<String, dynamic>>()) {
    final agendada = v['estado'] == 'AGENDADA';
    final data = v['data_agendada'] as String?;
    lista.add((
      id: 300000 + (v['id'] as int),
      titulo: agendada ? 'Visita técnica agendada' : 'Visita técnica resolvida',
      corpo: agendada
          ? (data != null ? 'O técnico marcou a visita para ${_dia(data)}.' : 'O técnico marcou a visita.')
          : 'O técnico deu a visita por resolvida. Veja as notas na app.',
    ));
  }
  for (final c in (n['campanhas'] as List? ?? []).cast<Map<String, dynamic>>()) {
    lista.add((
      id: 400000 + (c['id'] as int),
      titulo: 'Campanha na sua zona: ${c['titulo']}',
      corpo: 'Até ${_dia(c['fim'] as String)}. Fotografe as plantas, mesmo saudáveis, e sincronize.',
    ));
  }
  return lista;
}

class NotificacoesFundo {
  NotificacoesFundo._();

  static final _plugin = FlutterLocalNotificationsPlugin();
  static Timer? _temporizadorPolling;

  static const _detalhes = NotificationDetails(
    android: AndroidNotificationDetails(
      'novidades',
      'Novidades da zona',
      channelDescription: 'Alertas, validações do técnico, visitas e campanhas',
      importance: Importance.max,
      priority: Priority.high,
      playSound: true,
      enableVibration: true,
    ),
  );

  static Future<void> _iniciarPlugin() => _plugin.initialize(
    settings: const InitializationSettings(android: AndroidInitializationSettings('@mipmap/ic_launcher')),
  );

  /// Inicia polling periódico activo (15 segundos) enquanto a app estiver a correr.
  static void iniciarPolling({Duration intervalo = const Duration(seconds: 15)}) {
    _temporizadorPolling?.cancel();
    // Consulta inicial após 2 segundos
    Future.delayed(const Duration(seconds: 2), () async {
      try {
        await consultar(notificar: true);
      } catch (e) {
        debugPrint('Consulta inicial de novidades: $e');
      }
    });

    _temporizadorPolling = Timer.periodic(intervalo, (_) async {
      try {
        await consultar(notificar: true);
      } catch (e) {
        debugPrint('Polling de novidades: $e');
      }
    });
  }

  static void pararPolling() {
    _temporizadorPolling?.cancel();
    _temporizadorPolling = null;
  }

  /// No arranque da app: pede autorização (Android 13+), activa polling rápido e regista Workmanager.
  static Future<void> iniciar() async {
    await _iniciarPlugin();
    iniciarPolling();

    if (!Platform.isAndroid) return;
    try {
      await _plugin
          .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
          ?.requestNotificationsPermission();
      await Workmanager().initialize(despachante);
      await Workmanager().registerPeriodicTask(
        tarefaNovidades,
        tarefaNovidades,
        frequency: const Duration(minutes: 15),
        constraints: Constraints(networkType: NetworkType.connected),
        existingWorkPolicy: ExistingPeriodicWorkPolicy.keep,
      );
    } catch (e) {
      debugPrint('Notificações em segundo plano indisponíveis: $e');
    }
  }

  static Future<File> _estado() async => File(p.join((await getApplicationDocumentsDirectory()).path, _ficheiroEstado));

  static Future<String?> _lerDesde() async {
    final f = await _estado();
    if (!await f.exists()) return null;
    try {
      return (jsonDecode(await f.readAsString()) as Map<String, dynamic>)['desde'] as String?;
    } catch (_) {
      return null;
    }
  }

  static Future<void> _gravarDesde(String agora) async => (await _estado()).writeAsString(jsonEncode({'desde': agora}));

  /// Consulta as novidades. [notificar] = false na sincronização com a app aberta: o agricultor
  /// já vê tudo no ecrã, por isso só se avança o ponto de partida (não há notificações repetidas).
  static Future<int> consultar({bool notificar = true}) async {
    if (Sessao.instancia.token == null) return 0;
    final desde = await _lerDesde();
    final n = await ApiCliente.instancia.novidades(desde);
    var mostradas = 0;
    if (notificar && desde != null) {
      for (final x in notificacoesDe(n)) {
        await _plugin.show(id: x.id, title: x.titulo, body: x.corpo, notificationDetails: _detalhes);
        mostradas++;
      }
    }
    await _gravarDesde(n['agora'] as String);
    return mostradas;
  }

  /// Ao terminar a sessão: pára o polling, a tarefa e esquece o ponto de partida (as novidades são da conta).
  static Future<void> parar() async {
    pararPolling();
    if (!Platform.isAndroid) return;
    try {
      await Workmanager().cancelByUniqueName(tarefaNovidades);
    } catch (_) {}
    final f = await _estado();
    if (await f.exists()) await f.delete();
  }
}

/// Ponto de entrada da tarefa em segundo plano (corre num isolate próprio, sem a interface).
@pragma('vm:entry-point')
void despachante() {
  Workmanager().executeTask((tarefa, _) async {
    try {
      await Sessao.instancia.carregar();
      await NotificacoesFundo._iniciarPlugin();
      await NotificacoesFundo.consultar();
    } catch (e) {
      debugPrint('Consulta de novidades falhou: $e'); // sem rede ou servidor em baixo: tenta na próxima
    }
    return true;
  });
}
