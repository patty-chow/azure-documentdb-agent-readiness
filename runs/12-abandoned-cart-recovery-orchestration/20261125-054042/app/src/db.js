import { MongoClient } from "mongodb";
import dotenv from "dotenv";
dotenv.config();

const uri = process.env.DOCUMENTDB_URI;
if (!uri) {
  throw new Error('DOCUMENTDB_URI environment variable is required');
}

let client;
let db;

export async function getClient() {
  if (!client) {
    client = new MongoClient(uri, { family: 4 });
    await client.connect();
  }
  return client;
}

export async function getDb() {
  if (!db) {
    const c = await getClient();
    db = c.db('sample_retail_12');
  }
  return db;
}

export async function closeClient() {
  if (client) {
    await client.close();
    client = undefined;
    db = undefined;
  }
}
