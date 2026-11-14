#!/usr/bin/env node
// Tantra Teleprompter on Node: node server.js
// Serves the app and runs the shared core (core.js). Scripts and room state are saved in ./data.
'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { Readable } = require('stream');
const { createCore } = require('./core.js');

const PORT = Number(process.env.PORT || 4400);
const HOST = process.env.HOST || '0.0.0.0';
const DATA_DIR = process.env.TP_DATA_DIR || path.join(__dirname, 'data');
const PUBLIC_DIR = path.join(__dirname, 'public');
fs.mkdirSync(DATA_DIR, { recursive: true });

const SESSIONS_FILE = path.join(DATA_DIR, 'sessions.json');
let saveTimer = null;
const store = {
  sessions: (() => { try { return JSON.parse(fs.readFileSync(SESSIONS_FILE, 'utf8')); } catch { return {}; } })(),
  save() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
      fs.writeFileSync(SESSIONS_FILE + '.tmp', JSON.stringify(store.sessions));
      fs.renameSync(SESSIONS_FILE + '.tmp', SESSIONS_FILE);
    }, 300);
  },
};

function lanAddresses() {
  const out = [];
  for (const list of Object.values(os.networkInterfaces())) for (const a of list || []) {
    if (a.family === 'IPv4' && !a.internal) out.push(a.address);
  }
  return out;
}

const core = createCore(store, { lan: lanAddresses, port: PORT });

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon', '.woff2': 'font/woff2', '.webmanifest': 'application/manifest+json',
};
const PRETTY = { '/': '/index.html', '/prompter': '/prompter.html', '/remote': '/remote.html', '/scripts': '/scripts.html' };

function serveStatic(req, res, pathname) {
  let p = decodeURIComponent(pathname);
  if (PRETTY[p]) p = PRETTY[p];
  const file = path.normalize(path.join(PUBLIC_DIR, p));
  if (!file.startsWith(PUBLIC_DIR)) { res.writeHead(403); return res.end(); }
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404, { 'content-type': 'text/plain' }); return res.end('Not found'); }
    res.writeHead(200, { 'content-type': MIME[path.extname(file)] || 'application/octet-stream', 'cache-control': 'no-cache' });
    res.end(data);
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  if (!url.pathname.startsWith('/api/')) {
    if (req.method !== 'GET' && req.method !== 'HEAD') { res.writeHead(405); return res.end(); }
    return serveStatic(req, res, url.pathname);
  }
  const abort = new AbortController();
  res.on('close', () => abort.abort());
  const hasBody = req.method !== 'GET' && req.method !== 'HEAD';
  const request = new Request(url, {
    method: req.method,
    headers: Object.entries(req.headers).filter(([, v]) => typeof v === 'string'),
    body: hasBody ? Readable.toWeb(req) : undefined,
    duplex: hasBody ? 'half' : undefined,
    signal: abort.signal,
  });
  const response = await core.fetch(request);
  res.writeHead(response.status, Object.fromEntries(response.headers));
  if (!response.body) return res.end();
  const reader = response.body.getReader();
  res.on('close', () => reader.cancel().catch(() => {}));
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      res.write(value);
    }
  } catch {}
  res.end();
});
server.keepAliveTimeout = 65000;
server.requestTimeout = 0; // event streams stay open
server.listen(PORT, HOST, () => {
  console.log('\nTantra Teleprompter is running.\n');
  console.log(`  On this computer:  http://localhost:${PORT}`);
  for (const ip of lanAddresses()) console.log(`  On your phones:    http://${ip}:${PORT}`);
  console.log('\nOpen that address on both phones (same Wi-Fi). Leave this window open while you present.\n');
});
