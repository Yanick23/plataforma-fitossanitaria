/// Nível de um alerta (igual à API).
enum NivelAlerta {
  informacao('INFORMACAO', 'Informação'),
  aviso('AVISO', 'Aviso'),
  urgente('URGENTE', 'Urgente');

  const NivelAlerta(this.valor, this.nome);
  final String valor;
  final String nome;

  static NivelAlerta deTexto(String t) => values.firstWhere((e) => e.valor == t, orElse: () => aviso);
}

/// Alerta enviado pelo técnico ou pelo administrador para a zona do agricultor.
class Alerta {
  const Alerta({
    required this.id,
    required this.titulo,
    required this.mensagem,
    required this.nivel,
    required this.zona,
    required this.criadoEm,
    this.culturaId,
    this.patologiaId,
    this.patologiaCodigo,
    this.expiraEm,
    this.lido = false,
  });

  final int id;
  final String titulo;
  final String mensagem;
  final NivelAlerta nivel;
  final String zona;
  final DateTime criadoEm;
  final String? culturaId;
  final int? patologiaId;
  final String? patologiaCodigo;
  final DateTime? expiraEm;
  final bool lido;

  bool get expirado => expiraEm != null && expiraEm!.isBefore(DateTime.now());

  Alerta comLido(bool valor) => Alerta(
        id: id, titulo: titulo, mensagem: mensagem, nivel: nivel, zona: zona, criadoEm: criadoEm,
        culturaId: culturaId, patologiaId: patologiaId, patologiaCodigo: patologiaCodigo, expiraEm: expiraEm, lido: valor,
      );

  factory Alerta.fromJson(Map<String, dynamic> j) => Alerta(
        id: j['id'] as int,
        titulo: j['titulo'] as String,
        mensagem: j['mensagem'] as String,
        nivel: NivelAlerta.deTexto(j['nivel'] as String),
        zona: j['zona'] as String? ?? '',
        criadoEm: DateTime.parse(j['criado_em'] as String).toLocal(),
        culturaId: j['cultura_id'] as String?,
        patologiaId: j['patologia_id'] as int?,
        patologiaCodigo: j['patologia_codigo'] as String?,
        expiraEm: j['expira_em'] == null ? null : DateTime.parse(j['expira_em'] as String).toLocal(),
        lido: j['lido'] as bool? ?? false,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'titulo': titulo,
        'mensagem': mensagem,
        'nivel': nivel.valor,
        'zona': zona,
        'criado_em': criadoEm.toUtc().toIso8601String(),
        'cultura_id': culturaId,
        'patologia_id': patologiaId,
        'patologia_codigo': patologiaCodigo,
        'expira_em': expiraEm?.toUtc().toIso8601String(),
        'lido': lido,
      };
}
