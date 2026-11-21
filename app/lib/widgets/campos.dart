import 'package:flutter/material.dart';

/// Campo de texto branco e arredondado, no estilo do protótipo.
class CampoTexto extends StatelessWidget {
  const CampoTexto({
    super.key,
    required this.controlador,
    required this.rotulo,
    this.icone,
    this.teclado,
    this.oculto = false,
    this.validar,
    this.dica,
    this.accao = TextInputAction.next,
    this.exemplo,
  });

  final TextEditingController controlador;
  final String rotulo;
  final IconData? icone;
  final TextInputType? teclado;
  final bool oculto;
  final String? Function(String?)? validar;
  final String? dica;
  final TextInputAction accao;

  /// Texto de exemplo dentro do campo vazio.
  final String? exemplo;

  @override
  Widget build(BuildContext context) {
    // Rótulo por cima do campo (e não dentro): lê-se sempre, mesmo com o campo preenchido.
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(rotulo, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500)),
      const SizedBox(height: 8),
      TextFormField(
        controller: controlador,
        keyboardType: teclado,
        obscureText: oculto,
        validator: validar,
        textInputAction: accao,
        style: const TextStyle(fontSize: 16.5),
        decoration: InputDecoration(
          hintText: exemplo,
          helperText: dica,
          helperMaxLines: 2,
          prefixIcon: icone == null ? null : Padding(padding: const EdgeInsets.only(left: 12), child: Icon(icone)),
        ),
      ),
    ]);
  }
}

String? validarTelefone(String? v) =>
    RegExp(r'^\+?\d{9,15}$').hasMatch((v ?? '').replaceAll(' ', '')) ? null : 'Número de telefone inválido';

String? validarPalavraPasse(String? v) =>
    (v ?? '').length >= 6 ? null : 'Use pelo menos 6 caracteres';
