import { Megaphone, Siren, TriangleAlert } from 'lucide-react'
import { numero } from '@/nucleo/formatos'
import { NIVEL } from '@/nucleo/rotulos'
import { Botao, CabecalhoPagina, Campo, Cartao, Esqueleto, Etiqueta, Segmentos, Seleccao, Vazio } from '@/ui/componentes'
import { BarrasHorizontais, MapaDistritos } from '@/ui/graficos'
import { useCatalogo } from '@/viewmodels/referencias'
import { useVigilanciaViewModel, type Sensibilidade } from '@/viewmodels/useVigilanciaViewModel'

export function VigilanciaView() {
  const vm = useVigilanciaViewModel()
  const catalogo = useCatalogo()

  return (
    <>
      <CabecalhoPagina
        titulo="Vigilância"
        descricao="Onde estão as pragas e doenças, e onde estão a subir acima do habitual. Um sinal de surto é uma sugestão: o técnico decide se envia alerta."
      />
      <Cartao
        titulo="Sinais de surto"
        subtitulo={`Casos nos últimos ${vm.janela} dias comparados com a média das 4 semanas anteriores (mínimo ${vm.parametros.min_casos} casos, subida de ${String(vm.parametros.factor).replace('.', ',')}×)`}
        accoes={
          <div className="accoes">
            <Segmentos rotulo="Janela" valor={vm.janela} aoMudar={vm.setJanela} opcoes={[{ valor: 7, nome: '7 dias' }, { valor: 14, nome: '14 dias' }]} />
            <Segmentos rotulo="Sensibilidade" valor={vm.sensibilidade} aoMudar={(v: Sensibilidade) => vm.setSensibilidade(v)}
              opcoes={[{ valor: 'alta', nome: 'Sensível' }, { valor: 'normal', nome: 'Normal' }, { valor: 'baixa', nome: 'Conservador' }]} />
          </div>
        }
        semMargem
      >
        {vm.aCarregarSurtos ? <div style={{ padding: 20 }}><Esqueleto altura={120} /></div>
          : vm.surtos.length === 0 ? <Vazio titulo="Nenhum sinal de surto" texto="Nenhuma praga ou doença subiu acima do habitual com estes parâmetros." icone={<Siren size={28} />} /> : (
            <table className="tabela">
              <thead><tr><th>Praga ou doença</th><th>Distrito</th><th className="numero">Casos recentes</th><th className="numero">Média habitual</th><th className="numero">Subida</th><th>Nível</th><th /></tr></thead>
              <tbody>
                {vm.surtos.map((s) => (
                  <tr key={`${s.distrito_id}-${s.cultura_id}-${s.classe}`}>
                    <td className="celula-principal"><strong>{s.patologia_nome}</strong><span>{catalogo.nomeCultura(s.cultura_id)}</span></td>
                    <td>{s.distrito}</td>
                    <td className="numero">{numero(s.casos_recentes)}</td>
                    <td className="numero">{numero(s.media_anterior)}</td>
                    <td className="numero">{s.razao === null ? <span className="suave">sem histórico</span> : `${String(s.razao).replace('.', ',')}×`}</td>
                    <td><Etiqueta tom={NIVEL[s.nivel].tom} icone={<TriangleAlert size={12} />}>{NIVEL[s.nivel].nome}</Etiqueta></td>
                    <td style={{ width: 1 }}><Botao pequeno onClick={() => vm.criarAlerta(s)}><Megaphone size={14} />Criar alerta</Botao></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
      </Cartao>

      <div className="filtros">
        <Campo rotulo="Cultura">
          <Seleccao vazio="Todas" value={vm.cultura} onChange={(e) => vm.setCultura(e.target.value)} opcoes={catalogo.culturas.map((c) => ({ valor: c.id, nome: c.nome }))} />
        </Campo>
        <Campo rotulo="Praga ou doença">
          <Seleccao vazio="Todas" value={vm.classe} disabled={!vm.cultura} onChange={(e) => vm.setClasse(e.target.value)}
            opcoes={catalogo.patologiasDe(vm.cultura).map((p) => ({ valor: p.codigo, nome: p.nome_local }))} />
        </Campo>
        <Campo rotulo="Período">
          <Seleccao value={String(vm.periodo)} onChange={(e) => vm.setPeriodo(Number(e.target.value))}
            opcoes={[{ valor: '7', nome: 'Últimos 7 dias' }, { valor: '30', nome: 'Últimos 30 dias' }, { valor: '90', nome: 'Últimos 90 dias' }, { valor: '365', nome: 'Último ano' }]} />
        </Campo>
      </div>
      <div className="grelha grelha-principal">
        <Cartao titulo="Mapa de ocorrências" subtitulo={`${numero(vm.totalOcorrencias)} diagnósticos com estes filtros`}>
          {vm.aCarregarMapa ? <Esqueleto altura={460} /> : <MapaDistritos valores={vm.mapa} rotuloValor="Diagnósticos" />}
        </Cartao>
        <Cartao titulo="Distritos com mais casos">
          {vm.ranking.length ? <BarrasHorizontais itens={vm.ranking} /> : <Vazio titulo="Sem ocorrências" />}
        </Cartao>
      </div>
    </>
  )
}
