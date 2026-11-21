const _meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

/// "05 Ago 2026" (como no Ecrã 7 do protótipo).
String formatarData(DateTime d) => '${d.day.toString().padLeft(2, '0')} ${_meses[d.month - 1]} ${d.year}';

/// "05 Ago 2026, 14:03".
String formatarDataHora(DateTime d) =>
    '${formatarData(d)}, ${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';

String formatarMb(int bytes) => '${(bytes / 1048576).toStringAsFixed(1)} MB';

String _hora(DateTime d) => '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';

/// Data como se diz: «hoje, 09:30», «ontem, 18:05», «há 3 dias», «3 Nov», «3 Nov 2025».
String quando(DateTime d, {DateTime? agora}) {
  final hoje = agora ?? DateTime.now();
  final dias = DateTime(hoje.year, hoje.month, hoje.day).difference(DateTime(d.year, d.month, d.day)).inDays;
  if (dias == 0) return 'hoje, ${_hora(d)}';
  if (dias == 1) return 'ontem, ${_hora(d)}';
  if (dias > 1 && dias < 7) return 'há $dias dias';
  return d.year == hoje.year ? '${d.day} ${_meses[d.month - 1]}' : '${d.day} ${_meses[d.month - 1]} ${d.year}';
}

/// Data curta: «1 Dez» (este ano) ou «1 Dez 2027».
String dataCurta(DateTime d, {DateTime? agora}) {
  final ano = (agora ?? DateTime.now()).year;
  return d.year == ano ? '${d.day} ${_meses[d.month - 1]}' : '${d.day} ${_meses[d.month - 1]} ${d.year}';
}
