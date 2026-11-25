require('dotenv').config();
const express = require('express');
const { processPreauth } = require('./orchestrator');

const app = express();
app.use(express.json());

app.post('/preauth/:id/process', async (req, res) => {
  try{
    const id = req.params.id;
    const result = await processPreauth(id);
    res.json({ ok: true, result });
  }catch(e){
    console.error(e);
    res.status(500).json({ ok: false, error: e.message });
  }
});

const port = process.env.PORT || 3000;
if (require.main === module){
  app.listen(port, ()=> console.log('Server listening on', port));
}

module.exports = app;
