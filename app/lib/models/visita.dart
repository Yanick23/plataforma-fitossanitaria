/// Estado de um pedido de visita técnica (igual à API).
enum EstadoVisita {
  pendente('PENDENTE', 'À espera do técnico'),
  agendada('AGENDADA', 'Visita agendada'),
  resolvida('RESOLVIDA', 'Visita feita'),
  cancelada('CANCELADA', 'Cancelada');

  const EstadoVisita(this.valor, this.nome);
  final String valor;
  final String nome;

  static EstadoVisita deTexto(String t) => values.firstWhere((e) => e.valor == t, orElse: () => pendente);
}

/// Pedido de visita feito a partir de um diagnóstico.
class Visita {
  const Visita({
    required this.id,
    required this.diagnosticoId,
    required this.estado,
    required this.criadoEm,
    this.mensagem,
    this.dataAgendada,
    this.notasTecnico,
    this.tecnicoNome,
  });

  final int id;
  final String diagnosticoId;
  final EstadoVisita estado;
  final DateTime criadoEm;
  final String? mensagem;
  final DateTime? dataAgendada;
  final String? notasTecnico;
  final String? tecnicoNome;

  bool get activa => estado == EstadoVisita.pendente || estado == EstadoVisita.agendada;

  factory Visita.fromJson(Map<String, dynamic> j) => Visita(
        id: j['id'] as int,
        diagnosticoId: j['diagnostico_id'] as String,
        estado: EstadoVisita.deTexto(j['estado'] as String),
        criadoEm: DateTime.parse(j['criado_em'] as String).toLocal(),
        mensagem: j['mensagem'] as String?,
        dataAgendada: j['data_agendada'] == null ? null : DateTime.parse(j['data_agendada'] as String).toLocal(),
        notasTecnico: j['notas_tecnico'] as String?,
        tecnicoNome: j['tecnico_nome'] as String?,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'diagnostico_id': diagnosticoId,
        'estado': estado.valor,
        'criado_em': criadoEm.toUtc().toIso8601String(),
        'mensagem': mensagem,
        'data_agendada': dataAgendada?.toUtc().toIso8601String(),
        'notas_tecnico': notasTecnico,
        'tecnico_nome': tecnicoNome,
      };
}
