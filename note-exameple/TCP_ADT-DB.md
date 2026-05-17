---
tags:
  - mirth
  - canal
---

# TCP_ADT-DB

## Propiedades del canal

| Propiedad | Valor |
|---|---|
| Limpiar mapa canal | true |
| Almacenamiento mensajes | DEVELOPMENT |
| Cifrar datos | false |
| encryptAttachments | false |
| encryptCustomMetaData | false |
| removeContentOnCompletion | false |
| removeOnlyFilteredOnCompletion | false |
| removeAttachmentsOnCompletion | false |
| Estado inicial | STARTED |
| Guardar adjuntos | true |

| Metadato | Valor |
|---|---|
| Activo | true |
| Ultima modificacion | 2026-05-17 23:08 UTC (Europe/Paris) |
| userId | 1 |

## Descripcion

Example channel. Receives HL7 v2 ADT messages via TCP/MLLP, 
filters by event type and maps patient demographics to channel variables. 
Demonstrates: MLLP source, HL7 filter with AND/OR operators, 
demographic transformer, and conditional multi-destination routing.

## Configuracion

| Campo | Valor |
|---|---|
| **Source** | TCP Listener (MLLP/HL7) |
| **Inbound** | HL7V2 |
| **Outbound** | HL7V2 |
| **Version Mirth** | 4.5.2 |
| **Destinations** | 2 |

## Configuracion TCP Listener (MLLP/HL7)

| Parametro | Valor |
|---|---|
| Modo transmision | MLLP |
| MLLP v2 | false |
| Max conexiones | 10 |
| Mantener conexion | true |
| Datos binarios | false |
| Codificacion | DEFAULT_ENCODING |
| Responder en nueva conexion | 0 |

## Destinations

| Nombre          | Tipo              | Inbound | Outbound | Activo | Espera ant. |
| --------------- | ----------------- | ------- | -------- | ------ | ----------- |
| RegisterPatient | JavaScript Writer | HL7V2   | HL7V2    | ✓      | ✓           |
| RecordAdmission | JavaScript Writer | HL7V2   | HL7V2    | ✓      | ✓           |

## Scripts — Canal

### Preprocessor

```javascript
// Modify the message variable below to pre process data
return message;
```

### Postprocessor

```javascript
// This script executes once after a message has been processed
// Responses returned from here will be stored as "Postprocessor" in the response map
return;
```

### Deploy

```javascript
// This script executes once when the channel is deployed
// You only have access to the globalMap and globalChannelMap here to persist data
return;
```

### Undeploy

```javascript
// This script executes once when the channel is undeployed
// You only have access to the globalMap and globalChannelMap here to persist data
return;
```

## Scripts — Source

### Filter: Accept ADT messages only

```javascript
return msg['MSH']['MSH.9']['MSG.1'].toString() === 'ADT';
```

### Filter `[OR]`: Accept supported event types

```javascript
// Rule 2 — OR
var eventType = msg['MSH']['MSH.9']['MSG.2'].toString();
var supported = ['A01', 'A04', 'A08', 'A28', 'A31'];
return supported.indexOf(eventType) >= 0;
```

### Transformer: JavaScriptStep

```javascript
// Step 1 — Extract patient ID
var nhc = msg['PID']['PID.3']['CX.1'].toString();
channelMap.put('nhc', nhc);

// Step 2 — Extract patient name
var lastName  = msg['PID']['PID.5']['XPN.1'].toString();
var firstName = msg['PID']['PID.5']['XPN.2'].toString();
channelMap.put('lastName', lastName);
channelMap.put('firstName', firstName);

// Step 3 — Extract event type
var eventType = msg['MSH']['MSH.9']['MSG.2'].toString();
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
// Update patient demographics in database
var sql    = 'UPDATE PATIENTS SET FIRST_NAME=?, LAST_NAME=? WHERE PATIENT_ID=?';
var params = java.util.Arrays.asList($('firstName'), $('lastName'), $('nhc'));
var dbConn = DatabaseConnectionFactory.createDatabaseConnection(
    'oracle.jdbc.OracleDriver',
    configurationMap.get('DB_URL'),
    configurationMap.get('DB_USER'),
    configurationMap.get('DB_PASS')
);
var result = dbConn.executeUpdate(sql, params);
dbConn.close();

logger.info('Patient updated: ' + $('nhc') + ' rows=' + result);
```

## Scripts — RecordAdmission (JavaScript Writer)

### Filter: Only A01/A04

```javascript
var ev = $('eventType');
return ['A01', 'A04'].indexOf(ev) >= 0;
```

### JavaScript Writer Script

```javascript
// Insert admission record
var sql    = 'INSERT INTO ADMISSIONS (PATIENT_ID, EVENT_TYPE, TIMESTAMP) VALUES (?, ?, SYSDATE)';
var params = java.util.Arrays.asList($('nhc'), $('eventType'));
var dbConn = DatabaseConnectionFactory.createDatabaseConnection(
    'oracle.jdbc.OracleDriver',
    configurationMap.get('DB_URL'),
    configurationMap.get('DB_USER'),
    configurationMap.get('DB_PASS')
);
dbConn.executeUpdate(sql, params);
dbConn.close();
```

---
**Codigo JS:** `S:\Mirth\mirth-channels-repo\TCP_ADT-DB`