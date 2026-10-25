import 'dart:io';

import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:sqflite/sqflite.dart';

import '../models/diagnostico.dart';

/// Historial local em SQLite (RF08). Funciona sem rede; cada registo fica
/// PENDENTE até a API confirmar a recepção (RF09).
class HistorialDb {
  HistorialDb._();
  static final instancia = HistorialDb._();

  Database? _db;

  // Versão 2: colunas da validação pelo técnico.
  static const _colunasValidacao = [
    "validacao TEXT NOT NULL DEFAULT 'PENDENTE'",
    'classe_confirmada TEXT',
    'nota_tecnico TEXT',
  ];

  Future<Database> get _base async => _db ??= await openDatabase(
        p.join(await getDatabasesPath(), 'agrodiagnostico.db'),
        version: 2,
        onUpgrade: (db, antiga, nova) async {
          if (antiga < 2) {
            for (final coluna in _colunasValidacao) {
              await db.execute('ALTER TABLE diagnosticos ADD COLUMN $coluna');
            }
          }
        },
        onCreate: (db, version) => db.execute('''
          CREATE TABLE diagnosticos (
            id TEXT PRIMARY KEY,               -- UUID gerado no telemóvel
            utilizador_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            cultura TEXT NOT NULL,
            classe_prevista TEXT NOT NULL,
            confianca REAL NOT NULL,
            caminho_imagem TEXT NOT NULL,
            data_captura TEXT NOT NULL,
            versao_modelo INTEGER NOT NULL,
            tempo_inferencia_ms INTEGER NOT NULL,
            tempo_total_ms INTEGER NOT NULL,
            estado_sinc TEXT NOT NULL DEFAULT '${EstadoSinc.pendente.valor}',
            imagem_enviada INTEGER NOT NULL DEFAULT 0,
            ${_colunasValidacao.join(',\n            ')}
          )
        '''),
      );

  /// Copia a fotografia para a pasta da app (o image_picker devolve ficheiros
  /// temporários que o Android pode apagar) e devolve o novo caminho.
  Future<String> guardarImagem(String origem, String id) async {
    final pasta = Directory(p.join((await getApplicationDocumentsDirectory()).path, 'imagens'));
    await pasta.create(recursive: true);
    final destino = p.join(pasta.path, '$id${p.extension(origem).toLowerCase()}');
    await File(origem).copy(destino);
    return destino;
  }

  Future<void> inserir(Diagnostico d) async =>
      (await _base).insert('diagnosticos', d.toMap(), conflictAlgorithm: ConflictAlgorithm.ignore);

  Future<List<Diagnostico>> listar(int utilizadorId) async {
    final linhas = await (await _base)
        .query('diagnosticos', where: 'utilizador_id = ?', whereArgs: [utilizadorId], orderBy: 'data DESC');
    return linhas.map(Diagnostico.fromMap).toList();
  }

  Future<List<Diagnostico>> pendentes(int utilizadorId) async {
    final linhas = await (await _base).query('diagnosticos',
        where: 'utilizador_id = ? AND estado_sinc = ?',
        whereArgs: [utilizadorId, EstadoSinc.pendente.valor],
        orderBy: 'data');
    return linhas.map(Diagnostico.fromMap).toList();
  }

  Future<int> contarPendentes(int utilizadorId) async => Sqflite.firstIntValue(await (await _base).rawQuery(
        'SELECT COUNT(*) FROM diagnosticos WHERE utilizador_id = ? AND estado_sinc = ?',
        [utilizadorId, EstadoSinc.pendente.valor],
      )) ??
      0;

  Future<void> marcarImagemEnviada(String id) async =>
      (await _base).update('diagnosticos', {'imagem_enviada': 1}, where: 'id = ?', whereArgs: [id]);

  Future<void> marcarSincronizado(String id) async => (await _base).update(
      'diagnosticos', {'estado_sinc': EstadoSinc.sincronizado.valor},
      where: 'id = ?', whereArgs: [id]);

  /// Guarda a validação do técnico; devolve true se mudou alguma coisa.
  Future<bool> actualizarValidacao(String id, Validacao validacao, String? classe, String? nota) async {
    final n = await (await _base).update(
      'diagnosticos',
      {'validacao': validacao.valor, 'classe_confirmada': classe, 'nota_tecnico': nota},
      where: 'id = ? AND (validacao != ? OR IFNULL(classe_confirmada, \'\') != ? OR IFNULL(nota_tecnico, \'\') != ?)',
      whereArgs: [id, validacao.valor, classe ?? '', nota ?? ''],
    );
    return n > 0;
  }
}
