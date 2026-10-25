import 'dart:io';

import 'package:agrodiagnostico/services/pre_processamento.dart';
import 'package:flutter_test/flutter_test.dart';

/// Fotografias reais do SOTEN R80 sincronizadas na API (não estão no Git; o teste salta se faltarem).
const _pasta = '../api/dados/imagens';

String? _foto(String prefixo) {
  final d = Directory(_pasta);
  if (!d.existsSync()) return null;
  for (final f in d.listSync()) {
    if (f.path.split(Platform.pathSeparator).last.startsWith(prefixo)) return f.path;
  }
  return null;
}

void main() {
  final semFotos = !Directory(_pasta).existsSync();

  test('fotografias desfocadas são assinaladas', () {
    for (final p in ['fd1a991f', '8ee7e039']) {
      final q = avaliarQualidade(_foto(p)!);
      expect(q.problemas, contains(ProblemaFoto.desfocada), reason: '$p: nitidez ${q.nitidez}');
    }
  }, skip: semFotos);

  test('fotografias boas (incluindo uma suave mas utilizável) passam', () {
    for (final p in ['1ec39bad', '6f630124', '35b33bc1', '59100980', '157da319']) {
      final q = avaliarQualidade(_foto(p)!);
      expect(q.boa, isTrue, reason: '$p: nitidez ${q.nitidez.toStringAsFixed(1)}, brilho ${q.brilho.toStringAsFixed(1)}');
    }
  }, skip: semFotos);

  test('valores próximos dos da calibração em Python', () {
    final q = avaliarQualidade(_foto('1ec39bad')!); // Python: nitidez 323,1; brilho 106,2
    expect(q.brilho, closeTo(106.2, 3));
    expect(q.nitidez, greaterThan(150));
  }, skip: semFotos);
}
