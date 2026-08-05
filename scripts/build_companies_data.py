"""
Regenera companies_data.js a partir da planilha COMPANY_*.xlsx.

Uso:
    python3 scripts/build_companies_data.py caminho/para/COMPANY_*.xlsx

Requer pandas e openpyxl (pip install pandas openpyxl).

O que faz:
- Lê a planilha (aba única, colunas conforme export do CRM).
- Mantém só linhas com Nome da Empresa preenchido e Status em
  {Ativo, Inativo, Não é Cliente} (demais status/linhas em branco são
  descartados).
- Geocodifica Cidade/Estado usando a base de municípios em
  scripts/cities_br.json (extraída do pacote npm lib-city-br). Cidade
  ausente ou não encontrada cai no centro geográfico do estado, marcado
  com "ap": true.
- Faz backfill do campo de e-mail a partir do companies_data.js atual
  (casando por nome da empresa normalizado), já que a planilha não traz
  mais essa coluna.
- Sobrescreve companies_data.js na raiz do repositório.

Para atualizar a base de municípios (scripts/cities_br.json), rode:
    npm install lib-city-br --no-save
    node -e "require('fs').writeFileSync('scripts/cities_br.json', \\
      JSON.stringify(require('lib-city-br/data.min.json')))"
"""

import json
import re
import sys
import unicodedata
import difflib
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
CITIES_JSON = Path(__file__).resolve().parent / "cities_br.json"
OUT_JS = REPO_ROOT / "companies_data.js"
REPORT_PATH = Path(__file__).resolve().parent / "geocode_report.txt"

ALLOWED_STATUS = {"Ativo", "Inativo", "Não é Cliente"}

# correções manuais para erros de digitação conhecidos na planilha
MANUAL_FIXES = {
    ("panembi", "RS"): "panambi",
}


def strip_accents(s):
    if s is None:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def norm(s):
    return re.sub(r"\s+", " ", strip_accents(s).lower().strip())


def parse_uf(estado):
    if not estado or not str(estado).strip():
        return None
    s = str(estado).strip()
    m = re.search(r"-\s*([A-Z]{2})\s*$", s)
    if m:
        return m.group(1)
    if len(s) == 2:
        return s.upper()
    return None


def digits_only(v):
    if v is None:
        return None
    s = str(v)
    if s.lower() in ("nan", "none", ""):
        return None
    d = re.sub(r"[^0-9]", "", s)
    return int(d) if d else None


def clean_str(v):
    if v is None:
        return None
    s = str(v).strip()
    return s if s and s.lower() != "nan" else None


def load_city_db():
    with open(CITIES_JSON, "r", encoding="utf-8") as f:
        cities_raw = json.load(f)

    by_key = {}       # (normalized_name, uf) -> (lat, lon, official_name)
    by_norm_name = {}  # normalized_name -> [(uf, lat, lon, official_name), ...]
    state_cities = {}  # uf -> [(lat, lon), ...]

    for code, name, nname, uf, lat, lon in cities_raw:
        by_key[(nname, uf)] = (lat, lon, name)
        by_norm_name.setdefault(nname, []).append((uf, lat, lon, name))
        state_cities.setdefault(uf, []).append((lat, lon))

    state_center = {
        uf: (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
        for uf, pts in state_cities.items()
    }
    return by_key, state_center


def make_geocoder(by_key, state_center):
    def geocode(cidade, uf):
        """Retorna (lat, lon, aproximado, nota)."""
        if not uf:
            return None, None, True, "sem estado"
        if not cidade or not str(cidade).strip():
            c = state_center.get(uf)
            if c:
                return c[0], c[1], True, "sem cidade -> centro do estado"
            return None, None, True, "sem cidade e sem estado valido"

        nname = norm(cidade)
        nname = MANUAL_FIXES.get((nname, uf), nname)

        key = (nname, uf)
        if key in by_key:
            lat, lon, _ = by_key[key]
            return lat, lon, False, None

        # fuzzy match dentro do mesmo estado, com corte alto para evitar
        # falsos positivos (ex.: "Jurubatuba", bairro de São Paulo,
        # combinando por similaridade com "Ubatuba", cidade litorânea
        # não relacionada a ~200km de distância)
        candidates_in_uf = [n for n, u in by_key.keys() if u == uf]
        close = difflib.get_close_matches(nname, candidates_in_uf, n=1, cutoff=0.90)
        if close:
            lat, lon, _ = by_key[(close[0], uf)]
            return lat, lon, False, "fuzzy:" + close[0]

        # Propositalmente não tentamos casar o nome da cidade ignorando o
        # estado informado: texto abreviado (ex. "POA" para Porto Alegre)
        # pode colidir com uma cidade homônima não relacionada em outro
        # estado (ex. "Poá/SP"), posicionando a empresa no lugar errado
        # silenciosamente. É mais seguro cair no centro do estado
        # informado e marcar como aproximado.
        c = state_center.get(uf)
        if c:
            return c[0], c[1], True, "cidade nao encontrada -> centro do estado"
        return None, None, True, "sem geocodificacao possivel"

    return geocode


def load_old_emails():
    old_email_by_name = {}
    if OUT_JS.exists():
        content = OUT_JS.read_text(encoding="utf-8")
        m = re.search(r"const COMPANIES = (\[.*\]);", content, re.S)
        if m:
            for c in json.loads(m.group(1)):
                if c.get("em") and c.get("n"):
                    old_email_by_name[norm(c["n"])] = c["em"]
    return old_email_by_name


def main():
    if len(sys.argv) != 2:
        print(f"Uso: python3 {sys.argv[0]} caminho/para/planilha.xlsx", file=sys.stderr)
        sys.exit(1)
    xlsx_path = sys.argv[1]

    by_key, state_center = load_city_db()
    geocode = make_geocoder(by_key, state_center)
    old_email_by_name = load_old_emails()
    print("empresas com e-mail conhecido (base atual):", len(old_email_by_name), file=sys.stderr)

    df = pd.read_excel(xlsx_path)
    df = df[df["Nome da Empresa"].notna()]
    df = df[df["Status"].isin(ALLOWED_STATUS)]
    print("linhas após filtro de nome/status:", len(df), file=sys.stderr)

    companies = []
    report_lines = []
    next_id = 1

    for _, row in df.iterrows():
        nome = clean_str(row.get("Nome da Empresa"))
        if not nome:
            continue

        estado = clean_str(row.get("Estado"))
        uf = parse_uf(estado)
        cidade = clean_str(row.get("Cidade"))

        tel = digits_only(row.get("Telefone de trabalho"))
        if tel is None:
            tel = digits_only(row.get("Celular"))

        telemetria_raw = clean_str(row.get("É cliente do Portal de Telemetria?"))
        tm = "Sim" if telemetria_raw and telemetria_raw.strip().lower() == "sim" else "Não"

        lat, lon, approx, note = geocode(cidade, uf)
        if lat is None:
            report_lines.append(f"SEM COORDENADAS: {nome!r} cidade={cidade!r} estado={estado!r}")
            continue
        if note:
            report_lines.append(f"{note}: {nome!r} cidade={cidade!r} estado={estado!r}")

        companies.append({
            "id": next_id,
            "n": nome,
            "a": clean_str(row.get("Área(s) de Atuação")),
            "t": clean_str(row.get("Tipo da empresa")),
            "s": clean_str(row.get("Status")),
            "c": cidade,
            "e": estado,
            "tel": tel,
            "em": old_email_by_name.get(norm(nome)),
            "resp": clean_str(row.get("Responsável")),
            "cd": clean_str(row.get("Cliente de")),
            "tm": tm,
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "ap": approx,
        })
        next_id += 1

    print("empresas geradas:", len(companies), file=sys.stderr)

    with open(OUT_JS, "w", encoding="utf-8") as f:
        f.write("const COMPANIES = ")
        f.write(json.dumps(companies, ensure_ascii=False, separators=(",", ":")))
        f.write(";\n")

    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"relatório de geocodificação: {REPORT_PATH} ({len(report_lines)} linhas)", file=sys.stderr)


if __name__ == "__main__":
    main()
