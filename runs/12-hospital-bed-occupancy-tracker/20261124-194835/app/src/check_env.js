require('dotenv').config();
console.log('DOCUMENTDB_URI set:', !!process.env.DOCUMENTDB_URI);
console.log('DB_NAME:', process.env.DB_NAME || 'sample_healthcare_12');
console.log('CLEANING_TTL_SECONDS:', process.env.CLEANING_TTL_SECONDS || '300');
