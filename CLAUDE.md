# Empresas por Região — Mapa de Clientes (HI Tecnologia)

## O que é
Página web estática (sem backend) que mostra no mapa todas as empresas da carteira
de clientes do Luis (consultor comercial/técnico na HI Tecnologia), com filtros e
detalhes de contato. Uso pessoal — não é para publicação pública indexada.

## Arquivos
- `mapa-clientes.html` — página principal. Leaflet.js (mapa) + Leaflet.markercluster
  (agrupamento de pontos). Tema visual "blueprint industrial" (fundo azul-marinho,
  grade de fundo, acentos laranja/ciano). Fontes: JetBrains Mono + Inter (Google Fonts).
  Tiles do mapa: CartoDB dark_all (gratuito, sem API key).
- `companies_data.js` — dados embutidos como `const COMPANIES = [...]`. Cada empresa:
  `{id, n(ome), a(rea), t(ipo), s(tatus), c(idade), e(stado), tel(efone), em(ail),
  resp(onsável), cd (cliente de), tm (cliente telemetria? Sim/Não), sh (sheet/aba de
  origem), lat, lon, ap (approx: true se a localização é aproximada — cidade não
  informada na planilha original, ponto no centro do estado)}`.

## Origem dos dados
Os dados vêm de uma planilha Excel (`COMPANY_*.xlsx`) com abas: Infra, Diversos,
Saneamento, Agro, Outros. Colunas principais: ID, Nome da Empresa, Área(s) de Atuação,
Tipo da empresa, Status (Ativo/Inativo/Não é Cliente), Cidade, Estado, É cliente do
Portal de Telemetria?, Telefone, Email, Cliente de, Responsável.

As coordenadas foram geocodificadas por nome de cidade/UF usando uma base pública de
municípios brasileiros (pacote npm `lib-city-br`, ~5.571 municípios com lat/lon).
Erros de digitação de cidade/estado na planilha original foram corrigidos manualmente
(ex.: "Panembi/RS" → Panambi/RS). Empresas sem cidade preenchida foram posicionadas no
centro geográfico do estado e marcadas com `ap: true`.

Se a planilha for atualizada no futuro, o pipeline de geocodificação (pandas +
normalização de nomes + fallback por estado) precisa ser reaplicado para regerar
`companies_data.js`. Nenhum script Python desse pipeline está neste repositório ainda
— só o resultado final. Se quiser reprocessar, peça para reconstruir o pipeline a
partir da planilha original.

## Funcionalidades já implementadas
- Mapa com marcador em forma de losango, cor por status (ciano=Ativo,
  laranja=Não é Cliente, cinza=Inativo)
- Clusterização de pontos próximos com contador
- **Hover** num ponto → mostra o nome da empresa acima dele (tooltip)
- **Clique num cluster** → abre painel lateral direito com a lista de empresas
  daquela região (não zoom automático)
- **Clique numa empresa** (na lista ou direto no mapa) → abre painel de detalhes
  completo (telefone, e-mail, responsável, área, tipo, "cliente de", indicador de
  telemetria, coordenadas)
- Filtros: status (chips), tipo de empresa (select), área de atuação (select),
  busca por texto (nome/cidade)
- Estatísticas no topo (total, ativos, não-clientes, inativos)

## Destino no GitHub
Repositório do usuário: https://github.com/roxo-luis13/Clientes-por-regi-o.git
Ainda não foi feito o primeiro push. Este diretório deve virar a raiz desse repo.

## Próximos passos sugeridos (pendente, não decidido pelo usuário ainda)
- Fazer o primeiro commit/push para o repositório acima
- Perguntar ao usuário se quer publicar via GitHub Pages (isso tornaria a página
  pública na internet — o usuário até agora pediu explicitamente que o mapa NÃO
  fosse público/indexado, então confirme antes de habilitar Pages)
- Se for só para versionamento privado, manter o repo como **privado** no GitHub
