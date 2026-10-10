import 'dart:io';
import 'dart:typed_data';

import 'package:image/image.dart' as img;

/// Resolução de entrada do EfficientNetB0.
const int tamanhoEntrada = 224;

/// Lê a fotografia e devolve o tensor de entrada do modelo [1, 224, 224, 3]
/// como um Float32List contíguo (ordem: linha, coluna, canal RGB).
///
/// Tal como no treino (notebook 02_treino, secção 6):
///  - a imagem é esticada para 224×224 com interpolação bilinear
///    (tf.image.resize também não mantém a proporção);
///  - os píxeis ficam em 0–255, em float32. NÃO se divide por 255:
///    a normalização está dentro do modelo (camadas do EfficientNetB0).
///
/// É uma função de topo para poder correr noutro isolate (Isolate.run)
/// e não bloquear a interface enquanto descodifica a fotografia.
Float32List preprocessarImagem(String caminho) {
  final bytes = File(caminho).readAsBytesSync();
  final original = img.decodeImage(bytes);
  if (original == null) {
    throw const FormatException('Não foi possível ler a imagem.');
  }

  // Aplica a rotação EXIF, para o modelo ver a foto como o utilizador a vê.
  final orientada = img.bakeOrientation(original);
  final redimensionada = img.copyResize(
    orientada,
    width: tamanhoEntrada,
    height: tamanhoEntrada,
    interpolation: img.Interpolation.linear,
  );
  // Garante 3 canais de 8 bits (PNG com transparência ou 16 bits, por exemplo).
  final rgb = redimensionada.convert(format: img.Format.uint8, numChannels: 3);

  final entrada = Float32List(tamanhoEntrada * tamanhoEntrada * 3);
  var i = 0;
  for (var y = 0; y < tamanhoEntrada; y++) {
    for (var x = 0; x < tamanhoEntrada; x++) {
      final pixel = rgb.getPixel(x, y);
      entrada[i++] = pixel.r.toDouble();
      entrada[i++] = pixel.g.toDouble();
      entrada[i++] = pixel.b.toDouble();
    }
  }
  return entrada;
}
