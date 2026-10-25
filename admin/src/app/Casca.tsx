import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  BellRing, Boxes, CalendarCheck, FileText, LayoutDashboard, ListChecks, LogOut, MapPin, Moon, Radar, ScanSearch, ScrollText, Sprout, Sun,
  SunMoon, Users,
} from 'lucide-react'
import { visitasRepo } from '@/model/repositorios'
import { useSessao } from '@/nucleo/sessao'
import { PERFIL } from '@/nucleo/rotulos'
import { Botao, Etiqueta } from '@/ui/componentes'
import { useRegioes } from '@/viewmodels/referencias'

type Tema = 'sistema' | 'claro' | 'escuro'

function useTema() {
  const [tema, setTema] = useState<Tema>(() => {
    try { return (localStorage.getItem('painel.tema') as Tema) || 'sistema' } catch { return 'sistema' }
  })
  useEffect(() => {
    const raiz = document.documentElement
    if (tema === 'sistema') raiz.removeAttribute('data-tema')
    else raiz.setAttribute('data-tema', tema)
    try { localStorage.setItem('painel.tema', tema) } catch { /* sem armazenamento */ }
  }, [tema])
  const seguinte = () => setTema((t) => (t === 'sistema' ? 'claro' : t === 'claro' ? 'escuro' : 'sistema'))
  return { tema, seguinte }
}

interface ItemNav { para: string; nome: string; icone: typeof LayoutDashboard; soAdmin?: boolean; contador?: 'visitas' }

const NAVEGACAO: { grupo: string; itens: ItemNav[] }[] = [
  {
    grupo: 'Visão geral', itens: [
      { para: '/', nome: 'Painel', icone: LayoutDashboard },
      { para: '/vigilancia', nome: 'Vigilância', icone: Radar },
      { para: '/boletim', nome: 'Boletim', icone: FileText },
    ],
  },
  {
    grupo: 'Operação', itens: [
      { para: '/diagnosticos', nome: 'Diagnósticos', icone: ScanSearch },
      { para: '/validacao', nome: 'Validação', icone: ListChecks },
      { para: '/alertas', nome: 'Alertas', icone: BellRing },
      { para: '/visitas', nome: 'Visitas', icone: CalendarCheck, contador: 'visitas' },
    ],
  },
  {
    grupo: 'Conhecimento', itens: [
      { para: '/catalogo', nome: 'Culturas e pragas', icone: Sprout },
      { para: '/modelos', nome: 'Modelos', icone: Boxes },
    ],
  },
  {
    grupo: 'Administração', itens: [
      { para: '/utilizadores', nome: 'Utilizadores', icone: Users },
      { para: '/auditoria', nome: 'Auditoria', icone: ScrollText, soAdmin: true },
    ],
  },
]

export function Casca() {
  const { utilizador, sair, eAdministrador } = useSessao()
  const regioes = useRegioes()
  const { tema, seguinte } = useTema()
  const pendentes = useQuery({ queryKey: ['visitas', 'PENDENTE'], queryFn: () => visitasRepo.listar('PENDENTE'), refetchInterval: 60_000 })
  const visitasPendentes = pendentes.data?.length ?? 0
  if (!utilizador) return null

  const distrito = regioes.distrito(utilizador.distrito_id)
  const zona = utilizador.perfil === 'ADMINISTRADOR'
    ? 'Moçambique — todas as províncias'
    : distrito
      ? `${distrito.nome}, ${regioes.nomeProvincia(distrito.provincia_codigo)}`
      : utilizador.provincia_codigo
        ? `Província de ${regioes.nomeProvincia(utilizador.provincia_codigo)}`
        : 'Sem zona atribuída'
  const IconeTema = tema === 'claro' ? Sun : tema === 'escuro' ? Moon : SunMoon

  return (
    <div className="casca">
      <aside className="lateral">
        <div className="marca">
          <img src="/marca.svg" alt="" />
          <div>
            <strong>Vigilância Fitossanitária</strong>
            <span>Milho e mandioca</span>
          </div>
        </div>
        <nav aria-label="Navegação principal" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {NAVEGACAO.map((g) => (
            <div key={g.grupo} className="nav-grupo">
              <p>{g.grupo}</p>
              {g.itens.filter((i) => !i.soAdmin || eAdministrador).map(({ para, nome, icone: Icone, contador }) => (
                <NavLink key={para} to={para} end={para === '/'} className={({ isActive }) => `nav-ligacao${isActive ? ' activa' : ''}`}>
                  <Icone size={17} strokeWidth={1.8} />
                  {nome}
                  {contador === 'visitas' && visitasPendentes > 0 && <span className="contador" aria-label={`${visitasPendentes} pendentes`}>{visitasPendentes}</span>}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="lateral-rodape">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ minWidth: 0, flex: 1 }}>
              <div style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{utilizador.nome}</div>
              <Etiqueta tom={PERFIL[utilizador.perfil].tom}>{PERFIL[utilizador.perfil].nome}</Etiqueta>
            </div>
            <Botao variante="fantasma" icone onClick={seguinte} aria-label={`Tema: ${tema}`} title={`Tema: ${tema}`}>
              <IconeTema size={17} />
            </Botao>
            <Botao variante="fantasma" icone onClick={sair} aria-label="Terminar sessão" title="Terminar sessão">
              <LogOut size={17} />
            </Botao>
          </div>
        </div>
      </aside>
      <div className="principal">
        <header className="barra-topo">
          <span className="zona"><MapPin size={15} />Zona de actuação: <strong style={{ color: 'var(--tinta)' }}>{zona}</strong></span>
          <span className="espaco" />
          <span className="suave pequeno">{new Intl.DateTimeFormat('pt-MZ', { dateStyle: 'full' }).format(new Date())}</span>
        </header>
        <main className="conteudo">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
