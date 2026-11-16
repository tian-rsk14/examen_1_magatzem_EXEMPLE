# Examen 1 Magatzem — EXEMPLE

Projecte de referència del docent per a la gestió d'un magatzem amb validació d'informes a través del mecanisme d'eines/conectors d'OpenCode (servidor MCP local per stdio JSON-RPC 2.0).

---

## Verificació dels requisits de l'enunciat.pdf

S'ha llegit l'enunciat (convertit a text amb `pdftotext`) i s'han comprovat tots els requisits:

| Requisit de l'enunciat | Estat | Com s'ha complert |
|------------------------|-------|-------------------|
| Flux que consulti l'inventari per MCP, calculi compres, validi i desi per MCP | ✅ | `llegir_inventari` → càlcul reposició → `validar_informe` → `desar_informe` |
| Tres subagents: integrador, desenvolupador, verificador | ✅ | Dispatchats via OpenCode amb sessions `ses_*` |
| Tres skills específiques | ✅ | `connectar-inventari`, `calcular-reposicio`, `auditar-reposicio` carregades i invocades |
| Subagents definits a `.opencode/agents/` | ✅ | `integrador.md`, `desenvolupador.md`, `verificador.md` |
| Skills definides a `.opencode/skills/<nom>/SKILL.md` | ✅ | Cada skill amb `name`, `description`, entrades, procediment, eines i resultat |
| Servidor MCP local registrat a `opencode.json` | ✅ | Servidor `magatzem` via `python3 mcp_server.py` |
| Eina `llegir_inventari()` retorna l'inventari actual | ✅ | Retorna `dades/inventari.json` via MCP stdio |
| Eina `desar_informe(informe)` valida, desa i retorna confirmació | ✅ | Valida abans d'escriure; si invàlid, no sobreescribe el fitxer previ |
| Eina personalitzada `validar_informe(ruta)` retorna `{valide, errors}` | ✅ | Registrada a `mcp_server.py` i cridada via MCP stdio |
| Comprova camps obligatoris | ✅ | `reposicions`, `unitats_totals`, `descartats` |
| Comprova quantitats enters positius | ✅ | Rebutja booleans, no-int i <= 0 |
| Comprova identificadors no repetits | ✅ | Conjunt `ids_vistos` detecta duplicats |
| Comprova total d'unitats = suma quantitats | ✅ | Compara `unitats_totals` amb la suma acumulada |
| Verificador invoca `validar_informe` abans de desar | ✅ | `desar_informe` crida validació abans d'escriure al disc |
| Dades: estoc, minim, objectiu enters no negatius | ✅ | Validat a l'entrada i a les proves |
| objectiu >= minim; productes invàlids es descarten | ✅ | P3 (estoc -1) descartat al càlcul |
| Si estoc < minim, compra = objectiu - estoc | ✅ | P1=8, P3=7, P4=4 |
| Si estoc >= minim, no es proposa compra | ✅ | P2 (estoc=mínim=5) exclòs |
| Reposicions ordenades per identificador ascendent | ✅ | Informe desat ordenat P1, P3, P4 |
| Descartats conserven ordre d'entrada | ✅ | Llista `descartats` sense reordenar |
| No modificar dades originals | ✅ | `dades/inventari.json` sense canvis |
| Exemple d'entrada i resultat esperat | ✅ | P1=8, P4=4, total=12, descartats=["P3"] (grup 1) |
| Prova inventari buit | ✅ | `valide: true` (grup 2) |
| Prova estoc igual al mínim | ✅ | `valide: true` (grup 3) |
| Prova dades invàlides i tipus no admesos | ✅ | `valide: false` amb 6 errors concrets (grup 4) |
| Prova ordre i càlcul del total | ✅ | Ordonat vàlid; total erróneu rebutjat (grup 5) |
| Prova rebutge per `desar_informe` invàlid | ✅ | `INFORME_INVALID`, fitxer no sobreescrit (grup 6) |
| Evidències d'execucions reals, sense credencials | ✅ | `INFORME_EVIDENCIES.md` i `/tmp/opencode/evidencies/` |

---

## Descripció

Aquest projecte implementa un servidor MCP (`mcp_server.py`) que ofereix tres eines per a consultar l'inventari del magatzem, validar un informe de reposició i desar-lo definitivament. El client (`mcp_client.py`/`mcp_call.py`) es connecta al servidor a través de stdio utilitzant el protocol JSON-RPC 2.0, igual que fa OpenCode amb les seves eines natives.

L'objectiu principal és implementar l'eina **`validar_informe(ruta)`** que rep la ruta de l'informe i retorna un indicador de validesa i una llista d'errors, comprovant:

1. La presència dels camps obligatoris (`reposicions`, `unitats_totals`, `descartats`).
2. Que les quantitats de reposició siguin enters positius.
3. Que no es repeteixin identificadors a les reposicions.
4. Que el total d'unitats coincideixi amb la suma de les quantitats.

L'eina **`desar_informe`** valida l'informe abans de desar-lo; si no és vàlid, no s'escriu cap fitxer i es signal·la l'error.

---

## Estructura del projecte

```
examen_1_magatzem_EXEMPLE/
├── .gitignore                # Ignora __pycache__/ i .DS_Store
├── AGENTS.md                 # Coordinació dels tres subagents (OpenCode)
├── INFORME_EVIDENCIES.md     # Evidències brutes de les sis proves MCP
├── opencode.json             # Configuració del servidor MCP local d'OpenCode
├── infra.py                  # Excepció AppError (codi + missatge estructurats)
├── mcp_server.py             # Servidor MCP: eines i dispatch
├── mcp_client.py             # Client MCP (inicialització, crides, resposta)
├── mcp_call.py               # CLI per cridar eines MCP des de terminal
├── mcp_stdio.py              # Implementació del protocol JSON-RPC 2.0 over stdio
└── dades/
    ├── inventari.json        # Inventari actual del magatzem
    ├── informe.json          # Informe definitiu desat
    └── esperat.json          # Exemple d'informe esperat de l'enunciat
```

---

## Configuració OpenCode (`opencode.json`)

El servidor `magatzem` està registrat com a servidor local que executa `mcp_server.py` amb `/usr/bin/python3`:

```json
{
  "mcp": {
    "servers": {
      "magatzem": {
        "type": "local",
        "command": [
          "/usr/bin/python3",
          "/home/riku/joan/repaso_examen/examen_1_magatzem_EXEMPLE/mcp_server.py"
        ]
      }
    }
  }
}
```

---

## Eines MCP registrades

| Eina | Descripció | Arguments | Obligatoris |
|------|------------|-----------|-------------|
| `llegir_inventari` | Consulta l'inventari actual | — | — |
| `validar_informe` | Valida un informe des d'un fitxer i retorna `{valide, errors}` | `ruta` (string) | `ruta` |
| `desar_informe` | Valida i desa l'informe definitiu | `informe` (object) | `informe` |

Exemple de crida JSON-RPC (`tools/call`):

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "validar_informe",
    "arguments": { "ruta": "dades/informe.json" }
  }
}
```

---

## Com executar des de terminal

```bash
# 1. Llegir l'inventari
python3 mcp_call.py llegir_inventari '{}'

# 2. Validar un informe per ruta
python3 mcp_call.py validar_informe '{"ruta": "dades/informe.json"}'

# 3. Desar un informe (valida abans de desar)
python3 mcp_call.py desar_informe '{"informe": {"reposicions": [...], "unitats_totals": N, "descartats": [...]}}'
```

Si `desar_informe` rep un informe invàlid, retorna `isError: true` amb codi `INFORME_INVALID` i no modifica `dades/informe.json`.

---

## Lògica de validació (`_validar_dades_informe`)

La validació és compartida per `validar_informe` (fitxer) i `desar_informe` (objecte en memòria), cosa que garanteix consistència. Acumula **tots** els errors trobats en un sol pass:

| Regla | Comprova |
|-------|----------|
| Camps obligatoris | `reposicions`, `unitats_totals`, `descartats` han de existir |
| Quantitats enters positius | `int` (no `bool`), majors que 0 |
| Identificadors no repetits | Cap `id` duplicat a `reposicions` |
| Total d'unitats | `unitats_totals` ha de ser igual a la suma de les quantitats |

---

## Flux executat (segons AGENTS.md)

1. **Càrrega de les tres skills:** `auditar-reposicio`, `calcular-reposicio`, `connectar-inventori`.
2. **Dispatch de tres subagents** (`explore`) en OpenCode per auditar, calcular i connectar.
3. **Lectura MCP** de l'inventari amb `llegir_inventari`.
4. **Càlcul de reposició** (productes amb estoc < mínim): P1=8, P3=7, P4=4, total=19.
5. **Validació** de l'informe calculat amb `validar_informe` → `valide: true`.
6. **Desament final** amb `desar_informe` → informe desat a `dades/informe.json`.

---

## Sis proves executades (amb evidències reals vía MCP)

| Grup | Prova | Resultat |
|------|-------|----------|
| 1 | Exemple de l'enunciat (`dades/informe.json`) | `valide: true`, `errors: []` |
| 2 | Informe buit | `valide: true`, `errors: []` |
| 3 | Estoc igual al mínim (P2 exclòs) | `valide: true`, `errors: []` |
| 4 | Dades invàlides i tipus no admesos | `valide: false` amb 6 errors concrets |
| 5 | Ordre de reposicions i càlcul del total | Ordonat vàlid; total erróneu rebutjat |
| 6 | Rebuig per `desar_informe` invàlid | `INFORME_INVALID`, fitxer no sobreescrit |

Totes les sortides brutes estan a `INFORME_EVIDENCIES.md`.

---

## Repositori Git

- Repositori local creat amb `git init`.
- `.gitignore` exclou `__pycache__/` i `.DS_Store`.
- Commit `f87662b` amb 19 fitxers (inclòs README.md).
- Remot: `https://github.com/tian-rsk14/examen_1_magatzem_EXEMPLE.git`
- Branch: `master`, fent push al remot.

---

## Exemple d'informe vàlid

```json
{
  "reposicions": [
    { "id": "P1", "quantitat": 8 },
    { "id": "P3", "quantitat": 7 },
    { "id": "P4", "quantitat": 4 }
  ],
  "unitats_totals": 19,
  "descartats": []
}
```

Aquest informe passa totes les validacions i s'ha desat definitivament a `dades/informe.json`.
