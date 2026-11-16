"""Servidor MCP del magatzem: lectura d'inventari, validació i desament d'informes."""
from pathlib import Path
import json
from infra import AppError
from mcp_stdio import MCPServer, definition

ROOT = Path(__file__).resolve().parent
DADES = ROOT / "dades"
INVENTARI_FITXER = DADES / "inventari.json"
INFORME_FITXER = DADES / "informe.json"

# Estructura esperada d'un informe vàlid.
CAMP_OBLIGATORIS = ("reposicions", "unitats_totals", "descartats")


def llegir_inventari():
    """Retorna l'inventari actual del fitxer proporcionat."""
    if not INVENTARI_FITXER.is_file():
        raise AppError("INVENTARI_NO_TROBAT",
                       f"No s'ha trobat el fitxer d'inventari: {INVENTARI_FITXER}")
    try:
        with INVENTARI_FITXER.open("r", encoding="utf-8") as fitxer:
            inventari = json.load(fitxer)
    except json.JSONDecodeError as exc:
        raise AppError("DADES_INVALIDES",
                       f"El fitxer d'inventari no conté JSON vàlid: {exc}")
    except OSError as exc:
        raise AppError("INVENTARI_NO_LEGIBLE",
                       f"No s'ha pogut llegir l'inventari: {exc}")
    if not isinstance(inventari, list):
        raise AppError("DADES_INVALIDES",
                       "L'inventari ha de ser una llista de productes.")
    return inventari


def _validar_dades_informe(informe):
    """Valida les dades d'un informe.

    Retorna una tupla (valide: bool, errors: llista de cadenes) amb tots els
    errors trobats, sense aturar-se al primer error. Aquesta és la lògica
    compartida utilitzada tant per l'eina validar_informe (fitxer) com pel
    verificador de desar_informe (objecte en memòria).
    """
    errors = []

    if not isinstance(informe, dict):
        return False, ["L'informe ha de ser un objecte JSON."]

    # 1. Presència dels camps obligatoris.
    faltants = [camp for camp in CAMP_OBLIGATORIS if camp not in informe]
    if faltants:
        errors.append(f"Falten camps obligatoris: {', '.join(faltants)}")

    reposicions = informe.get("reposicions")
    suma_quantitats = 0
    reposicions_estructura_ok = False

    if isinstance(reposicions, list):
        reposicions_estructura_ok = True
        ids_vistos = set()
        for index, reposicio in enumerate(reposicions):
            prefix = f"reposicions[{index}]"
            if not isinstance(reposicio, dict):
                errors.append(f"{prefix} ha de ser un objecte.")
                continue

            identificador = reposicio.get("id")
            if not isinstance(identificador, str) or not identificador:
                errors.append(f"{prefix}.id ha de ser un text no buit.")
            else:
                # 3. Que no es repeteixin identificadors a les reposicions.
                if identificador in ids_vistos:
                    errors.append(f"{prefix}.id '{identificador}' està repetit.")
                ids_vistos.add(identificador)

            quantitat = reposicio.get("quantitat")
            # 2. Que les quantitats de reposició siguin enters positius.
            if isinstance(quantitat, bool) or not isinstance(quantitat, int) or quantitat <= 0:
                errors.append(f"{prefix}.quantitat ha de ser un enter positiu.")
            else:
                suma_quantitats += quantitat

    # 4. Que el total d'unitats coincideixi amb la suma de les quantitats.
    unitats_totals = informe.get("unitats_totals")
    if isinstance(unitats_totals, bool) or not isinstance(unitats_totals, int) or unitats_totals < 0:
        errors.append("unitats_totals ha de ser un enter no negatiu.")
    elif reposicions_estructura_ok:
        if unitats_totals != suma_quantitats:
            errors.append(
                f"unitats_totals ({unitats_totals}) no coincideix amb la suma "
                f"de les quantitats ({suma_quantitats})."
            )

    descartats = informe.get("descartats")
    if descartats is not None and (
            not isinstance(descartats, list) or
            not all(isinstance(d, str) for d in descartats)):
        errors.append("descartats ha de ser una llista de textos.")

    return len(errors) == 0, errors


def validar_informe(ruta):
    """Valida l'informe del fitxer donat per la ruta.

    Rep la ruta de l'informe i retorna un indicador de validesa i una llista
    d'errors: {"valide": bool, "errors": [str]}.
    """
    fitxer = Path(ruta)
    if not fitxer.is_file():
        return {"valide": False, "errors": [f"No s'ha trobat el fitxer d'informe: {ruta}"]}
    try:
        with fitxer.open("r", encoding="utf-8") as fitxer_obert:
            informe = json.load(fitxer_obert)
    except json.JSONDecodeError as exc:
        return {"valide": False, "errors": [f"El fitxer no conté JSON vàlid: {exc}"]}
    except OSError as exc:
        return {"valide": False, "errors": [f"No s'ha pogut llegir l'informe: {exc}"]}
    valide, errors = _validar_dades_informe(informe)
    return {"valide": valide, "errors": errors}


def desar_informe(informe):
    """Valida i desa l'informe.

    El verificador invoca la validació abans de desar l'informe definitiu.
    Si l'informe no és vàlid, no s'escriu cap fitxer i es signal·la l'error.
    """
    # El verificador valida abans de tocar el fitxer per no sobreescriure un
    # informe vàlid previ.
    valide, errors = _validar_dades_informe(informe)
    if not valide:
        raise AppError("INFORME_INVALID",
                       "L'informe no és vàlid: " + "; ".join(errors))

    try:
        with INFORME_FITXER.open("w", encoding="utf-8") as fitxer:
            json.dump(informe, fitxer, ensure_ascii=False, indent=2)
            fitxer.write("\n")
    except OSError as exc:
        raise AppError("INFORME_NO_DESAT",
                       f"No s'ha pogut desar l'informe: {exc}")

    return {
        "ok": True,
        "missatge": "Informe desat correctament.",
        "ruta": str(INFORME_FITXER),
    }


TOOLS = [
    definition("llegir_inventari", "Consulta l'inventari actual."),
    definition("desar_informe", "Valida i desa l'informe.",
               {"informe": {"type": "object"}}, ["informe"]),
    definition("validar_informe", "Valida un informe des d'un fitxer i retorna validesa i errors.",
               {"ruta": {"type": "string"}}, ["ruta"]),
]


def dispatch(name, arguments):
    if name == "llegir_inventari":
        return llegir_inventari()
    if name == "desar_informe":
        return desar_informe(arguments["informe"])
    return validar_informe(arguments["ruta"])


if __name__ == "__main__":
    MCPServer("magatzem", TOOLS, dispatch).serve()
