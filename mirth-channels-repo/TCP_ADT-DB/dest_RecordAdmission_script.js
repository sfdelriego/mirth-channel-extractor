// Script: JavaScript Writer Script
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