# Empresas por Região — Mapa de Clientes (HI Tecnologia)

## O que é
Página web estática (sem backend) que mostra no mapa todas as empresas da carteira
de clientes do Luis (consultor comercial/técnico na HI Tecnologia), com filtros e
detalhes de contato.

## Arquivos
- `mapa-clientes.html` — página principal. Leaflet.js (mapa) + Leaflet.markercluster
  (agrupamento de pontos). Tema visual "blueprint industrial" (fundo azul-marinho,
  grade de fundo, acentos laranja/ciano). Fontes: JetBrains Mono + Inter (Google Fonts).
  Tiles do mapa: CartoDB dark_all (gratuito, sem API key).
- `companies_data.js` — dados embutidos como `const COMPANIES = [...]`. Cada empresa:
  `{id, n(ome), a(rea de atuação), t(ipo de empresa), s(tatus), c(idade), e(stado),
  end (ereço completo: rua/número/complemento/bairro/CEP formatados numa string, pode
  ser null), tel(efone, só dígitos), em(ail, pode ser null), resp(onsável), cd (cliente
  de), tm (cliente telemetria? "Sim"/"Não"), lat, lon, ap (approx: true se a localização
  é aproximada — cidade não encontrada/não informada, ponto no centro do estado)}`.
- `scripts/build_companies_data.py` — pipeline que regera `companies_data.js` a partir
  de uma planilha `COMPANY_*.xlsx` nova. Ver "Origem dos dados" abaixo.
- `scripts/cities_br.json` — base de ~5.571 municípios brasileiros (código IBGE, nome,
  nome normalizado, UF, lat, lon), extraída do pacote npm `lib-city-br`. Usada pelo
  script de geocodificação.

## Origem dos dados
A planilha `COMPANY_*.xlsx` (exportada do CRM) tem uma única aba com colunas: Nome da
Empresa, Tipo da empresa, Telefone de trabalho, Celular, Site Corporativo, Responsável,
Número, Complemento, Endereço, Cidade, Tipo de empresa, Estado, Razão Social, Bairro,
CEP, É cliente do Portal de Telemetria?, Status, Atendido por, Cliente de, Área(s) de
Atuação, Cliente estratégico. Ela **não tem coluna de e-mail** (diferente de versões
anteriores da planilha).

Para regerar `companies_data.js` a partir de uma planilha nova:
```
pip install pandas openpyxl   # se ainda não instalado
python3 scripts/build_companies_data.py caminho/para/COMPANY_novo.xlsx
```

O que o script faz:
- Mantém só linhas com Nome da Empresa preenchido e Status em
  `{Ativo, Inativo, Não é Cliente}` — outros status (`Sem fit`, `Inexistente`, em
  branco) são descartados por decisão do usuário.
- Geocodifica Cidade/Estado usando `scripts/cities_br.json`: match exato → fuzzy match
  dentro do mesmo estado (corte alto, 0.90, para evitar falsos positivos tipo bairro
  "Jurubatuba" casando com a cidade "Ubatuba") → fallback pro centro geográfico do
  estado informado (marcado `ap: true`). Nunca ignora o estado informado pra tentar
  achar a cidade em outro estado (abreviação como "POA" poderia colidir com uma cidade
  homônima não relacionada, tipo "Poá/SP", e posicionar a empresa no lugar errado
  silenciosamente).
- Erros de digitação conhecidos ficam hardcoded em `MANUAL_FIXES` no topo do script
  (ex.: "Panembi/RS" → Panambi/RS). Adicione novos casos ali conforme forem achados.
- Monta o campo `end` (endereço completo) juntando Endereço + Número + Complemento +
  Bairro + CEP numa única string formatada, removendo um resíduo tipo "(, )"/"(0, 0)"
  que a planilha às vezes deixa no fim do Endereço (placeholder de coordenada não
  preenchido). Só ~493 das 2.015 linhas têm Endereço preenchido — as demais ficam com
  `end: null` (exibido como "Não informado" no painel de detalhes).
- Como a planilha não tem mais e-mail, o script faz backfill do campo `em` a partir do
  `companies_data.js` atual, casando por nome da empresa normalizado — empresas novas
  ou com nome muito diferente do anterior ficam sem e-mail (`em: null`, exibido como
  "Não informado" no painel de detalhes).
- Gera `scripts/geocode_report.txt` (não versionado) listando toda aproximação/fuzzy
  match/erro, pra revisão manual se necessário.

Para atualizar a base de municípios (`scripts/cities_br.json`), caso o pacote
`lib-city-br` seja atualizado:
```
npm install lib-city-br --no-save
node -e "require('fs').writeFileSync('scripts/cities_br.json', JSON.stringify(require('lib-city-br/data.min.json')))"
```

A planilha original (`.xlsx`) não fica versionada no repositório — só o resultado
processado (`companies_data.js`).

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
- Filtros: status, tipo de empresa, área de atuação e responsável — todos como chips
  (mesma estética visual, todos multi-seleção: cada valor começa ativo e o clique
  inclui/exclui aquele item), busca por texto (nome/cidade/estado/endereço, incluindo
  bairro)
- Painel de filtros/busca é **retrátil** (clique na barra "// filtros e busca" no topo
  do painel) — começa recolhido em telas ≤720px para não ocupar a tela no mobile
- Cada grupo de filtro (Status, Tipo, Área, Responsável) também é retrátil
  individualmente e **começa minimizado** — clique no título do grupo (ex.: "Status")
  pra expandir e ver/selecionar os chips daquele grupo
- Busca por texto **não oculta** empresas próximas — só centraliza/dá zoom no mapa
  sobre os resultados encontrados (debounce de 500ms), mantendo a vizinhança visível.
  Os filtros de status/tipo/área/responsável continuam ocultando normalmente.
- Estatísticas no topo (total, ativos, não-clientes, inativos)

## GitHub
Repositório: https://github.com/roxo-luis13/Clientes-por-regi-o (**público**,
GitHub Pages habilitado servindo a partir da branch `main`).

URL pública da página: https://roxo-luis13.github.io/Clientes-por-regi-o/mapa-clientes.html

Fluxo de trabalho: desenvolver na branch `claude/shared-link-info-0hxk8z`, abrir PR
contra `main` e mesclar — combinado com o usuário que atualizações pedidas por ele
já devem ser commitadas/versionadas (e mescladas) sem precisar confirmar a cada passo.

**Atenção:** por ser público, `companies_data.js` expõe telefone/responsável de todas
as empresas da planilha para qualquer pessoa com o link (mesmo sem indexação por
buscadores — a página tem `<meta name="robots" content="noindex, nofollow">`).
