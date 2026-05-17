# 🏥 Mirth Channel Extractor

> Convierte exportaciones XML de canales **Mirth Connect** en notas **markdown** estructuradas y un repositorio de **código JavaScript** reutilizable.

Ideal para equipos de integración sanitaria que quieren documentar, buscar y reutilizar la lógica de sus canales HL7/FHIR sin tener que abrir Mirth cada vez.

---

## 🎯 ¿Para qué sirve?

Si trabajas con **Mirth Connect** sabes que el código JavaScript de los filtros y transformers está "atrapado" dentro del XML de cada canal. Este script los extrae en fichero individuales para poder tener une repositorio y reutilizar código:

- 📝 **Genera una nota markdown** por canal con descripción funcional, propiedades, configuración TCP, tipo de conectores y todo el código JS en bloques con syntax highlight
- 🗂️ **Organiza el JavaScript** en ficheros `.js` separados por canal y componente (source transformer, filtros, destinations...)
- 📋 **Crea un inventario** con tabla de todos los canales procesados
- 🔒 **Elimina credenciales** automáticamente (IPs, passwords, usuarios) de las descripciones
- 🏷️ **Anonimiza** el nombre del hospital si es algo habitual en el nombre de los canales para poder reutilizar la documentación en otros entornos
- 🔀 **Nombrado flexible**: conserva el nombre original del canal (ideal para documentar) o genera un nombre basado en los conectores, p.ej. `TCP_ADT-DB` (ideal para base de conocimiento reutilizable)
- ⚙️ **Extrae propiedades del canal**: estado inicial, almacenamiento de mensajes, fecha de última modificación, revisión...
- 🔌 **Muestra la configuración TCP/MLLP**: modo de transmisión, puerto, codificación, conexiones máximas...
- 🔁 **Documenta los operadores AND/OR** de los filtros con etiquetas visibles en la nota
- ✅ Compatible con **Mirth Connect 3.x y 4.x** (soporta ambos formatos XML)

---

## 📋 Requisitos

- Python **3.8 o superior**
- **Sin dependencias externas** — solo usa la librería estándar de Python

```bash
python --version   # debe ser 3.8+
```

---

## ⚙️ Configuración inicial

Copia `config.example.json` a `config.json` y edita los valores:

```bash
cp config.example.json config.json
```

```json
{
  "obsidian_dir": "C:\\Vault\\Mirth\\Canales",
  "repo_dir":     "C:\\repos\\mirth-js",

  "rename_by_connectors": false,

  "replacements": {
    "MiHospital":   "Hospital",
    "MiSistemaHIS": "HIS",
    "MiPACS":       "PACS"
  }
}
```

El fichero `config.json` está en `.gitignore` y **nunca se sube al repositorio** — contiene rutas locales e información sensible de tu entorno.

El campo `replacements` es un diccionario de sustituciones que se aplican a los textos descriptivos (descripciones, nombres de steps...) pero **no** al código JavaScript. Útil para anonimizar el nombre de tu hospital, el HIS, el PACS, etc.

El campo `rename_by_connectors` controla cómo se nombran las notas y carpetas de salida (ver sección [Nombrado por conectores](#-nombrado-por-conectores) más adelante).

> 💡 También puedes sobreescribir las rutas con argumentos de línea de comandos sin editar el fichero.

---

## 🚀 Uso

### Un solo canal

```bash
python mirth_extractor.py C:\exports\T_HOSPITAL_ADT.xml
```

### Una carpeta entera

```bash
python mirth_extractor.py C:\exports\canales\
```

> Si existe una subcarpeta `Deprecated\` dentro, se procesa automáticamente y las notas se etiquetan como deprecated.

### Con rutas personalizadas (sobreescriben config.json)

```bash
python mirth_extractor.py C:\exports\canales\ --obsidian C:\vault\Mirth\ --repo C:\repos\mirth-js\
```

### Con fichero de configuración alternativo

```bash
python mirth_extractor.py canal.xml --config C:\configs\hospital_b.json
```

### Marcar canales como deprecated

```bash
python mirth_extractor.py canal_obsoleto.xml --deprecated
```

### Sin actualizar el inventario

```bash
python mirth_extractor.py canal.xml --no-inventory
```

### Nombrar por conectores (nombre generado automáticamente)

```bash
python mirth_extractor.py C:\exports\canales\ --rename-by-connectors
```

> Genera nombres como `TCP_ADT-DB`, `FR_SFTP-FW_SMB`, `HTTP-JS`... a partir del tipo de source y destinations. Si varios canales comparten el mismo patrón de conectores, se añade un sufijo numérico (`TCP_ADT-DB_1`, `TCP_ADT-DB_2`). También puede activarse en `config.json` con `"rename_by_connectors": true`.

---

## 📁 Estructura de salida

Con el comportamiento por defecto (`rename_by_connectors: false`) el nombre del canal se toma directamente del XML. Con `rename_by_connectors: true` se genera automáticamente a partir de los conectores.

```
📂 Obsidian/Mirth/Canales/
│
├── 📄 Canales Mirth - Inventario.md      ← tabla de todos los canales
│
├── 📄 TCP_ADT-DB.md                      ← nota del canal (nombre original o por conectores)
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

> 💡 En la carpeta [`channel-example/`](channel-example/) del repositorio encontrarás un canal de ejemplo completo: XML de exportación, nota markdown generada y ficheros JS.

---

## 📄 Ejemplo de nota markdown generada

> Ver también el ejemplo completo en [`channel-example/TCP_ADT-DB.md`](channel-example/TCP_ADT-DB.md).

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
| Cifrar datos | false |
| Estado inicial | STARTED |

| Metadato | Valor |
|---|---|
| Revision | 3 |
| Ultima modificacion | 2025-12-01 10:30 UTC (Europe/Madrid) |

## Descripcion

Example channel. Receives HL7 v2 ADT messages via TCP/MLLP,
filters by event type and maps patient demographics to channel variables.
Demonstrates: MLLP source, HL7 filter with AND/OR operators,
demographic transformer and conditional multi-destination routing.

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
| MLLP v2 | false |
| Max conexiones | 10 |
| Mantener conexion | true |
| Codificacion | DEFAULT_ENCODING |

## Destinations

| Nombre | Tipo | Inbound | Outbound | Activo | Espera ant. |
|---|---|---|---|---|---|
| RegisterPatient | JavaScript Writer | HL7V2 | HL7V2 | ✓ | ✓ |
| RecordAdmission | JavaScript Writer | HL7V2 | HL7V2 | ✓ | ✗ |

## Scripts — Canal

### Preprocessor

```javascript
return message;
```

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
var nhc       = msg['PID']['PID.3']['CX.1'].toString();
var lastName  = msg['PID']['PID.5']['XPN.1'].toString();
var firstName = msg['PID']['PID.5']['XPN.2'].toString();
var eventType = msg['MSH']['MSH.9']['MSG.2'].toString();
channelMap.put('nhc',       nhc);
channelMap.put('lastName',  lastName);
channelMap.put('firstName', firstName);
channelMap.put('eventType', eventType);
```

## Scripts — RegisterPatient (JavaScript Writer)

### Filter: Only A28/A31

```javascript
var ev = $('eventType');
return ['A28', 'A31'].indexOf(ev) >= 0;
```

### JavaScript Writer Script

```javascript
var sql    = 'UPDATE PATIENTS SET FIRST_NAME=?, LAST_NAME=? WHERE PATIENT_ID=?';
var params = java.util.Arrays.asList($('firstName'), $('lastName'), $('nhc'));
// ...
```

---
**Codigo JS:** `C:\repos\mirth-js\TCP_ADT-DB`

---

## 🔐 Limpieza automática de credenciales

El script detecta y elimina automáticamente líneas que contengan:

| Patrón detectado | Ejemplo |
|---|---|
| Direcciones IP | `10.116.128.138:4300` |
| Passwords | `pwd: MyP@ss123` / `password: secret` |
| Usuarios | `U: admin` / `login: mirth_user` |
| Credenciales de entorno | `Produccion U: hismirth0123 P: xxxxx` |

> ⚠️ Siempre revisa las notas generadas antes de publicarlas. El script hace un primer filtro pero puede no cubrir todos los casos.

---

## 🏷️ Anonimización y reemplazos

El diccionario `replacements` de `config.json` permite sustituir cualquier término en los textos descriptivos, **sin tocar** los nombres técnicos de canales, variables ni bloques de código JavaScript:

```json
"replacements": {
  "CentroHospitalario":       "Hospital",
  "HISComercialName": "HIS"
}
```

```
"Integracion ADT HISComercialName - HPHIS en el CentroHospitalario"
                     ↓
"Integracion ADT HIS - HPHIS en el Hospital"
```

Puedes añadir tantas entradas como necesites (PACS, proveedor externo, región...). Los reemplazos son **insensibles a mayúsculas** y solo afectan a palabras completas.

---

## 🔌 Conectores Mirth soportados

| Tipo Mirth | Nombre en nota |
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

## 🗺️ Formatos XML compatibles

Mirth Connect cambió el formato XML interno entre versiones:

| Versión | Formato transformers | Formato filtros |
|---|---|---|
| **3.x antiguo** | `elements/JavaScriptStep` | `elements/JavaScriptRule` |
| **3.x / 4.x nuevo** | `steps/step/script` | `rules/rule/script` |

El script detecta automáticamente cuál usa cada canal y los procesa correctamente.

---

## 💡 Flujo de trabajo recomendado

```
1. Abre el canal en Mirth Connect y entiende qué hace
2. Exporta el canal: Admin → Export Channel → guarda el XML
3. Ejecuta el script sobre el XML exportado
4. Abre la nota markdown y mejora la descripción auto-generada
5. (Opcional) Sube el repositorio JS a GitHub para compartirlo
```

> 📌 Si la descripción del canal en Mirth estaba vacía o era muy vaga, el script genera una automática basada en los conectores y nombres de steps. Aparece marcada con un callout `[!todo]` para que recuerdes revisarla.

---

## 🔀 Nombrado por conectores

El campo `rename_by_connectors` (o la opción `--rename-by-connectors` en CLI) cambia el comportamiento de nombrado de las notas y carpetas JS generadas:

| Valor | Comportamiento | Cuándo usarlo |
|---|---|---|
| `false` (default) | Usa el nombre original del canal en el XML | Documentar canales con nombres significativos |
| `true` | Genera un nombre a partir de los conectores | Base de conocimiento de patrones reutilizables |

### Formato del nombre generado

```
{SOURCE}[_MSGTYPE]-{DEST1[_DEST2]}
```

Donde:
- `SOURCE` = abreviatura del conector de entrada: `TCP`, `HTTP`, `WS`, `FR_SFTP`, `FR_SMB`, `FR_FTP`, `FR_LOCAL`, `DB`, `JS`, `CH`
- `MSGTYPE` = tipo de mensaje HL7 detectado en el nombre original: `ADT`, `SIU`, `ORM`, `ORU`, `MDM`...
- `DEST` = abreviatura del/los conector/es de salida: `TCP`, `FW_SFTP`, `FW_SMB`, `DB`, `WS`, `JS`, `SMTP`, `CH`
- Si hay más de 2 tipos distintos de destino → se usa `ROUTER`

### Ejemplos

| Nombre original | Nombre generado |
|---|---|
| `T_HOSPITAL_InMillenniumADT` | `TCP_ADT-DB` |
| `C_HOSPITAL_SMS_ALERTAS` | `HTTP-SMTP` |
| `E_HOSPITAL_WS_DEMOGRAFICOS` | `WS-DB` |
| `T_HOSPITAL_SIU_PACIENTES` | `TCP_SIU-ROUTER` |
| `Import_Ficheros_SFTP` | `FR_SFTP-DB` |

Si varios canales comparten el mismo patrón, se añade sufijo numérico: `FR_SFTP-DB`, `FR_SFTP-DB_1`, `FR_SFTP-DB_2`...

---

## 🤝 Contribuciones

¿Usas este script en otro hospital o entorno? Las contribuciones son bienvenidas:

- 🐛 Abre un issue si encuentras un canal que no se parsea correctamente
- ✨ Pull requests para añadir nuevos tipos de conectores o mejorar la generación de descripciones
- 🌍 Si lo adaptas para otro sistema de integración (Rhapsody, Ensemble, etc.), compártelo

---

## 📜 Licencia

MIT — libre para uso personal y comercial.

---

*Desarrollado para facilitar la vida a los equipos de integración sanitaria que trabajan con HL7, FHIR y Mirth Connect.* 🏥
