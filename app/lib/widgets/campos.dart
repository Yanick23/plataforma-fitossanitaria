import 'package:flutter/material.dart';

import '../tema.dart';

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
  });

  final TextEditingController controlador;
  final String rotulo;
  final IconData? icone;
  final TextInputType? teclado;
  final bool oculto;
  final String? Function(String?)? validar;
  final String? dica;
  final TextInputAction accao;

  @override
  Widget build(BuildContext context) {
    final borda = OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide.none);
    return TextFormField(
      controller: controlador,
      keyboardType: teclado,
      obscureText: oculto,
      validator: validar,
      textInputAction: accao,
      decoration: InputDecoration(
        labelText: rotulo,
        helperText: dica,
        prefixIcon: icone == null ? null : Icon(icone, color: Cores.textoSecundario),
        filled: true,
        fillColor: Cores.cartao,
        border: borda,
        enabledBorder: borda,
        focusedBorder: borda.copyWith(borderSide: const BorderSide(color: Cores.verde, width: 2)),
      ),
    );
  }
}

String? validarTelefone(String? v) =>
    RegExp(r'^\+?\d{9,15}$').hasMatch((v ?? '').replaceAll(' ', '')) ? null : 'Número de telefone inválido';

String? validarPalavraPasse(String? v) =>
    (v ?? '').length >= 6 ? null : 'Use pelo menos 6 caracteres';
