# Painel web — Vigilância Fitossanitária

Painel para **técnicos** e **administradores** da plataforma: indicadores e mapa da zona,
diagnósticos (com fotografia, Grad-CAM e validação), alertas por zona, catálogo de culturas e
pragas, versões do modelo e contas. Os agricultores usam a aplicação móvel.

React 18 + Vite 5 + TypeScript, TanStack Query, Axios e d3-geo (mapa).

## Executar

```bash
cd admin
npm install
cp .env.example .env        # se a API não estiver em http://localhost:8000
npm run dev                 # http://localhost:5173
```

A API tem de estar a correr e a autorizar a origem do painel (`CORS_ORIGENS`, por omissão
`localhost:5173`, `5174` e `4173`). Entrar com uma conta de técnico ou de administrador.

Outros comandos: `npm run build` (versão de produção em `dist/`), `npm run verificar` (TypeScript).

## Arquitectura (MVVM)

```
src/
  model/        Model: tipos do domínio, cliente HTTP (token, erros) e repositórios (uma função por rota)
  viewmodels/   ViewModel: um hook por ecrã (estado, filtros, pedidos, acções) + referências partilhadas
  views/        View: componentes de apresentação, sem pedidos à API nem regras
  ui/           componentes visuais reutilizáveis e gráficos (colunas, barras, mapa)
  nucleo/       sessão, notificações, formatação pt-MZ e rótulos do domínio
  estilos/      tokens de design (claro/escuro), base e componentes
  app/          rotas e casca (navegação, zona de actuação, tema)
```

- A **View** só lê o que o ViewModel expõe e chama as suas acções.
- O **ViewModel** usa os repositórios através do TanStack Query (cache, recarregamento,
  invalidação depois de alterar dados) e transforma os dados para o ecrã.
- O **Model** não conhece ecrãs: tipos iguais aos esquemas da API e funções de acesso.

## Regras visíveis no painel

- O técnico vê e actua só na sua zona (distrito ou província); o administrador vê o país.
- Só o administrador altera o catálogo, publica modelos e gere contas.
- Gráficos: paleta validada para daltonismo (azul/laranja), escala sequencial azul no mapa,
  níveis de alerta sempre com ícone e texto, modo escuro próprio.
