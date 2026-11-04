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

// --- Qualidade da fotografia (entrega 2c) --------------------------------------------------

/// Limiares medidos em 29 fotografias reais do SOTEN R80 e em cópias desfocadas/escurecidas
/// (docs/entrega_tese/03_resultados_plataforma.md, entrega 2c):
/// nitidez das fotos boas ≥ 23 (mediana 135); desfocadas (raio 3 px) ≤ 8,4;
/// brilho das fotos boas 84–189; escurecidas ≤ 47; sobreexpostas até 247.
const double limiarNitidez = 12;
const double limiarEscura = 55;
const double limiarClara = 220;

enum ProblemaFoto { desfocada, escura, clara }

class QualidadeFoto {
  const QualidadeFoto(this.nitidez, this.brilho);

  /// Variância do Laplaciano da luminância, com a foto reduzida a 256 px de largura.
  final double nitidez;

  /// Média da luminância (0–255).
  final double brilho;

  List<ProblemaFoto> get problemas => [
        if (nitidez < limiarNitidez) ProblemaFoto.desfocada,
        if (brilho < limiarEscura) ProblemaFoto.escura,
        if (brilho > limiarClara) ProblemaFoto.clara,
      ];

  bool get boa => problemas.isEmpty;
}

/// Mede a nitidez e o brilho da fotografia. Função de topo para correr com Isolate.run.
QualidadeFoto avaliarQualidade(String caminho) {
  final original = img.decodeImage(File(caminho).readAsBytesSync());
  if (original == null) throw const FormatException('Não foi possível ler a imagem.');
  final orientada = img.bakeOrientation(original);
  final w = 256;
  final h = (orientada.height * w / orientada.width).round().clamp(1, 4096).toInt();
  final pequena = img.copyResize(orientada, width: w, height: h, interpolation: img.Interpolation.linear);

  final lum = Float64List(w * h);
  var soma = 0.0;
  for (var y = 0; y < h; y++) {
    for (var x = 0; x < w; x++) {
      final p = pequena.getPixel(x, y);
      final l = 0.299 * p.r + 0.587 * p.g + 0.114 * p.b; // Rec. 601, como no PIL
      lum[y * w + x] = l;
      soma += l;
    }
  }
  // Laplaciano de 4 vizinhos no interior da imagem; variância pelo método de duas somas.
  var n = 0, s = 0.0, s2 = 0.0;
  for (var y = 1; y < h - 1; y++) {
    for (var x = 1; x < w - 1; x++) {
      final i = y * w + x;
      final v = lum[i - w] + lum[i + w] + lum[i - 1] + lum[i + 1] - 4 * lum[i];
      s += v;
      s2 += v * v;
      n++;
    }
  }
  final media = n == 0 ? 0.0 : s / n;
  return QualidadeFoto(n == 0 ? 0 : s2 / n - media * media, soma / (w * h));
}
