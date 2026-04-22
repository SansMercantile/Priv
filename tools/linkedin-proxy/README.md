LinkedIn Proxy (dev)

This is a small Express proxy to call LinkedIn APIs server-side to avoid exposing your secret keys in client JS.

Setup

1. Install dependencies:

   npm install express node-fetch

2. Set environment variable with your LinkedIn bearer token:

   export LINKEDIN_BEARER_TOKEN="YOUR_TOKEN"

3. Run the server:

   node server.js

4. The feed endpoint will be available at `http://localhost:3030/feed` (adjust as needed).

Security

This proxy is for local development only. Do not deploy it without proper auth and rate limiting. Keep the token secret.
