import mongoose from "mongoose";
import dotenv from "dotenv";
dotenv.config();

const uri = process.env.DOCUMENTDB_URI;
const dbName = process.env.DB_NAME || 'sample_fintech_12';

if (!uri) {
  console.warn('DOCUMENTDB_URI not set. Tests that require the cluster will fail.');
}

const options = {
  dbName,
  // Keep sensible defaults; pool size can be tuned per documentdb-connection guidance
};

export async function connect() {
  if (!uri) throw new Error('DOCUMENTDB_URI is required in environment');
  await mongoose.connect(uri, options);
}

export async function disconnect() {
  await mongoose.disconnect();
}
