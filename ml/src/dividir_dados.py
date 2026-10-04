"""Divide data/metadados.csv em treino/validação/teste (70/15/15), por cultura.

Regras (secção 4.3.4 do relatório):
  - divisão independente por cultura e por fonte (CCMT, técnicos, campo):
    a estratificação usa a combinação fonte + classe, para que nenhuma
    classe de nenhuma fonte fique ausente de um dos três subconjuntos;
  - random_state fixo (config.RANDOM_STATE);
  - todas as fotos da mesma folha (id_folha) ficam no mesmo subconjunto.

Para cumprir as duas regras ao mesmo tempo, a divisão é feita sobre a lista
de folhas únicas (cada folha tem uma só classe) e só depois o subconjunto é
atribuído a todas as fotos de cada folha.

Gera um CSV por cultura em data/divisoes/, por exemplo divisao_milho.csv,
com as colunas de metadados.csv mais a coluna "subconjunto".

Utilização (a partir da raiz do repositório):
    python ml/src/dividir_dados.py            # não reescreve divisões existentes
    python ml/src/dividir_dados.py --forcar   # reescreve (altera as experiências!)
"""

import argparse
import sys

import pandas as pd
from sklearn.model_selection import train_test_split

import config


def dividir_folhas(folhas):
    """Recebe um DataFrame com uma linha por folha e devolve id_folha -> subconjunto."""
    # 1.º corte: 70% treino, 30% para validação + teste.
    treino, resto = train_test_split(
        folhas,
        test_size=config.PROPORCAO_VALIDACAO + config.PROPORCAO_TESTE,
        stratify=folhas["estrato"],
        random_state=config.RANDOM_STATE,
    )
    # 2.º corte: os 30% restantes divididos ao meio (15% + 15%).
    proporcao_teste_no_resto = config.PROPORCAO_TESTE / (
        config.PROPORCAO_VALIDACAO + config.PROPORCAO_TESTE
    )
    validacao, teste = train_test_split(
        resto,
        test_size=proporcao_teste_no_resto,
        stratify=resto["estrato"],
        random_state=config.RANDOM_STATE,
    )

    subconjuntos = {}
    for nome, parte in [("treino", treino), ("validacao", validacao), ("teste", teste)]:
        for id_folha in parte["id_folha"]:
            subconjuntos[id_folha] = nome
    return subconjuntos


def verificar_folhas(df, cultura):
    """Garante que nenhuma folha aparece com mais do que uma classe."""
    classes_por_folha = df.groupby("id_folha")["classe"].nunique()
    inconsistentes = classes_por_folha[classes_por_folha > 1]
    if not inconsistentes.empty:
        sys.exit(
            f"ERRO ({cultura}): folhas com mais do que uma classe:\n  "
            + "\n  ".join(inconsistentes.index)
        )

def remover_imagens_ilegiveis(df, cultura):
    """Exclui as fotos que o TensorFlow não consegue descodificar.

    Usa o mesmo método do pipeline de treino (tf.io.decode_image), para que
    nenhuma imagem incluída na divisão falhe depois no treino ou na avaliação.
    """
    import tensorflow as tf  # importado aqui: só é preciso nesta verificação

    def legivel(caminho):
        try:
            tf.io.decode_image(tf.io.read_file(str(config.PASTA_RAW / caminho)),
                               channels=3, expand_animations=False)
            return True
        except Exception:
            return False

    validas = df["caminho"].map(legivel)
    ilegiveis = df.loc[~validas, "caminho"]
    if not ilegiveis.empty:
        print(f"{cultura}: {len(ilegiveis)} imagens ilegíveis excluídas da divisão:")
        for caminho in ilegiveis:
            print("   ", caminho)
    return df[validas].copy()

def resumo(df):
    """Tabela com o número de imagens por classe e subconjunto."""
    tabela = pd.crosstab(df["classe"], df["subconjunto"], margins=True, margins_name="total")
    colunas = [c for c in ["treino", "validacao", "teste", "total"] if c in tabela.columns]
    return tabela[colunas]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--forcar", action="store_true",
                        help="reescreve as divisões já existentes")
    args = parser.parse_args()

    if not config.FICHEIRO_METADADOS.exists():
        sys.exit("ERRO: execute primeiro gerar_metadados.py.")

    metadados = pd.read_csv(config.FICHEIRO_METADADOS)
    config.PASTA_DIVISOES.mkdir(parents=True, exist_ok=True)

    for cultura in config.CLASSES:
        destino = config.PASTA_DIVISOES / f"divisao_{cultura}.csv"
        if destino.exists() and not args.forcar:
            print(f"{destino.name} já existe; mantido (use --forcar para reescrever).")
            continue

        df = metadados[metadados["cultura"] == cultura].copy()
        if df.empty:
            print(f"AVISO: sem imagens de {cultura}; divisão não gerada.")
            continue

        df = remover_imagens_ilegiveis(df, cultura)   # <- nova linha
        verificar_folhas(df, cultura)

        # Estrato = fonte + classe (ex.: "ccmt/mosaico", "campo/mosaico").
        folhas = df.drop_duplicates("id_folha")[["id_folha", "fonte", "classe"]].copy()
        folhas["estrato"] = folhas["fonte"] + "/" + folhas["classe"]
        subconjuntos = dividir_folhas(folhas)
        df["subconjunto"] = df["id_folha"].map(subconjuntos)

        # Verificação final: cada folha pertence a um único subconjunto.
        assert (df.groupby("id_folha")["subconjunto"].nunique() == 1).all()

        df.to_csv(destino, index=False)
        print(f"\n=== {cultura} -> {destino} ===")
        print(resumo(df).to_string())
        proporcoes = df["subconjunto"].value_counts(normalize=True).round(3)
        print("Proporções:", proporcoes.to_dict())


if __name__ == "__main__":
    main()
