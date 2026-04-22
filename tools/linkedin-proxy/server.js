// Simple LinkedIn proxy (dev only).
// Usage: set LINKEDIN_BEARER_TOKEN env var and run `node server.js`.
const express = require('express');
const fetch = require('node-fetch');
const app = express();
const PORT = process.env.PORT || 3030;

app.get('/feed', async (req, res) => {
  try {
    const token = process.env.LINKEDIN_BEARER_TOKEN;
    if(!token) return res.status(500).json({ error: 'Missing LINKEDIN_BEARER_TOKEN' });
    // Example LinkedIn v2 API call (developer to adapt)
    const response = await fetch('https://api.linkedin.com/v2/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    res.json({ data });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.listen(PORT, () => console.log(`LinkedIn proxy listening on http://localhost:${PORT}`));
