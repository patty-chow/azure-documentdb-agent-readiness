const { getDb, clientPromise } = require('./client');

async function seed() {
  await clientPromise;
  const db = getDb();
  const segments = db.collection('segments');
  const campaigns = db.collection('campaigns');

  const docs = [
    {
      segmentId: 'seg-1',
      name: 'Frequent Buyers - Home Goods',
      purchase_history: [
        { sku: 'HG-101', name: 'Ceramic Vase', price: 29.99, purchasedAt: '2024-09-10' },
        { sku: 'HG-202', name: 'Throw Pillow', price: 19.5, purchasedAt: '2024-08-22' }
      ],
      preferences: { categories: ['home','decor'], tone: 'warm', discountSensitivity: 'medium' }
    },
    {
      segmentId: 'seg-2',
      name: 'Bargain Hunters',
      purchase_history: [
        { sku: 'ELEC-33', name: 'Bluetooth Earbuds', price: 49.99, purchasedAt: '2024-07-02' }
      ],
      preferences: { categories: ['electronics','accessories'], tone: 'upbeat', discountSensitivity: 'high' }
    }
  ];

  for (const doc of docs) {
    await segments.replaceOne({ segmentId: doc.segmentId }, doc, { upsert: true });
  }

  // Create indexes: segments.segmentId unique; campaigns.segmentId
  await segments.createIndex({ segmentId: 1 }, { unique: true, name: 'idx_segmentId' });
  await campaigns.createIndex({ segmentId: 1 }, { name: 'idx_campaigns_segmentId' });

  console.log('Seeding complete. Segments upserted and indexes created.');
  process.exit(0);
}

seed().catch(err => {
  console.error(err);
  process.exit(1);
});
