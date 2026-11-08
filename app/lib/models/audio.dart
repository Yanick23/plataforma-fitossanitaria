/// Línguas em que a equipa pode gravar (iguais a GET /linguas da API; ficam na app para o registo
/// funcionar sem rede). Códigos ISO 639-3.
class Lingua {
  const Lingua(this.codigo, this.nome);
  final String codigo;
  final String nome;

  static const portugues = Lingua('por', 'Português');

  static const todas = [
    portugues,
    Lingua('vmw', 'Emakhuwa'),
    Lingua('tso', 'Xichangana'),
    Lingua('ngl', 'Elomwe'),
    Lingua('seh', 'Cisena'),
    Lingua('chw', 'Echuwabo'),
    Lingua('ndc', 'Cindau'),
    Lingua('nya', 'Cinyanja'),
    Lingua('nyu', 'Cinyungwe'),
    Lingua('tsc', 'Citshwa'),
    Lingua('rng', 'Xirhonga'),
    Lingua('toh', 'Gitonga'),
    Lingua('kde', 'Shimakonde'),
    Lingua('yao', 'Ciyao'),
  ];

  static String nomeDe(String codigo) =>
      todas.firstWhere((l) => l.codigo == codigo, orElse: () => Lingua(codigo, codigo)).nome;
}

/// Gravação de voz (funcionalidade 14): a recomendação de uma praga ou a mensagem de um alerta,
/// lida por alguém da equipa numa língua local. A app descarrega-a e toca-a sem rede.
class AudioVoz {
  const AudioVoz({required this.id, required this.lingua, required this.url, this.duracaoS});

  final int id;
  final String lingua; // ISO 639-3
  final String url; // relativo à API; muda a cada gravação nova
  final double? duracaoS;

  String get nomeLingua => Lingua.nomeDe(lingua);

  /// Nome do ficheiro local: o último segmento do url, único por gravação.
  String get ficheiro => url.split('/').last;

  factory AudioVoz.fromJson(Map<String, dynamic> j) => AudioVoz(
        id: j['id'] as int,
        lingua: j['lingua'] as String,
        url: j['url'] as String,
        duracaoS: (j['duracao_s'] as num?)?.toDouble(),
      );

  Map<String, dynamic> toJson() => {'id': id, 'lingua': lingua, 'url': url, 'duracao_s': duracaoS};

  static List<AudioVoz> lista(Object? json) =>
      [for (final a in (json as List? ?? const [])) AudioVoz.fromJson(a as Map<String, dynamic>)];

  /// A gravação a tocar para quem escolheu [lingua]: a da língua dele; se não houver, a em português;
  /// se nenhuma das duas existir, nenhuma (a app mostra só o texto).
  static AudioVoz? escolher(List<AudioVoz> audios, String? lingua) {
    if (lingua == null) return null;
    for (final codigo in [lingua, Lingua.portugues.codigo]) {
      for (final a in audios) {
        if (a.lingua == codigo) return a;
      }
    }
    return null;
  }
}
