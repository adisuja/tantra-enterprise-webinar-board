// Shared by the browser and the server.
// parseScript: script text -> blocks the prompter renders.
// parseImport: raw text from a file or link -> { title, text } in script format.
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.TPImport = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // Script format:
  //   # Heading  or  **Heading** on its own line   a section you can jump to from the remote
  //   blank line                                   starts a new paragraph
  //   [stage note]                                 shown in a different colour, not read out
  //   **Post in chat:** text                       a labelled paragraph becomes a stage note
  //   | Question | Answer |                         a table: each row becomes [first cell] then the rest
  function stripMd(t) {
    return t.replace(/\*\*(.+?)\*\*/g, '$1').replace(/__(.+?)__/g, '$1').replace(/(^|[\s(])\*([^*\s][^*]*?)\*(?=[\s).,!?]|$)/g, '$1$2');
  }
  function parseScript(text) {
    const blocks = [];
    const lines = String(text || '').replace(/\r\n?/g, '\n').split('\n');
    let buf = [];
    let table = [];
    const flush = () => {
      let t = buf.join('\n').trim();
      buf = [];
      if (!t) return;
      const label = t.match(/^\*\*([^*\n]{1,40}?:)\*\*\s*([\s\S]*)$/) || t.match(/^\*\*([^*\n]{1,40}?)\*\*:\s*([\s\S]*)$/);
      if (label) t = `[${label[1].replace(/:$/, '')}: ${stripMd(label[2]).replace(/[\[\]]/g, '')}]`;
      blocks.push({ type: 'p', text: stripMd(t) });
    };
    const cells = (l) => l.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((c) => stripMd(c.trim()));
    const flushTable = () => {
      if (!table.length) return;
      const rows = table.filter((l) => !/^\s*\|?\s*:?-{2,}/.test(l.replace(/\|/g, ' ').trim() ? l : '')).filter((l) => !/^[\s|:-]+$/.test(l)).map(cells);
      table = [];
      if (!rows.length) return;
      const header = rows.length > 1 ? rows.shift() : null;
      if (header) blocks.push({ type: 'h', text: header.filter(Boolean).join(' / ') });
      for (const r of rows) {
        const c = r.filter((x) => x !== '');
        if (!c.length) continue;
        blocks.push({ type: 'p', text: c.length > 1 ? `[${c[0]}]\n${c.slice(1).join('\n')}` : c[0] });
      }
    };
    for (const line of lines) {
      if (/^\s*\|/.test(line)) { flush(); table.push(line); continue; }
      flushTable();
      const h = line.match(/^\s*#{1,6}\s+(.*)$/) || line.match(/^\s*\*\*([^*]+?)\*\*\s*$/);
      if (h) { flush(); blocks.push({ type: 'h', text: stripMd(h[1].trim()) }); continue; }
      if (/^\s*(-{3,}|\*{3,})\s*$/.test(line)) { flush(); continue; }
      if (!line.trim()) { flush(); continue; }
      buf.push(line);
    }
    flush();
    flushTable();
    return blocks;
  }

  function decodeEntities(s) {
    return String(s)
      .replace(/&nbsp;/g, ' ')
      .replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)))
      .replace(/&#x([0-9a-f]+);/gi, (_, n) => String.fromCodePoint(parseInt(n, 16)))
      .replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'")
      .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
  }

  function htmlToParagraphs(html) {
    return decodeEntities(
      String(html)
        .replace(/<(script|style|noscript)[\s\S]*?<\/\1>/gi, '')
        .replace(/<br\s*\/?>/gi, '\n')
        .replace(/<\/(p|div|li|h[1-6]|section|tr)>/gi, '\n\n')
        .replace(/<[^>]+>/g, '')
    ).replace(/[ \t]+/g, ' ').replace(/\n[ \t]+/g, '\n').replace(/\n{3,}/g, '\n\n').trim();
  }

  // The webinar deck: each <section data-n data-title> carries <div class="notes">.
  function parseDeck(html) {
    const out = [];
    const re = /<section\b([^>]*)>([\s\S]*?)<\/section>/gi;
    let m;
    while ((m = re.exec(html))) {
      const attrs = m[1];
      const notes = m[2].match(/<div class="notes"[^>]*>([\s\S]*?)<\/div>/i);
      if (!notes) continue;
      const n = (attrs.match(/data-n="([^"]*)"/) || [])[1] || String(out.length + 1);
      const title = decodeEntities((attrs.match(/data-title="([^"]*)"/) || [])[1] || '');
      const paras = [...notes[1].matchAll(/<p>([\s\S]*?)<\/p>/gi)].map((p) => htmlToParagraphs(p[1])).filter(Boolean);
      if (!paras.length) continue;
      // The first notes paragraph is the minute and chat cue: keep it as a stage note.
      if (/^Minute\b/.test(paras[0])) paras[0] = `[${paras[0]}]`;
      out.push(`# Slide ${n}${title ? ': ' + title : ''}\n\n${paras.join('\n\n')}`);
    }
    return out.join('\n\n');
  }

  function parseImport(raw, opts) {
    opts = opts || {};
    const text = String(raw || '').replace(/^﻿/, '');
    const name = opts.filename || opts.url || '';
    const looksHtml = /<html|<body|<section|<div|<p[\s>]/i.test(text.slice(0, 5000));
    if (looksHtml && /class="notes"/.test(text)) {
      const titleTag = (text.match(/<title>([\s\S]*?)<\/title>/i) || [])[1];
      return { title: 'Deck notes: ' + (titleTag ? decodeEntities(titleTag).trim() : 'webinar deck'), text: parseDeck(text), source: 'deck' };
    }
    if (looksHtml) {
      const titleTag = (text.match(/<title>([\s\S]*?)<\/title>/i) || [])[1];
      return { title: titleTag ? decodeEntities(titleTag).trim() : guessTitle(name), text: htmlToParagraphs(text), source: 'html' };
    }
    // plain text or markdown, including a Google Doc exported as text
    let body = text.replace(/\r\n?/g, '\n');
    let title = guessTitle(name);
    const firstLine = body.split('\n').find((l) => l.trim());
    if (opts.isGoogleDoc && firstLine && firstLine.length < 120) title = firstLine.replace(/^#+\s*/, '').trim();
    return { title, text: body.trim(), source: 'text' };
  }

  function guessTitle(name) {
    const base = String(name || '').split(/[?#]/)[0].split('/').filter(Boolean).pop() || 'Imported script';
    return decodeURIComponent(base).replace(/\.(txt|md|markdown|html?)$/i, '').replace(/[-_]+/g, ' ').trim() || 'Imported script';
  }

  return { parseScript, parseImport, parseDeck };
});
