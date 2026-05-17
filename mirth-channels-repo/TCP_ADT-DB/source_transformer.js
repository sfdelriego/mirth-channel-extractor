// Step: JavaScriptStep
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