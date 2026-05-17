// Rule: Accept ADT messages only
return msg['MSH']['MSH.9']['MSG.1'].toString() === 'ADT';

// ---

// Rule: Accept supported event types
// Rule 2 — OR
var eventType = msg['MSH']['MSH.9']['MSG.2'].toString();
var supported = ['A01', 'A04', 'A08', 'A28', 'A31'];
return supported.indexOf(eventType) >= 0;