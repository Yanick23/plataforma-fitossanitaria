/// Calendário agrícola da província do agricultor (funcionalidade 10), vindo da API
/// (GET /calendario) e guardado no telemóvel para se ler sem rede.
class AvisoCalendario {
  const AvisoCalendario({
    required this.culturaId,
    required this.texto,
    required this.confianca,
    required this.fontes,
    this.classe,
    this.patologiaNome,
  });

  final String culturaId;
  final String? classe;
  final String? patologiaNome;
  final String texto;
  final String confianca; // alta | media
  final List<String> fontes;

  factory AvisoCalendario.fromJson(Map<String, dynamic> j) => AvisoCalendario(
    culturaId: j['cultura_id'] as String,
    classe: j['classe'] as String?,
    patologiaNome: j['patologia_nome'] as String?,
    texto: j['texto'] as String,
    confianca: j['confianca'] as String,
    fontes: (j['fontes'] as List).cast<String>(),
  );

  Map<String, dynamic> toJson() => {
    'cultura_id': culturaId,
    'classe': classe,
    'patologia_nome': patologiaNome,
    'texto': texto,
    'confianca': confianca,
    'fontes': fontes,
  };
}

class MesCalendario {
  const MesCalendario(this.mes, this.actividades, this.avisos);
  final int mes; // 1 a 12
  final List<String> actividades;
  final List<AvisoCalendario> avisos;
}

class Calendario {
  const Calendario({
    required this.provinciaCodigo,
    required this.provincia,
    required this.regiao,
    required this.meses,
    required this.fontes,
    required this.aviso,
    this.sementeira,
  });

  final String provinciaCodigo;
  final String provincia;
  final String regiao;
  final String? sementeira;
  final List<MesCalendario> meses;
  final Map<String, String> fontes; // id -> referência
  final String aviso;

  static const nomesMeses = [
    'Janeiro',
    'Fevereiro',
    'Março',
    'Abril',
    'Maio',
    'Junho',
    'Julho',
    'Agosto',
    'Setembro',
    'Outubro',
    'Novembro',
    'Dezembro',
  ];

  /// O mês pedido (1 a 12); um calendário incompleto devolve um mês vazio.
  MesCalendario mes(int m) => meses.firstWhere((x) => x.mes == m, orElse: () => MesCalendario(m, const [], const []));

  factory Calendario.fromJson(Map<String, dynamic> j) => Calendario(
    provinciaCodigo: j['provincia_codigo'] as String,
    provincia: j['provincia'] as String,
    regiao: j['regiao'] as String,
    sementeira: j['sementeira'] as String?,
    aviso: j['aviso'] as String,
    meses: [
      for (final m in (j['meses'] as List).cast<Map<String, dynamic>>())
        MesCalendario(m['mes'] as int, (m['actividades'] as List).cast<String>(), [
          for (final a in (m['avisos'] as List).cast<Map<String, dynamic>>()) AvisoCalendario.fromJson(a),
        ]),
    ],
    fontes: {
      for (final f in (j['fontes'] as List).cast<Map<String, dynamic>>()) f['id'] as String: f['referencia'] as String,
    },
  );

  Map<String, dynamic> toJson() => {
    'provincia_codigo': provinciaCodigo,
    'provincia': provincia,
    'regiao': regiao,
    'sementeira': sementeira,
    'aviso': aviso,
    'meses': [
      for (final m in meses)
        {
          'mes': m.mes,
          'actividades': m.actividades,
          'avisos': [for (final a in m.avisos) a.toJson()],
        },
    ],
    'fontes': [
      for (final e in fontes.entries) {'id': e.key, 'referencia': e.value},
    ],
  };
}
