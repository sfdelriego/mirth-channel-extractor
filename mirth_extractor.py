#!/usr/bin/env python3
"""
mirth_extractor.py
==================
Procesa exportaciones XML de canales Mirth Connect y genera:
  - Notas Obsidian (.md) con descripcion, configuracion y codigo JS
  - Ficheros .js organizados por canal en un repositorio

Uso:
    # Un solo canal:
    python mirth_extractor.py canal.xml

    # Carpeta entera:
    python mirth_extractor.py C:/ruta/canales/

    # Con rutas de salida personalizadas:
    python mirth_extractor.py C:/canales/ --obsidian C:/vault/Mirth/ --repo S:/repo/

    # Usando un fichero de config alternativo:
    python mirth_extractor.py C:/canales/ --config mi_config.json

Configuracion (fichero config.json junto al script):
    {
      "obsidian_dir": "C:/Users/tu_usuario/Vault/Mirth/Canales",
      "repo_dir":     "C:/repos/mirth-js",
      "replacements": {
        "MiHospital": "Hospital",
        "MiHIS":      "HIS"
      }
    }

    Copia config.example.json a config.json y edita los valores.
    El fichero config.json esta en .gitignore y NO se sube al repositorio.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

# Mapeo de clases Java de conectores a nombres legibles
CONNECTOR_TYPES = {
    "FileReceiverProperties":        "File Reader",
    "FileDispatcherProperties":      "File Writer",
    "TcpReceiverProperties":         "TCP Listener (MLLP/HL7)",
    "TcpSenderProperties":           "TCP Sender (MLLP/HL7)",
    "HttpReceiverProperties":        "HTTP Listener",
    "HttpDispatcherProperties":      "HTTP Sender",
    "WebServiceReceiverProperties":  "Web Service Listener (SOAP)",
    "WebServiceDispatcherProperties":"Web Service Sender (SOAP)",
    "JavaScriptReceiverProperties":  "JavaScript Reader",
    "JavaScriptDispatcherProperties":"JavaScript Writer",
    "SmtpDispatcherProperties":      "SMTP (Email)",
    "MllpReceiverProperties":        "MLLP Listener",
    "MllpSenderProperties":          "MLLP Sender",
    "VmReceiverProperties":          "Channel Reader",
    "VmDispatcherProperties":        "Channel Writer",
    "DatabaseReceiverProperties":    "Database Reader",
    "DatabaseDispatcherProperties":  "Database Writer",
    "DimseReceiverProperties":       "DICOM Listener",
    "DimseSenderProperties":         "DICOM Sender",
    "JmsReceiverProperties":         "JMS Listener",
    "JmsSenderProperties":           "JMS Sender",
}

# Patrones de credenciales a eliminar de los textos
CREDENTIAL_PATTERNS = [
    r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?\b',   # IPs con o sin puerto
    r'(?i)pwd\s*[:\-]\s*\S+',                              # pwd: valor
    r'(?i)password\s*[:\-]\s*\S+',                         # password: valor
    r'(?i)contrase[nñ]a\s*[:\-]\s*\S+',                   # contraseña: valor
    r'(?i)(U|user|usuario)\s*:\s*\S+',                     # U: usuario
    r'(?i)(P|pass)\s*:\s*\S+',                             # P: pass
    r'(?i)login\s*[:\-]\s*\S+',                            # login: valor
    r'(?i)Produccion U:.*',                                 # lineas de credenciales de produccion
    r'(?i)Test U:.*',                                       # lineas de credenciales de test
]


# =============================================================================
# Carga de configuracion
# =============================================================================

def load_config(config_path: Path) -> dict:
    """
    Lee el fichero JSON de configuracion y devuelve un dict con los valores.
    Las claves que empiezan por '_' (comentarios) se ignoran.
    Si el fichero no existe, devuelve un dict vacio (se usaran los defaults de CLI).
    """
    if not config_path.exists():
        print(f"\n  ⚠️  No se encontro config.json en: {config_path}")
        print(f"     Copia config.example.json a config.json y edita los valores.\n")
        return {}
    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)
    # Filtrar claves internas de comentarios
    return {k: v for k, v in data.items() if not k.startswith("_")}


# =============================================================================
# Utilidades de texto
# =============================================================================

def remove_credentials(text: str) -> str:
    """Elimina lineas completas que contengan patrones de credenciales."""
    lines = text.splitlines()
    clean_lines = []
    for line in lines:
        skip = any(re.search(p, line) for p in CREDENTIAL_PATTERNS)
        if not skip:
            clean_lines.append(line)
    return "\n".join(clean_lines).strip()


def apply_replacements(text: str, replacements: dict) -> str:
    """
    Aplica el diccionario de reemplazos sobre el texto,
    respetando los bloques de codigo (``` ... ```) que NO se modifican.
    """
    if not replacements:
        return text

    # Dividir en partes: indices pares = texto normal, impares = bloques de codigo
    parts = re.split(r"(```[\s\S]*?```)", text)
    result = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            # Texto normal: aplicar reemplazos
            for original, replacement in replacements.items():
                part = re.sub(
                    rf"\b{re.escape(original)}\b",
                    replacement,
                    part,
                    flags=re.IGNORECASE,
                )
        result.append(part)
    return "".join(result)


def sanitize_text(text: str, replacements: dict) -> str:
    """
    Limpia el texto:
      - Elimina lineas con credenciales (IPs, passwords, logins)
      - Aplica el diccionario de reemplazos (anonimizacion de hospital, etc.)
    """
    return apply_replacements(remove_credentials(text), replacements)


# =============================================================================
# Parsing del XML
# =============================================================================

def get_connector_type(props_elem):
    """Devuelve el nombre legible del tipo de conector."""
    if props_elem is None:
        return "Unknown"
    class_attr = props_elem.get("class", "")
    short = class_attr.split(".")[-1]
    return CONNECTOR_TYPES.get(short, short or "Unknown")


def extract_scripts(container_elem):
    """
    Extrae scripts JS de un nodo transformer o filter.
    Soporta el formato nuevo (steps/step, rules/rule)
    y el formato antiguo (elements/com.mirth...JavaScriptStep).
    Devuelve lista de dicts: {name, script}
    """
    results = []
    if container_elem is None:
        return results

    # Formato nuevo: .//step y .//rule con subelemento <script>
    for item in container_elem.findall(".//step") + container_elem.findall(".//rule"):
        name_elem   = item.find("name")
        script_elem = item.find("script")
        if script_elem is not None and script_elem.text and script_elem.text.strip():
            results.append({
                "name":   name_elem.text if name_elem is not None else "Step",
                "script": script_elem.text.strip(),
            })

    # Formato antiguo: elements/* con tag JavaScriptStep o JavaScriptRule
    for item in list(container_elem.find("elements") or []):
        if "JavaScriptStep" in item.tag or "JavaScriptRule" in item.tag:
            name_elem   = item.find("name")
            script_elem = item.find("script")
            if script_elem is not None and script_elem.text and script_elem.text.strip():
                results.append({
                    "name":   name_elem.text if name_elem is not None else item.tag.split(".")[-1],
                    "script": script_elem.text.strip(),
                })

    return results


def parse_channel(xml_path):
    """
    Parsea un XML de canal Mirth Connect.
    Devuelve un dict con toda la informacion estructurada.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"  ERROR parseando {xml_path.name}: {e}")
        return None

    # El XML puede ser un <channel> directo o una <list><channel>
    if root.tag == "list":
        channel = root.find("channel")
    else:
        channel = root

    if channel is None:
        return None

    name        = channel.findtext("name", "Unknown")
    description = (channel.findtext("description") or "").strip()
    version     = channel.get("version", "")

    # Source connector
    source      = channel.find("sourceConnector")
    source_type = get_connector_type(source.find("properties") if source is not None else None)
    source_scheme      = ""
    source_file_filter = ""
    source_port        = ""

    if source is not None:
        props = source.find("properties")
        if props is not None:
            source_scheme      = props.findtext("scheme", "")
            source_file_filter = props.findtext("fileFilter", "")
            source_port        = props.findtext("port", "")

    src_transformer_scripts = extract_scripts(source.find("transformer") if source is not None else None)
    src_filter_scripts      = extract_scripts(source.find("filter")      if source is not None else None)

    # Destination connectors
    destinations = []
    for connector in channel.findall(".//destinationConnectors/connector"):
        dest_name = connector.findtext("name", "Destination")
        dest_type = get_connector_type(connector.find("properties"))

        # Script directo en properties (JavaScript Writer, Database Writer...)
        props_scripts = []
        props = connector.find("properties")
        if props is not None:
            script_elem = props.find("script")
            if script_elem is not None and script_elem.text and script_elem.text.strip():
                props_scripts.append({
                    "name":   f"{dest_type} Script",
                    "script": script_elem.text.strip(),
                })

        destinations.append({
            "name":                dest_name,
            "type":                dest_type,
            "filter_scripts":      extract_scripts(connector.find("filter")),
            "transformer_scripts": extract_scripts(connector.find("transformer")),
            "props_scripts":       props_scripts,
        })

    return {
        "name":                      name,
        "description":               description,
        "version":                   version,
        "source_type":               source_type,
        "source_scheme":             source_scheme,
        "source_file_filter":        source_file_filter,
        "source_port":               source_port,
        "source_transformer_scripts": src_transformer_scripts,
        "source_filter_scripts":     src_filter_scripts,
        "destinations":              destinations,
    }


# =============================================================================
# Generacion de contenido
# =============================================================================

def generate_auto_description(ch):
    """
    Genera una descripcion funcional automatica basada en los datos del canal.
    Sirve como borrador cuando no hay descripcion en el XML.
    """
    src   = ch["source_type"]
    dests = ch["destinations"]

    # Informacion del source
    src_detail = src
    if ch["source_scheme"]:
        src_detail += f" ({ch['source_scheme']})"
    if ch["source_file_filter"]:
        src_detail += f", patron: {ch['source_file_filter']}"
    if ch["source_port"]:
        src_detail += f", puerto: {ch['source_port']}"

    # Tipos de destinations unicos
    dest_types = list(dict.fromkeys(d["type"] for d in dests))
    dest_names = [d["name"] for d in dests]

    # Nombres de steps del source transformer/filter (los mas descriptivos)
    src_steps = [s["name"] for s in ch["source_filter_scripts"] + ch["source_transformer_scripts"]]
    src_steps_clean = [s for s in src_steps if s and s.lower() not in ("step", "rule", "filter rule", "transformer step")]

    # Nombres de destinations (suelen describir la logica)
    dest_ops = [d for d in dest_names if d and d.lower() not in ("destination 1", "destination 2", "destination 3")]

    # Componer descripcion
    lines = []

    if "Reader" in src or "Listener" in src:
        lines.append(f"Canal con entrada {src_detail}.")
    else:
        lines.append(f"Source: {src_detail}.")

    if dest_ops:
        lines.append(f"Operaciones/destinos: {', '.join(dest_ops[:6])}{'...' if len(dest_ops) > 6 else ''}.")

    if src_steps_clean:
        lines.append(f"Pasos en source transformer: {', '.join(src_steps_clean[:5])}{'...' if len(src_steps_clean) > 5 else ''}.")

    if dest_types:
        lines.append(f"Salida via: {', '.join(dict.fromkeys(dest_types))}.")

    desc = " ".join(lines)
    desc += "\n\n> [!todo] Descripcion generada automaticamente — revisar y completar."

    return desc


def build_description(ch, replacements: dict) -> str:
    """
    Usa la descripcion existente del canal si la tiene y es util.
    Si no, genera una automatica.
    """
    raw = ch["description"]

    if raw and len(raw.strip()) > 20:
        cleaned = sanitize_text(raw, replacements)
        if len(cleaned) > 20:
            return cleaned

    return generate_auto_description(ch)


# =============================================================================
# Escritura de salida
# =============================================================================

def write_obsidian_note(ch, output_path, replacements: dict, repo_dir: Path, deprecated=False):
    """Genera y escribe la nota Obsidian en formato Markdown."""
    lines = []

    # Frontmatter
    lines += ["---", "tags:", "  - mirth", "  - canal"]
    if deprecated:
        lines.append("  - deprecated")
    lines += ["---", ""]

    # Titulo
    lines.append(f"# {ch['name']}")
    lines.append("")

    if deprecated:
        lines += ["> [!warning] Canal deprecado", ""]

    # Descripcion
    lines.append("## Descripcion")
    lines.append("")
    lines.append(build_description(ch, replacements))
    lines.append("")

    # Configuracion
    lines.append("## Configuracion")
    lines.append("")
    lines += ["| Campo | Valor |", "|---|---|"]
    lines.append(f"| **Source** | {ch['source_type']} |")
    if ch["source_scheme"]:
        lines.append(f"| **Protocolo** | {ch['source_scheme']} |")
    if ch["source_file_filter"]:
        lines.append(f"| **Patron ficheros** | `{ch['source_file_filter']}` |")
    if ch["source_port"]:
        lines.append(f"| **Puerto** | {ch['source_port']} |")
    lines.append(f"| **Version Mirth** | {ch['version']} |")
    lines.append(f"| **Destinations** | {len(ch['destinations'])} |")
    lines.append("")

    # Destinations
    if ch["destinations"]:
        lines.append("## Destinations")
        lines.append("")
        lines += ["| Nombre | Tipo |", "|---|---|"]
        for d in ch["destinations"]:
            lines.append(f"| {d['name']} | {d['type']} |")
        lines.append("")

    # Scripts del source
    all_src = ch["source_filter_scripts"] + ch["source_transformer_scripts"]
    if all_src:
        lines.append("## Scripts — Source")
        lines.append("")
        for s in ch["source_filter_scripts"]:
            lines += [f"### Filter: {s['name']}", "", "```javascript", s["script"], "```", ""]
        for s in ch["source_transformer_scripts"]:
            lines += [f"### Transformer: {s['name']}", "", "```javascript", s["script"], "```", ""]

    # Scripts de cada destination
    for d in ch["destinations"]:
        all_d = d["filter_scripts"] + d["transformer_scripts"] + d["props_scripts"]
        if all_d:
            lines.append(f"## Scripts — {d['name']} ({d['type']})")
            lines.append("")
            for s in d["filter_scripts"]:
                lines += [f"### Filter: {s['name']}", "", "```javascript", s["script"], "```", ""]
            for s in d["transformer_scripts"]:
                lines += [f"### Transformer: {s['name']}", "", "```javascript", s["script"], "```", ""]
            for s in d["props_scripts"]:
                lines += [f"### {s['name']}", "", "```javascript", s["script"], "```", ""]

    # Enlace al repo
    repo_path = str(repo_dir / ch["name"])
    lines += ["---", f"**Codigo JS:** `{repo_path}`"]

    content = "\n".join(lines)
    output_path.write_text(content, encoding="utf-8")


def write_js_files(ch, channel_repo_dir):
    """Escribe los ficheros .js del canal en el directorio del repositorio."""
    channel_repo_dir.mkdir(parents=True, exist_ok=True)

    def join_scripts(scripts, kind):
        parts = [f"// {kind}: {s['name']}\n{s['script']}" for s in scripts]
        return "\n\n// ---\n\n".join(parts)

    def safe_name(name):
        return re.sub(r'[<>:"/\\|?*\s]', "_", name)

    if ch["source_transformer_scripts"]:
        (channel_repo_dir / "source_transformer.js").write_text(
            join_scripts(ch["source_transformer_scripts"], "Step"), encoding="utf-8")

    if ch["source_filter_scripts"]:
        (channel_repo_dir / "source_filter.js").write_text(
            join_scripts(ch["source_filter_scripts"], "Rule"), encoding="utf-8")

    for dest in ch["destinations"]:
        sn = safe_name(dest["name"])
        if dest["filter_scripts"]:
            (channel_repo_dir / f"dest_{sn}_filter.js").write_text(
                join_scripts(dest["filter_scripts"], "Rule"), encoding="utf-8")
        if dest["transformer_scripts"]:
            (channel_repo_dir / f"dest_{sn}_transformer.js").write_text(
                join_scripts(dest["transformer_scripts"], "Step"), encoding="utf-8")
        if dest["props_scripts"]:
            (channel_repo_dir / f"dest_{sn}_script.js").write_text(
                join_scripts(dest["props_scripts"], "Script"), encoding="utf-8")


def _count_scripts(ch) -> int:
    return (
        len(ch["source_filter_scripts"]) +
        len(ch["source_transformer_scripts"]) +
        sum(
            len(d["filter_scripts"]) + len(d["transformer_scripts"]) + len(d["props_scripts"])
            for d in ch["destinations"]
        )
    )


def process_file(xml_path, obsidian_dir, repo_dir, replacements: dict, deprecated=False):
    """Procesa un unico fichero XML de canal."""
    print(f"  Procesando: {xml_path.name} ... ", end="")

    ch = parse_channel(xml_path)
    if ch is None:
        print("ERROR (XML invalido o sin canal)")
        return None

    total_scripts = _count_scripts(ch)

    # Nota Obsidian
    suffix = " (deprecated)" if deprecated else ""
    note_path = obsidian_dir / f"{ch['name']}{suffix}.md"
    write_obsidian_note(ch, note_path, replacements, repo_dir, deprecated)

    # JS repo
    repo_subdir = repo_dir / ("_Deprecated" if deprecated else "") / ch["name"]
    write_js_files(ch, repo_subdir)

    print(f"OK ({total_scripts} scripts JS, {len(ch['destinations'])} destinations)")
    return ch


def update_inventory(channels, obsidian_dir, repo_dir):
    """Genera o actualiza el fichero INVENTORY.md."""
    active     = [c for c in channels if not c.get("deprecated")]
    deprecated = [c for c in channels if c.get("deprecated")]

    def make_table(channel_list, include_desc=True):
        if include_desc:
            header = "| Canal | Source | Dest | Scripts JS | Descripcion |"
            sep    = "|---|---|---|---|---|"
        else:
            header = "| Canal | Source | Scripts JS |"
            sep    = "|---|---|---|"

        rows = [header, sep]
        for c in channel_list:
            desc  = c.get("desc_short", "")
            total = c.get("total_scripts", 0)
            if include_desc:
                rows.append(f"| [[{c['name']}]] | {c['source_type']} | {len(c['destinations'])} | {total} | {desc} |")
            else:
                rows.append(f"| [[{c['name']} (deprecated)]] | {c['source_type']} | {total} |")
        return "\n".join(rows)

    lines = [
        "# Inventario Canales Mirth Connect",
        "",
        f"Total: {len(channels)} canales  ({len(active)} activos, {len(deprecated)} deprecated)",
        "",
        "## Canales Activos",
        "",
        make_table(active),
        "",
    ]
    if deprecated:
        lines += ["## Deprecated", "", make_table(deprecated, include_desc=False), ""]

    content = "\n".join(lines)

    # Obsidian (con wikilinks)
    inv_obs = obsidian_dir.parent / "Canales Mirth - Inventario.md"
    inv_obs.write_text(content, encoding="utf-8")

    # Repo (sin wikilinks)
    inv_repo = repo_dir / "INVENTORY.md"
    inv_repo.write_text(content.replace("[[", "").replace("]]", ""), encoding="utf-8")

    print(f"\n  Inventario actualizado: {inv_obs.name}")


# =============================================================================
# Punto de entrada
# =============================================================================
def main():
    # Localizar config.json en el mismo directorio que el script
    script_dir  = Path(__file__).parent
    config_path = script_dir / "config.json"

    parser = argparse.ArgumentParser(
        description="Extrae canales Mirth Connect a notas Obsidian y ficheros JS."
    )
    parser.add_argument(
        "input",
        help="Ruta al fichero XML de un canal o a una carpeta con varios XMLs."
    )
    parser.add_argument(
        "--config",
        default=str(config_path),
        help=f"Ruta al fichero de configuracion JSON. Default: {config_path}"
    )
    parser.add_argument(
        "--obsidian",
        default=None,
        help="Carpeta de salida para notas Obsidian (sobreescribe el valor del config)."
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="Carpeta raiz del repositorio JS (sobreescribe el valor del config)."
    )
    parser.add_argument(
        "--deprecated",
        action="store_true",
        help="Marca los canales como deprecated en las notas."
    )
    parser.add_argument(
        "--no-inventory",
        action="store_true",
        help="No actualizar el fichero INVENTORY.md."
    )
    args = parser.parse_args()

    # Cargar configuracion
    cfg          = load_config(Path(args.config))
    replacements = cfg.get("replacements", {})

    # Las rutas CLI tienen prioridad sobre el config; si ninguna da valor, error
    obsidian_str = args.obsidian or cfg.get("obsidian_dir")
    repo_str     = args.repo     or cfg.get("repo_dir")

    if not obsidian_str:
        print("ERROR: obsidian_dir no configurado. Usa --obsidian o define 'obsidian_dir' en config.json.")
        sys.exit(1)
    if not repo_str:
        print("ERROR: repo_dir no configurado. Usa --repo o define 'repo_dir' en config.json.")
        sys.exit(1)

    input_path   = Path(args.input)
    obsidian_dir = Path(obsidian_str)
    repo_dir     = Path(repo_str)

    obsidian_dir.mkdir(parents=True, exist_ok=True)
    repo_dir.mkdir(parents=True, exist_ok=True)

    # Recopilar XMLs a procesar
    if input_path.is_file():
        xml_files = [input_path]
    elif input_path.is_dir():
        xml_files = sorted(input_path.glob("*.xml"))
    else:
        print(f"ERROR: ruta no encontrada: {input_path}")
        sys.exit(1)

    if not xml_files:
        print(f"No se encontraron ficheros .xml en: {input_path}")
        sys.exit(1)

    repl_summary = ", ".join(f"{k}->{v}" for k, v in replacements.items()) if replacements else "(ninguno)"
    print(f"\nMirth Extractor")
    print(f"  Input        : {input_path}")
    print(f"  Obsidian     : {obsidian_dir}")
    print(f"  Repo         : {repo_dir}")
    print(f"  Reemplazos   : {repl_summary}")
    print(f"  XMLs         : {len(xml_files)} encontrados")
    print()

    processed  = []
    seen_names = set()

    # Procesar canales activos
    for xml_file in xml_files:
        ch = process_file(xml_file, obsidian_dir, repo_dir, replacements, args.deprecated)
        if ch and ch["name"] not in seen_names:
            seen_names.add(ch["name"])
            desc_full  = build_description(ch, replacements)
            first_line = desc_full.splitlines()[0]
            short      = first_line[:90] + "..." if len(first_line) > 90 else first_line
            ch["total_scripts"] = _count_scripts(ch)
            ch["desc_short"]    = short
            ch["deprecated"]    = args.deprecated
            processed.append(ch)

    # Procesar deprecated si estamos procesando una carpeta
    if input_path.is_dir():
        dep_dir = input_path / "Deprecated"
        if dep_dir.exists():
            print("\n  Deprecated:")
            for xml_file in sorted(dep_dir.glob("*.xml")):
                ch = process_file(xml_file, obsidian_dir, repo_dir, replacements, deprecated=True)
                if ch and ch["name"] not in seen_names:
                    seen_names.add(ch["name"])
                    desc_full  = build_description(ch, replacements)
                    first_line = desc_full.splitlines()[0]
                    short      = first_line[:90] + "..." if len(first_line) > 90 else first_line
                    ch["total_scripts"] = _count_scripts(ch)
                    ch["desc_short"]    = short
                    ch["deprecated"]    = True
                    processed.append(ch)

    # Inventario
    if not args.no_inventory and processed:
        update_inventory(processed, obsidian_dir, repo_dir)

    print(f"\n  Canales procesados: {len(processed)}")
    print("  Listo.\n")


if __name__ == "__main__":
    main()
