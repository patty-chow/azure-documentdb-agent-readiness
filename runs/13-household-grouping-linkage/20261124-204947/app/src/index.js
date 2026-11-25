const express = require('express');
const bodyParser = require('body-parser');
const { connect } = require('./db');
const householdsRouter = require('./routes/households');

const PORT = process.env.PORT || 3000;

async function main() {
  await connect();
  const app = express();
  app.use(bodyParser.json());

  app.use('/households', householdsRouter);

  app.get('/', (req, res) => res.json({ ok: true, message: 'DocumentDB household sample' }));

  app.listen(PORT, () => console.log(`Server listening on ${PORT}`));
}

main().catch(err => {
  console.error('Failed to start app', err);
  process.exit(1);
});
