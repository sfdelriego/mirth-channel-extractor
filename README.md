🌐 **English** | [Español](README.es.md)

# 🏥 Mirth Channel Extractor

> Converts **Mirth Connect** channel XML exports into structured **Markdown notes** and a reusable **JavaScript repository**.

Designed for healthcare integration teams who want to document, search and reuse their HL7/FHIR channel logic without opening Mirth every time.

---

## 🎯 What does it do?

If you work with **Mirth Connect** you know that JavaScript code in filters and transformers is "trapped" inside each channel's XML. This script extracts it into individual files so you can build a repository and reuse code:

- 📝 **Generates a Markdown note** per channel — description, properties, TCP config, connector types and all JS code with syntax highlighting
- 🗂️ **Organises JavaScript** into `.js` files per channel and component (source transformer, filters, destinations...)
- 📋 **Creates an inventory** with a table of all processed channels
- 🔒 **Strips credentials** automatically (IPs, passwords, usernames) from descriptions
- 🏷️ **Anonymises** hospital names and system names via a replacements dictionary
- 🔀 **Flexible naming**: keep the original channel name (good for documentation) or auto-generate from connector types, e.g. `TCP_ADT-DB` (good for a reusable knowledge base)
- ⚙️ **Extracts channel properties**: initial state, message storage, last modified date, revision...
- 🔌 **Shows TCP/MLLP config**: transmission mode, port, encoding, max connections...
- 🔁 **Documents AND/OR filter operators** with visible tags in the note
- ✅ Compatible with **Mirth Connect 3.x and 4.x** (auto-detects both XML formats)

---

## 📋 Requirements

- Python **3.8 or later**
- **No external dependencies** — standard library only

```bash
python --version   # must be 3.8+
```

---

## ⚙️ Initial setup

Copy `config.example.json` to `config.json` and edit the values:

```bash
cp config.example.json config.json
```

```json
{
  "obsidian_dir": "C:\\Notes\\Mirth\\Channels",
  "repo_dir":     "C:\\repos\\mirth-js",

  "rename_by_connectors": false,

  "replacements": {
    "MyHospital":   "Hospital",
    "MyHISSystem":  "HIS",
    "MyPACS":       "PACS"
  }
}
```

`config.json` is in `.gitignore` and **never committed** — it contains local paths and environment-specific information.

| Field | Description |
|---|---|
| `obsidian_dir` | Output folder for Markdown notes |
| `repo_dir` | Root folder for extracted JavaScript files |
| `rename_by_connectors` | `false` (default): use the channel's original name. `true`: auto-generate name from connectors (see [Connector-based naming](#-connector-based-naming)) |
| `replacements` | Dictionary of case-insensitive word substitutions applied to descriptions (not to JS code) |

> 💡 All paths can be overridden with CLI arguments without editing the config file.

---

## 🚀 Usage

### Single channel

```bash
python mirth_extractor.py C:\exports\MyChannel.xml
```

### Entire folder

```bash
python mirth_extractor.py C:\exports\channels\
```

> If a `Deprecated\` subfolder exists inside, it is processed automatically and notes are tagged as deprecated.

### Custom output paths (override config.json)

```bash
python mirth_extractor.py C:\exports\channels\ --obsidian C:\notes\Mirth\ --repo C:\repos\mirth-js\
```

### Alternative config file

```bash
python mirth_extractor.py channel.xml --config C:\configs\hospital_b.json
```

### Mark channels as deprecated

```bash
python mirth_extractor.py old_channel.xml --deprecated
```

### Skip inventory update

```bash
python mirth_extractor.py channel.xml --no-inventory
```

### Connector-based naming

```bash
python mirth_extractor.py C:\exports\channels\ --rename-by-connectors
```

> Generates names like `TCP_ADT-DB`, `FR_SFTP-FW_SMB`, `HTTP-JS`... from the source and destination connector types. Duplicate patterns get a numeric suffix (`TCP_ADT-DB_1`, `TCP_ADT-DB_2`). Can also be set in `config.json` with `"rename_by_connectors": true`.

---

## 📁 Output structure

```
📂 notes/Mirth/Channels/
│
├── 📄 Canales Mirth - Inventario.md      ← channel inventory table
│
├── 📄 TCP_ADT-DB.md                      ← channel note
├── 📄 TCP_SIU-JS.md
├── 📄 FR_SFTP-DB.md
└── 📄 HTTP-WS.md

📂 mirth-js-repo/
│
├── 📄 INVENTORY.md
│
├── 📂 TCP_ADT-DB/
│   ├── 📄 source_filter.js
│   ├── 📄 source_transformer.js
│   ├── 📄 dest_RegisterPatient_filter.js
│   ├── 📄 dest_RegisterPatient_script.js
│   ├── 📄 dest_RecordAdmission_filter.js
│   └── 📄 dest_RecordAdmission_script.js
│
├── 📂 FR_SFTP-DB/
│   ├── 📄 source_filter.js
│   └── 📄 source_transformer.js
│
└── 📂 _Deprecated/
    └── 📂 TCP_ADT-DB_OLD/
        └── 📄 source_transformer.js
```

> 💡 The [`channel-example/`](channel-example/) folder contains a complete working example: export XML, generated Markdown note and JS files.

---

## 📄 Generated note example

> See the full example in [`channel-example/TCP_ADT-DB.md`](channel-example/TCP_ADT-DB.md).

````markdown
---
tags:
  - mirth
  - canal
---

# TCP_ADT-DB

## Propiedades del canal

| Propiedad | Valor |
|---|---|
| Almacenamiento mensajes | DEVELOPMENT |
| Estado inicial | STARTED |

| Metadato | Valor |
|---|---|
| Revision | 3 |
| Ultima modificacion | 2025-12-01 10:30 UTC (Europe/Madrid) |

## Descripcion

Example channel. Receives HL7 v2 ADT messages via TCP/MLLP,
filters by event type and maps patient demographics to channel variables.

## Configuracion

| Campo | Valor |
|---|---|
| **Source** | TCP Listener (MLLP/HL7) |
| **Inbound** | HL7V2 |
| **Outbound** | HL7V2 |
| **Puerto** | 6661 |
| **Version Mirth** | 4.5.2 |
| **Destinations** | 2 |

## Configuracion TCP Listener (MLLP/HL7)

| Parametro | Valor |
|---|---|
| Modo transmision | MLLP |
| Max conexiones | 10 |
| Codificacion | DEFAULT_ENCODING |

## Destinations

| Nombre | Tipo | Inbound | Outbound | Activo | Espera ant. |
|---|---|---|---|---|---|
| RegisterPatient | JavaScript Writer | HL7V2 | HL7V2 | ✓ | ✓ |
| RecordAdmission | JavaScript Writer | HL7V2 | HL7V2 | ✓ | ✗ |

## Scripts — Source

### Filter: Accept ADT messages only

```javascript
return msg['MSH']['MSH.9']['MSG.1'].toString() === 'ADT';
```

### Filter `[OR]`: Accept supported event types

```javascript
var eventType = msg['MSH']['MSH.9']['MSG.2'].toString();
var supported = ['A01', 'A04', 'A08', 'A28', 'A31'];
return supported.indexOf(eventType) >= 0;
```

### Transformer: MapPatientDemographics

```javascript
var nhc = msg['PID']['PID.3']['CX.1'].toString();
channelMap.put('nhc', nhc);
channelMap.put('eventType', msg['MSH']['MSH.9']['MSG.2'].toString());
```

---
**JS code:** `C:\repos\mirth-js\TCP_ADT-DB`
````

---

## 🔀 Connector-based naming

The `rename_by_connectors` option changes how output notes and JS folders are named:

| Value | Behaviour | When to use |
|---|---|---|
| `false` (default) | Uses the original channel name from XML | Documenting channels with meaningful names |
| `true` | Auto-generates name from connector types | Building a reusable pattern knowledge base |

### Name format

```
{SOURCE}[_MSGTYPE]-{DEST1[_DEST2]}
```

- **SOURCE** — source connector abbreviation: `TCP`, `HTTP`, `WS`, `FR_SFTP`, `FR_SMB`, `FR_FTP`, `FR_LOCAL`, `DB`, `JS`, `CH`
- **MSGTYPE** — HL7 message type detected in the original name: `ADT`, `SIU`, `ORM`, `ORU`, `MDM`...
- **DEST** — destination connector abbreviation(s): `TCP`, `FW_SFTP`, `FW_SMB`, `DB`, `WS`, `JS`, `SMTP`, `CH`
- More than 2 distinct destination types → `ROUTER`

### Examples

| Original name | Generated name |
|---|---|
| `T_HOSPITAL_InMillenniumADT` | `TCP_ADT-DB` |
| `C_HOSPITAL_SMS_ALERTS` | `HTTP-SMTP` |
| `E_HOSPITAL_WS_DEMOGRAPHICS` | `WS-DB` |
| `T_HOSPITAL_SIU_PATIENTS` | `TCP_SIU-ROUTER` |
| `Import_Files_SFTP` | `FR_SFTP-DB` |

---

## 🔐 Automatic credential removal

The script detects and removes lines containing:

| Pattern | Example |
|---|---|
| IP addresses | `10.116.128.138:4300` |
| Passwords | `pwd: MyP@ss123` / `password: secret` |
| Usernames | `U: admin` / `login: mirth_user` |
| Environment credentials | `Produccion U: hismirth01 P: xxxxx` |

> ⚠️ Always review generated notes before publishing. The script does a first pass but may not catch every case.

---

## 🔌 Supported Mirth connectors

| Mirth type | Note label |
|---|---|
| File (SFTP/FTP/SMB/local) | File Reader / File Writer |
| TCP (MLLP/HL7) | TCP Listener / TCP Sender |
| HTTP | HTTP Listener / HTTP Sender |
| Web Service (SOAP) | Web Service Listener / Web Service Sender |
| JavaScript | JavaScript Reader / JavaScript Writer |
| Database | Database Reader / Database Writer |
| SMTP | SMTP (Email) |
| Channel | Channel Reader / Channel Writer |
| DICOM | DICOM Listener / DICOM Sender |
| JMS | JMS Listener / JMS Sender |

---

## 🗺️ Compatible XML formats

Mirth Connect changed its internal XML format between versions:

| Version | Transformers | Filters |
|---|---|---|
| **3.x old** | `elements/JavaScriptStep` | `elements/JavaScriptRule` |
| **3.x / 4.x new** | `steps/step/script` | `rules/rule/script` |

The script auto-detects which format each channel uses.

---

## 💡 Recommended workflow

```
1. Open the channel in Mirth Connect and understand what it does
2. Export it: Admin → Export Channel → save the XML
3. Run the script on the exported XML
4. Open the generated note and improve the auto-generated description
5. (Optional) Push the JS repository to GitHub to share it
```

> 📌 If the channel description in Mirth was empty or too vague, the script generates one automatically from the connectors and step names. It is marked with a `[!todo]` callout so you remember to review it.

---

## 🤝 Contributing

Using this script at another hospital or integration team? Contributions welcome:

- 🐛 Open an issue if you find a channel that doesn't parse correctly
- ✨ Pull requests to add new connector types or improve description generation
- 🌍 If you adapt it for another integration engine (Rhapsody, Ensemble, etc.), share it

---

## 📜 Licence

MIT — free for personal and commercial use.

---

*Built to make life easier for healthcare integration teams working with HL7, FHIR and Mirth Connect.* 🏥
