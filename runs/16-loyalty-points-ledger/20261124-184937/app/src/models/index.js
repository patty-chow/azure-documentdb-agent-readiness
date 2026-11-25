const mongoose = require('mongoose');
const EventSchema = require('./event');
const Balance = require('./balance');

const Event = mongoose.model('Event', EventSchema);

module.exports = { Event, Balance };
