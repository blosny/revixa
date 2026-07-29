import sys, io
sys.path.insert(0, 'backend')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from google_play_scraper import reviews, Sort

for lang, country in [("tr","tr"), ("en","us"), ("tr","us"), ("en","tr")]:
    result, _ = reviews(
        'com.acabaneyesem',
        lang=lang, country=country,
        sort=Sort.MOST_RELEVANT,
        count=50
    )
    print(f"[{lang.upper()}/{country.upper()}] Ham yorum: {len(result)}")
    for r in result:
        content = r.get("content") or ""
        print(f"  - Puan:{r['score']} | '{content[:70]}'")
    print()
