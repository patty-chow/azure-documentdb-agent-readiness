const { processPreauth } = require('../src/orchestrator');

// Mock db and agents
jest.mock('../src/db', ()=>({
  getDb: jest.fn()
}));
jest.mock('../src/agents/medicalReviewAgent', ()=>({ medicalReview: jest.fn() }));
jest.mock('../src/agents/insurerCommsAgent', ()=>({ draftSubmission: jest.fn() }));

const { getDb } = require('../src/db');
const { medicalReview } = require('../src/agents/medicalReviewAgent');
const { draftSubmission } = require('../src/agents/insurerCommsAgent');

describe('processPreauth', ()=>{
  beforeEach(()=>{
    jest.resetAllMocks();
  });

  it('processes a preauth and stores submission', async ()=>{
    const fakePreauth = { _id: 'preauth-test', patientId: 'patient-x', clinician: 'Dr Test', requestedProcedureCodes: ['PROC-100'], clinicalNotes: 'Notes' };
    const inserted = [];
    const updated = [];

    const collections = {
      preauth_requests: { findOne: jest.fn().mockResolvedValue(fakePreauth), updateOne: jest.fn((q,u)=>{ updated.push({q,u}); return Promise.resolve(); }) },
      submissions: { insertOne: jest.fn((doc)=>{ inserted.push(doc); return Promise.resolve({ insertedId: 'sub-1' }); }) }
    };

    getDb.mockResolvedValue({ collection: (name)=>collections[name] });
    medicalReview.mockResolvedValue({ necessary: true, reasons: ['ok'], confidence: 0.9 });
    draftSubmission.mockResolvedValue('LETTER TEXT');

    const res = await processPreauth('preauth-test');
    expect(res.preauthId).toBe('preauth-test');
    expect(inserted.length).toBe(1);
    expect(updated.length).toBe(1);
  });

  it('throws if preauth not found', async ()=>{
    const collections = { preauth_requests: { findOne: jest.fn().mockResolvedValue(null) } };
    getDb.mockResolvedValue({ collection: (name)=>collections[name] });
    await expect(processPreauth('nope')).rejects.toThrow('Preauth not found');
  });
});
