import 'package:agrodiagnostico/models/utilizador.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> conta(String perfil) =>
    {'id': 7, 'nome': 'Helena', 'telefone': '841000001', 'perfil': perfil, 'area': 'Boane'};

void main() {
  test('todos os perfis da API são lidos (coordenador e investigador incluídos)', () {
    for (final (texto, perfil) in [
      ('AGRICULTOR', Perfil.agricultor),
      ('TECNICO', Perfil.tecnico),
      ('COORDENADOR', Perfil.coordenador),
      ('INVESTIGADOR', Perfil.investigador),
      ('ADMINISTRADOR', Perfil.administrador),
    ]) {
      expect(Utilizador.fromJson(conta(texto)).perfil, perfil);
    }
  });

  test('um perfil desconhecido não impede a entrada', () {
    final u = Utilizador.fromJson(conta('PERFIL_FUTURO'));
    expect(u.perfil, Perfil.outro);
    expect(u.nome, 'Helena');
  });

  test('a conta guardada volta igual (toJson / fromJson)', () {
    final u = Utilizador.fromJson(conta('COORDENADOR'));
    expect(Utilizador.fromJson(u.toJson()).perfil, Perfil.coordenador);
  });
}
