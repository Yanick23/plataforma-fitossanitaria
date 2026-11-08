enum Perfil {
  agricultor('AGRICULTOR', 'Agricultor'),
  tecnico('TECNICO', 'Técnico'),
  coordenador('COORDENADOR', 'Coordenador provincial'),
  investigador('INVESTIGADOR', 'Investigador'),
  administrador('ADMINISTRADOR', 'Administrador'),
  // Perfil que esta versão da app ainda não conhece (a API pode ganhar perfis novos):
  // a conta entra na mesma, em vez de a leitura falhar.
  outro('OUTRO', 'Outro perfil');

  const Perfil(this.valor, this.nome);
  final String valor;
  final String nome;

  static Perfil deTexto(String texto) =>
      values.firstWhere((p) => p.valor == texto, orElse: () => Perfil.outro);
}

/// Utilizador autenticado (RF10).
class Utilizador {
  const Utilizador({
    required this.id,
    required this.nome,
    required this.telefone,
    required this.perfil,
    this.area,
  });

  final int id;
  final String nome;
  final String telefone;
  final Perfil perfil;
  final String? area;

  factory Utilizador.fromJson(Map<String, dynamic> j) => Utilizador(
        id: j['id'] as int,
        nome: j['nome'] as String,
        telefone: j['telefone'] as String,
        perfil: Perfil.deTexto(j['perfil'] as String),
        area: j['area'] as String?,
      );

  Map<String, dynamic> toJson() =>
      {'id': id, 'nome': nome, 'telefone': telefone, 'perfil': perfil.valor, 'area': area};
}
