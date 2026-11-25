const request = require('supertest');
const express = require('express');

// We'll mock the model's upsertFromEvent
const mockUpsert = jest.fn().mockResolvedValue({ matched: 1, modified: 1 });

jest.mock('../src/models/customerProfile', () => {
  const Schema = function(){};
  return Schema;
});

// Create a fake model wrapper
const fakeModel = {
  upsertFromEvent: mockUpsert,
};

const eventsRouterFactory = require('../src/routes/events');

let app;
beforeEach(() => {
  app = express();
  app.use(express.json());
  app.use('/events', eventsRouterFactory(fakeModel));
});

test('POST /events validates input and calls upsert', async () => {
  const res = await request(app).post('/events').send({ source: 'crm', customerId: 'cust_001', attributes: { name: 'Test' } });
  expect(res.status).toBe(200);
  expect(res.body.ok).toBe(true);
  expect(mockUpsert).toHaveBeenCalledWith({ source: 'crm', customerId: 'cust_001', attributes: { name: 'Test' } });
});

test('POST /events rejects bad payload', async () => {
  const res = await request(app).post('/events').send({ source: 'crm', attributes: {} });
  expect(res.status).toBe(400);
});
