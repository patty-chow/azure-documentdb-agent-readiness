import Invoice from './models/invoice.js';
import PurchaseOrder from './models/purchaseOrder.js';
import { extractFieldsLLM, extractFieldsFallback, embedText } from './llm.js';

function normalizeVendor(v) {
  if (!v) return '';
  return v.toLowerCase().replace(/[^a-z0-9]/g, '').trim();
}

function vendorScore(v1, v2) {
  const n1 = normalizeVendor(v1);
  const n2 = normalizeVendor(v2);
  if (!n1 || !n2) return 0.1;
  if (n1 === n2) return 1.0;
  if (n1.includes(n2) || n2.includes(n1)) return 0.85;
  // partial similarity fallback
  const common = n1.split('').filter(ch => n2.includes(ch)).length;
  return Math.min(0.9, Math.max(0.2, common / Math.max(n1.length, n2.length)));
}

export async function reconcileOne(invoice, useLLM=true) {
  const text = `${invoice.vendorName} ${invoice.invoiceNumber || ''} $${invoice.totalAmount}`;
  let fields;
  if (useLLM) {
    try {
      fields = await extractFieldsLLM(text);
    } catch (e) {
      fields = await extractFieldsFallback(text);
    }
  } else {
    fields = await extractFieldsFallback(text);
  }

  const vendor = fields.vendorName || invoice.vendorName;
  const amount = fields.totalAmount || invoice.totalAmount;

  // Find candidate POs by vendor (case-insensitive) and amount within +/-5%
  const tolerance = 0.05;
  const minAmount = amount * (1 - tolerance);
  const maxAmount = amount * (1 + tolerance);

  const candidates = await PurchaseOrder.find({
    vendorName: { $regex: new RegExp(vendor, 'i') },
    totalAmount: { $gte: minAmount, $lte: maxAmount }
  }).limit(10);

  const scored = [];
  for (const po of candidates) {
    const amtDiff = Math.abs(po.totalAmount - amount);
    const amtScore = 1 / (1 + (amtDiff / Math.max(1, amount)));
    const vScore = vendorScore(vendor, po.vendorName);
    let embScore = 0;
    // Optional: use embeddings if available
    const emb1 = await embedText(`${vendor} ${amount}`);
    const emb2 = await embedText(`${po.vendorName} ${po.totalAmount}`);
    if (emb1 && emb2 && emb1.length === emb2.length) {
      // cosine similarity
      let dot = 0, a2 = 0, b2 = 0;
      for (let i=0;i<emb1.length;i++){ dot += emb1[i]*emb2[i]; a2 += emb1[i]*emb1[i]; b2 += emb2[i]*emb2[i]; }
      embScore = dot / (Math.sqrt(a2)*Math.sqrt(b2) + 1e-12);
    }

    const combined = 0.6 * amtScore + 0.3 * vScore + 0.1 * (embScore || 0);
    scored.push({ po, amtScore, vScore, embScore, combined });
  }

  scored.sort((a,b)=>b.combined - a.combined);
  if (scored.length === 0) {
    return { matched: false, invoiceId: invoice._id };
  }
  const best = scored[0];
  // Apply a threshold
  if (best.combined < 0.4) {
    return { matched: false, invoiceId: invoice._id, candidates: scored.slice(0,5).map(s=>({id:s.po._id, score:s.combined})) };
  }

  // Update invoice
  invoice.matchedPoId = best.po._id;
  invoice.matchScore = best.combined;
  invoice.matchDetails = { amtScore: best.amtScore, vendorScore: best.vScore, embScore: best.embScore };
  invoice.status = 'matched';
  invoice.matchedAt = new Date();
  await invoice.save();

  return { matched: true, invoiceId: invoice._id, poId: best.po._id, score: best.combined };
}

export async function runReconcile({ useLLM=true, limit=20 } = {}) {
  const invoices = await Invoice.find({ status: 'unmatched' }).limit(limit);
  const results = [];
  for (const inv of invoices) {
    const r = await reconcileOne(inv, useLLM);
    results.push(r);
  }
  return results;
}
