require('dotenv').config();
const express = require('express');
const { run } = require('./run');
const app = express();
app.get('/run', async (req,res)=>{
  try{
    await run();
    res.json({ status: 'ok' });
  }catch(e){
    res.status(500).json({ error: String(e) });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, ()=>console.log('Server listening on', port));
