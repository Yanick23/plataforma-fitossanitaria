/// Campanha de vigilância activa da zona do agricultor (funcionalidade 12): o técnico pede que
/// fotografe uma cultura durante alguns dias, mesmo que as plantas pareçam saudáveis.
class Campanha {
  const Campanha({
    required this.id,
    required this.titulo,
    required this.mensagem,
    required this.culturaId,
    required this.zona,
    required this.inicio,
    required this.fim,
    this.patologiaCodigo,
    this.respondeu = false,
  });

  final int id;
  final String titulo;
  final String mensagem;
  final String culturaId;
  final String zona;
  final DateTime inicio;
  final DateTime fim; // último dia (inclusive)
  final String? patologiaCodigo;

  /// Já enviou um diagnóstico desta cultura durante a campanha (segundo a API).
  final bool respondeu;

  /// A decorrer hoje (a lista guardada pode ter ficado antiga sem rede).
  bool decorre(DateTime agora) {
    final hoje = DateTime(agora.year, agora.month, agora.day);
    return !hoje.isBefore(inicio) && !hoje.isAfter(fim);
  }

  factory Campanha.fromJson(Map<String, dynamic> j) => Campanha(
    id: j['id'] as int,
    titulo: j['titulo'] as String,
    mensagem: j['mensagem'] as String,
    culturaId: j['cultura_id'] as String,
    zona: j['zona'] as String,
    inicio: DateTime.parse(j['inicio'] as String),
    fim: DateTime.parse(j['fim'] as String),
    patologiaCodigo: j['patologia_codigo'] as String?,
    respondeu: j['respondeu'] == true,
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'titulo': titulo,
    'mensagem': mensagem,
    'cultura_id': culturaId,
    'zona': zona,
    'inicio': _dia(inicio),
    'fim': _dia(fim),
    'patologia_codigo': patologiaCodigo,
    'respondeu': respondeu,
  };

  Campanha comRespondeu() => Campanha(
    id: id,
    titulo: titulo,
    mensagem: mensagem,
    culturaId: culturaId,
    zona: zona,
    inicio: inicio,
    fim: fim,
    patologiaCodigo: patologiaCodigo,
    respondeu: true,
  );

  static String _dia(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
}
