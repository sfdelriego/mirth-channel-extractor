# 🏥 Mirth Channel Extractor

> Convierte exportaciones XML de canales **Mirth Connect** en notas **Obsidian** estructuradas y un repositorio de **código JavaScript** reutilizable.

Ideal para equipos de integración sanitaria que quieren documentar, buscar y reutilizar la lógica de sus canales HL7/FHIR sin tener que abrir Mirth cada vez.

---

## 🎯 ¿Para qué sirve?

Si trabajas con **Mirth Connect** sabes que el código JavaScript de los filtros y transformers está "atrapado" dentro del XML de cada canal. Este script los extrae en fichero individuales para poder tener une repositorio y reutilizar código:

- 📝 **Genera una nota Obsidian** por canal con descripción funcional, tipo de conectores y todo el código JS en bloques con syntax highlight
- 🗂️ **Organiza el JavaScript** en ficheros `.js` separados por canal y componente (source transformer, filtros, destinations...)
- 📋 **Crea un inventario** con tabla de todos los canales procesados
- 🔒 **Elimina credenciales** automáticamente (IPs, passwords, usuarios) de las descripciones
- 🏷️ **Anonimiza** el nombre del hospital si es algo habitual en el nombre de los canales para poder reutilizar la documentación en otros entornos
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

  "replacements": {
    "MiHospital":   "Hospital",
    "MiSistemaHIS": "HIS",
    "MiPACS":       "PACS"
  }
}
```

El fichero `config.json` está en `.gitignore` y **nunca se sube al repositorio** — contiene rutas locales e información sensible de tu entorno.

El campo `replacements` es un diccionario de sustituciones que se aplican a los textos descriptivos (descripciones, nombres de steps...) pero **no** al código JavaScript. Útil para anonimizar el nombre de tu hospital, el HIS, el PACS, etc.

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

---

## 📁 Estructura de salida

```
📂 Obsidian/Mirth/Canales/
│
├── 📄 Canales Mirth - Inventario.md      ← tabla de todos los canales
│
├── 📄 T_HOSPITAL_ADT.md                  ← nota del canal
├── 📄 T_HOSPITAL_SIU.md
├── 📄 C_HOSPITAL_SMS.md
└── 📄 E_HOSPITAL_WS_DEMOGRAFICOS.md

📂 mirth-js-repo/
│
├── 📄 INVENTORY.md
│
├── 📂 T_HOSPITAL_ADT/
│   ├── 📄 source_transformer.js
│   ├── 📄 source_filter.js
│   ├── 📄 dest_CrearPaciente_filter.js
│   ├── 📄 dest_CrearPaciente_transformer.js
│   ├── 📄 dest_ModificarPaciente_filter.js
│   └── 📄 dest_ModificarPaciente_transformer.js
│
├── 📂 C_HOSPITAL_SMS/
│   ├── 📄 source_filter.js
│   └── 📄 source_transformer.js
│
└── 📂 _Deprecated/
    └── 📂 T_HOSPITAL_ADT_OLD/
        └── 📄 source_transformer.js
```

---

## 📄 Ejemplo de nota Obsidian generada

````markdown
---
tags:
  - mirth
  - canal
---

# T_HOSPITAL_IMH_InMillenniumADT

## Descripcion

Receptor TCP de mensajes HL7 ADT desde Millennium. Mapea datos demográficos
completos del paciente (NHC, datos personales, domicilio, identificadores: NIF,
CIPN, CIPA, CIAS) y datos del episodio (ingreso, servicio, cama, médico).
Distribuye a HPHIS según tipo de evento ADT: crear/modificar paciente (A28/A31),
registrar episodio (A01/A04), trasladar (A02/A12), alta (A03)...

## Configuracion

| Campo          | Valor                  |
|----------------|------------------------|
| **Source**     | TCP Listener (MLLP/HL7)|
| **Puerto**     | 6661                   |
| **Version Mirth** | 3.12.0              |
| **Destinations**  | 11                  |

## Destinations

| Nombre                    | Tipo               |
|---------------------------|--------------------|
| OutHphisCrearPaciente     | JavaScript Writer  |
| OutHphisModificarPaciente | JavaScript Writer  |
| OutHphisAltaEpisodio      | JavaScript Writer  |
| ...                       | ...                |

## Scripts — Source

### Filter: Acepta solo eventos soportados

```javascript
// Solo procesamos eventos ADT conocidos
var eventType = msg['MSH']['MSH.9']['MSG.2'].toString();
var supported = ['A01','A02','A03','A04','A08','A11','A12','A13','A17','A28','A31','A34','A44'];
return supported.indexOf(eventType) >= 0;
```

### Transformer: T_MAP_PAC_NUMEROHC

```javascript
var nhc = msg['PID']['PID.3']['CX.1'].toString();
channelMap.put('numerohc', nhc);
```
````

---

## 🔐 Limpieza automática de credenciales

El script detecta y elimina automáticamente líneas que contengan:

| Patrón detectado | Ejemplo |
|---|---|
| Direcciones IP | `10.116.128.138:4300` |
| Passwords | `pwd: MyP@ss123` / `password: secret` |
| Usuarios | `U: admin` / `login: mirth_user` |
| Credenciales de entorno | `Produccion U: hismirth01 P: xxxxx` |

> ⚠️ Siempre revisa las notas generadas antes de publicarlas. El script hace un primer filtro pero puede no cubrir todos los casos.

---

## 🏷️ Anonimización y reemplazos

El diccionario `replacements` de `config.json` permite sustituir cualquier término en los textos descriptivos, **sin tocar** los nombres técnicos de canales, variables ni bloques de código JavaScript:

```json
"replacements": {
  "HUCA":       "Hospital",
  "Millennium": "HIS"
}
```

```
"Integracion ADT Millennium - HPHIS en el HUCA"
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
4. Abre la nota en Obsidian y mejora la descripción auto-generada
5. (Opcional) Sube el repositorio JS a GitHub para compartirlo
```

> 📌 Si la descripción del canal en Mirth estaba vacía o era muy vaga, el script genera una automática basada en los conectores y nombres de steps. Aparece marcada con un callout `[!todo]` para que recuerdes revisarla.

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
