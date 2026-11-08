"""Línguas em que a equipa pode gravar áudio (funcionalidade 14).

Códigos ISO 639-3. As províncias indicam onde cada língua é mais falada, para o painel sugerir
o que gravar primeiro; não limitam nada (um agricultor escolhe a língua que quiser).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Lingua:
    codigo: str
    nome: str
    provincias: tuple[str, ...]


LINGUAS: tuple[Lingua, ...] = (
    Lingua("por", "Português", ()),
    Lingua("vmw", "Emakhuwa", ("MZ-N", "MZ-P", "MZ-A", "MZ-Q")),
    Lingua("tso", "Xichangana", ("MZ-G", "MZ-L", "MZ-MPM")),
    Lingua("ngl", "Elomwe", ("MZ-Q", "MZ-A")),
    Lingua("seh", "Cisena", ("MZ-S", "MZ-T", "MZ-B", "MZ-Q")),
    Lingua("chw", "Echuwabo", ("MZ-Q",)),
    Lingua("ndc", "Cindau", ("MZ-B", "MZ-S")),
    Lingua("nya", "Cinyanja", ("MZ-T", "MZ-A")),
    Lingua("nyu", "Cinyungwe", ("MZ-T",)),
    Lingua("tsc", "Citshwa", ("MZ-I", "MZ-G")),
    Lingua("rng", "Xirhonga", ("MZ-L", "MZ-MPM")),
    Lingua("toh", "Gitonga", ("MZ-I",)),
    Lingua("kde", "Shimakonde", ("MZ-P",)),
    Lingua("yao", "Ciyao", ("MZ-A",)),
)

CODIGOS = {lingua.codigo for lingua in LINGUAS}
NOMES = {lingua.codigo: lingua.nome for lingua in LINGUAS}
