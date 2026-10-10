const _meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

/// "05 Ago 2026" (como no Ecrã 7 do protótipo).
String formatarData(DateTime d) => '${d.day.toString().padLeft(2, '0')} ${_meses[d.month - 1]} ${d.year}';

/// "05 Ago 2026, 14:03".
String formatarDataHora(DateTime d) =>
    '${formatarData(d)}, ${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';

String formatarMb(int bytes) => '${(bytes / 1048576).toStringAsFixed(1)} MB';
