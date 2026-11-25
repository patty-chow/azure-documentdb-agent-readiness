const { connect } = require('./db');
const Order = require('./models/order');
const Return = require('./models/return');
const { policyAgent, refundAgent, commsAgent } = require('./llm');

async function processReturn({ orderId, reason, requester }) {
  await connect();
  const order = await Order.findOne({ orderId }).lean();
  if (!order) throw new Error('order_not_found');

  const returnDoc = {
    orderId,
    status: 'error',
    refundAmount: 0,
    reason,
    requester,
    policyResult: null,
    refundResult: null,
    commsResult: null
  };

  try {
    const policyResult = await policyAgent(order, reason);
    returnDoc.policyResult = policyResult;

    if (!policyResult || !policyResult.eligible) {
      returnDoc.status = 'rejected';
      returnDoc.refundAmount = 0;
      const refundResult = { amount: 0, breakdown: [] };
      returnDoc.refundResult = refundResult;
      const commsResult = await commsAgent(order, { amount: 0, reason: 'not eligible' });
      returnDoc.commsResult = commsResult;
    } else {
      const refundResult = await refundAgent(order, policyResult);
      returnDoc.refundResult = refundResult;
      returnDoc.refundAmount = refundResult.amount || 0;
      returnDoc.status = returnDoc.refundAmount > 0 ? 'approved' : 'rejected';
      const commsResult = await commsAgent(order, refundResult);
      returnDoc.commsResult = commsResult;
    }
  } catch (err) {
    returnDoc.status = 'error';
    returnDoc.error = { message: err.message, stack: err.stack };
  }

  const saved = await Return.create(returnDoc);
  return saved.toObject();
}

module.exports = { processReturn };
