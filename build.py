"""Inline demo-data.js into the page so the demo is one file you can email."""
html = open("payout-review.html", encoding="utf-8").read()
data = open("demo-data.js", encoding="utf-8").read()

tag = '<script src="demo-data.js"></script>'
if tag not in html:
    raise SystemExit("demo-data.js tag not found in the page")

html = html.replace(tag, "<script>\n" + data + "\n</script>")
out = "Payout-Review-DEMO.html"
open(out, "w", encoding="utf-8").write(html)
print("written:", out, len(html), "characters")
