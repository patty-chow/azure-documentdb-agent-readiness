/*
  db.js

  Purpose:
  - Provide a singleton MongoClient instance for the app.
  - Export helper functions to get the sample database and named collections.

  Usage:
  const { getDb, getCollection } = require('./db');
*/

const { MongoClient } = require('mongodb');
const dotenv = require('dotenv');
dotenv.config();

// Read connection string from environment. Do not store secrets in files.
const DOCUMENTDB_URI = process.env.DOCUMENTDB_URI;
if (!DOCUMENTDB_URI) {
  console.error('ERROR: DOCUMENTDB_URI is not set. Copy .env.example to .env and set DOCUMENTDB_URI');
  process.exit(1);
}

// Database name used by this sample (explicit requirement).
const DB_NAME = 'sample_retail_02';

// Singleton client variable following documentdb-driver guidance.
let client;

/**
 * Initialize and return the MongoClient singleton.
 * This function ensures the client is created once per process.
 */
async function getClient() {
  if (client) return client;
  client = new MongoClient(DOCUMENTDB_URI, {
    // sensible defaults; allow users to override via connection string
    maxPoolSize: 10
  });
  await client.connect();
  return client;
}

/**
 * Get the sample database object. Ensures the client is connected.
 */
async function getDb() {
  const c = await getClient();
  return c.db(DB_NAME);
}

/**
 * Convenience: get a collection handle in the sample database.
 * @param {string} name
 */
async function getCollection(name) {
  const db = await getDb();
  return db.collection(name);
}

module.exports = { getClient, getDb, getCollection };
