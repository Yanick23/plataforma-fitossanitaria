/// Culturas suportadas (entidade Cultura do diagrama de classes).
/// Cada uma tem o seu próprio modelo TFLite (RF02).
enum Cultura {
  milho(
    id: 'milho',
    nome: 'Milho',
    nomeCientifico: 'Zea mays',
    modeloEmbutido: 'assets/models/modelo_milho_int8_dinamica.tflite',
    classesEmbutidas: 'assets/models/classes_milho.json',
  ),
  mandioca(
    id: 'mandioca',
    nome: 'Mandioca',
    nomeCientifico: 'Manihot esculenta',
    modeloEmbutido: 'assets/models/modelo_mandioca_int8_dinamica.tflite',
    classesEmbutidas: 'assets/models/classes_mandioca.json',
  );

  const Cultura({
    required this.id,
    required this.nome,
    required this.nomeCientifico,
    required this.modeloEmbutido,
    required this.classesEmbutidas,
  });

  final String id;
  final String nome;
  final String nomeCientifico;

  /// Modelo (versão 1) que vem dentro do APK; pode ser substituído por uma
  /// versão mais recente descarregada da API (RF12).
  final String modeloEmbutido;
  final String classesEmbutidas;

  static Cultura porId(String id) => values.firstWhere((c) => c.id == id);
}
