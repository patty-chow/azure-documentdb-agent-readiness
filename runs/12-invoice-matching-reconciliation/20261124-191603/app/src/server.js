import express from 'express';
import dotenv from 'dotenv';
import bodyParser from 'body-parser';
import { connect, disconnect } from './db.js';
import { runReconcile } from './reconciler.js';
import Invoice from './models/invoice.js';

dotenv.config();

const app = express();
app.use(bodyParser.json());

// Simple in-memory session corrections store
const sessionCorrections = new Map();
let lastRun = null;

app.post('/reconcile/run', async (req,res)=>{
  try{
    const results = await runReconcile({ useLLM: !!process.env.OPENAI_API_KEY, limit: req.body?.limit || 50 });
    lastRun = { when: new Date(), results };
    res.json({ ok: true, results });
  }catch(e){
    res.status(500).json({ ok:false, error: e.message });
  }
});

app.post('/reconcile/manual-correction', async (req,res)=>{
  const { invoiceId, matchedPoId } = req.body || {};
  if (!invoiceId || !matchedPoId) return res.status(400).json({ ok:false, error:'invoiceId and matchedPoId required' });
  try{
    const inv = await Invoice.findById(invoiceId);
    if (!inv) return res.status(404).json({ ok:false, error:'invoice not found' });
    inv.matchedPoId = matchedPoId;
    inv.status = 'matched';
    inv.matchedAt = new Date();
    inv.matchScore = 1.0;
    inv.matchDetails = { manualCorrection: true };
    await inv.save();
    // store in session memory
    sessionCorrections.set(invoiceId, { matchedPoId, at: new Date() });
    res.json({ ok:true });
  }catch(e){
    res.status(500).json({ ok:false, error: e.message });
  }
});

app.get('/reconcile/status', async (req,res)=>{
  res.json({ ok:true, lastRun, sessionCorrections: Array.from(sessionCorrections.entries()) });
});

const port = process.env.PORT || 3000;

connect().then(()=>{
  app.listen(port, ()=> console.log(`Server listening on ${port}`));
}).catch(err=>{ console.error('Failed to connect to DB:', err); process.exit(1); });

process.on('SIGINT', async ()=>{ await disconnect(); process.exit(0); });
