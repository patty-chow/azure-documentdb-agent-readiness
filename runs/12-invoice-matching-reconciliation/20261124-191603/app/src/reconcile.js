const Invoice = require('./models/invoice');
const PurchaseOrder = require('./models/po');
const agent = require('./agent');

async function findCandidatesByInvoice(extracted) {
  const { vendorName, totalAmount } = extracted;
  if (!vendorName && !totalAmount) return [];

  const query = {};
  if (vendorName) query.vendorName = { $regex: `^${escapeRegExp(vendorName)}`, $options: 'i' };
  if (totalAmount) {
    // within +/- 2% tolerance
    const tol = Math.max(1, Math.abs(totalAmount) * 0.02);
    query.totalAmount = { $gte: totalAmount - tol, $lte: totalAmount + tol };
  }

  const candidates = await PurchaseOrder.find(query).limit(50).lean();
  return candidates;
}

function scoreCandidate(extracted, candidate) {
  let score = 0;
  if (extracted.vendorName && candidate.vendorName && extracted.vendorName.toLowerCase() === candidate.vendorName.toLowerCase()) score += 60;
  const a = extracted.totalAmount || 0;
  const b = candidate.totalAmount || 0;
  const diff = Math.abs(a - b);
  const pct = a ? diff / Math.abs(a) : 1;
  score += Math.max(0, 40 - Math.min(40, pct * 100));
  return score;
}

function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

async function reconcileAll(sessionId) {
  const invoices = await Invoice.find({ status: 'unmatched' }).limit(200);
  const session = agent.getSession(sessionId);
  const results = [];
  for (const inv of invoices) {
    // check session corrections first
    if (session.corrections && session.corrections[inv.invoiceNumber]) {
      const poNumber = session.corrections[inv.invoiceNumber];
      const po = await PurchaseOrder.findOne({ poNumber }).lean();
      if (po) {
        inv.matchedPoId = po._id;
        inv.matchScore = 100;
        inv.matchDetails = { forcedBy: 'manual-correction', matchedPoNumber: poNumber };
        inv.status = 'matched';
        inv.matchedAt = new Date();
        await inv.save();
        results.push({ invoice: inv.invoiceNumber, matched: poNumber, score: 100, details: inv.matchDetails });
        continue;
      }
    }

    const extracted = await agent.extractInvoiceFields(inv.rawText || inv.invoiceNumber || '');
    const candidates = await findCandidatesByInvoice(extracted);
    let best = null;
    let bestScore = 0;
    for (const c of candidates) {
      const s = scoreCandidate(extracted, c);
      if (s > bestScore) { bestScore = s; best = c; }
    }
    if (best && bestScore >= 50) {
      inv.matchedPoId = best._id;
      inv.matchScore = bestScore;
      inv.matchDetails = { vendorMatched: best.vendorName, poNumber: best.poNumber };
      inv.status = 'matched';
      inv.matchedAt = new Date();
      await inv.save();
      results.push({ invoice: inv.invoiceNumber, matched: best.poNumber, score: bestScore });
    } else {
      results.push({ invoice: inv.invoiceNumber, matched: null, score: bestScore });
    }
  }
  return results;
}

module.exports = { reconcileAll };
