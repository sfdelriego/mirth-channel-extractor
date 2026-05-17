// Script: JavaScript Writer Script
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