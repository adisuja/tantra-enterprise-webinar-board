"""Fetch Google Docs (all tabs) as plain text via the local OAuth token. usage: python3 fetch_docs.py OUTDIR ID..."""
import json, sys, pathlib, ssl, urllib.request, urllib.parse, certifi
TOK = pathlib.Path.home() / 'CEO/.secrets/token.json'
CTX = ssl.create_default_context(cafile=certifi.where())
def token():
    t = json.loads(TOK.read_text())
    data = urllib.parse.urlencode({'client_id': t['client_id'], 'client_secret': t['client_secret'], 'refresh_token': t['refresh_token'], 'grant_type': 'refresh_token'}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request(t.get('token_uri', 'https://oauth2.googleapis.com/token'), data=data), context=CTX))
    return r['access_token']
def text_of(content):
    out = []
    for el in content:
        if 'paragraph' in el:
            p = el['paragraph']; s = ''.join(e.get('textRun', {}).get('content', '') for e in p.get('elements', []))
            st = p.get('paragraphStyle', {}).get('namedStyleType', '')
            if st.startswith('HEADING_') and s.strip(): s = '#' * int(st[-1]) + ' ' + s
            elif st == 'TITLE' and s.strip(): s = '# ' + s
            if 'bullet' in p: s = '- ' + s
            out.append(s)
        elif 'table' in el:
            for row in el['table']['tableRows']:
                cells = [text_of(c['content']).strip().replace('\n', ' / ') for c in row['tableCells']]
                out.append('| ' + ' | '.join(cells) + ' |\n')
    return ''.join(out)
def walk(tabs, depth=0):
    for tb in tabs:
        props = tb['tabProperties']
        yield depth, props.get('title', ''), props.get('tabId'), text_of(tb.get('documentTab', {}).get('body', {}).get('content', []))
        yield from walk(tb.get('childTabs', []), depth + 1)
def main():
  out = pathlib.Path(sys.argv[1]); at = token()
  for did in sys.argv[2:]:
      req = urllib.request.Request(f'https://docs.googleapis.com/v1/documents/{did}?includeTabsContent=true', headers={'Authorization': 'Bearer ' + at})
      try: d = json.load(urllib.request.urlopen(req, context=CTX))
      except Exception as e: print(did, 'ERROR', e); continue
      parts = [f'@@DOC {d["title"]}\n']
      for depth, title, tid, txt in walk(d.get('tabs', [])):
          parts.append(f'\n@@TAB {"  " * depth}{title} ({tid})\n{txt}')
      (out / f'{did}.txt').write_text(''.join(parts))
      print(did, d['title'], len(''.join(parts)), 'chars', sum(1 for _ in walk(d.get('tabs', []))), 'tabs')

if __name__ == '__main__':
    main()
