Tecsaving pages, one batch:
1. python3 mkspecs.py <batch.json> <workdir>
2. python3 build.py <workdir>/specs/*.json --out <workdir>/out
3. serve: mkdir <workdir>/serve; ln -s <workdir>/out <workdir>/serve/tecsaving; cp ~/paginadedicata/site.js <workdir>/serve; python3 -m http.server 8766 --bind 127.0.0.1 (from serve)
4. ~/deck-kit-review/.venv/bin/python og_check.py <workdir>/out   (OG images + overflow + JS errors)
5. copy only <slug>/index.html and assets/og/<slug>.jpg for the batch slugs into ~/paginadedicata/tecsaving, git add those paths only, push.
6. live check 200 + idea line, then write the slug -> URL map next to the batch file.
