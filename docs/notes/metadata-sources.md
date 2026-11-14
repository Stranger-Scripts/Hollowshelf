# Metadata sources: evaluation (2026-11-14)

The record behind **D-016**, so the same research doesn't have to be redone.
Requirements live in [URS.md](../URS.md) §6.3. This page explains *why* each source is in or out.

## In scope for v1.0

| Source | Access | Why | URS |
|--------|--------|-----|-----|
| Open Library | Keyless | Primary source, good DE/EN coverage, covers | LKP-001 |
| Google Books | Keyless (optional key raises the quota) | Strong descriptions and page counts | LKP-001 |
| ISFDB | Keyless, ISBN → XML (`getpub.cgi`) | Deep speculative-fiction data: series, editions, cover artists. *Data licence still to be confirmed.* | LKP-015 |
| Hardcover | Free personal API token, about 5,000 req/day and 60/min | Series and editions; opt-in | LKP-011 |

## Maybe later: scraper-type sources (Parking Lot)

These have no usable API for this project, so they'd need HTML scraping. Promoting one needs a decision that covers terms of service, breakage risk and maintenance cost.

| Source | Situation |
|--------|-----------|
| Amazon | PA-API v5 was retired on 15 May 2026. The Creators API needs an Associates account with ≥ 10 qualified sales in the last 30 days. |
| Goodreads | No new API keys since Dec 2020. Data import is possible via a CSV export (PORT-002). |
| Kobo | No public catalog API found |
| Moly (moly.hu) | Hungarian community site with no public API. Calibre's `Moly_hu` plugin scrapes it. |
| Biblio | biblio.com only offers an affiliate program; Biblio.bg (Bulgarian store) has no API |

## Out of scope for now

| Source | Access | Reason |
|--------|--------|--------|
| ISBNdb | Paid only (about $14.99/month and up, 7-day trial) | NG-10: no paid APIs |
| WorldCat | OCLC key, only for member libraries and individuals sanctioned by them | NG-10: needs an institutional account |
| Apple Books / iTunes Search API | Keyless, ebook and audiobook media types | Removed for now. ISBN lookup reportedly unreliable since about 09/2024, and the terms frame the data as store promotion. |
| Libris (Swedish union catalog) | Keyless (unverified; docs blocked during research) | Removed for now; Swedish focus |
| data.bnf.fr / BnF SRU | Keyless SPARQL endpoint, Licence Ouverte | Removed for now; French focus |
| DNB (Deutsche Nationalbibliothek) SRU | Keyless, MARC21-xml | Removed for now. The strongest candidate if German-edition coverage turns out to be thin. |
| ISBNPlus | No current documentation or API found | Treated as defunct |

## References

- ISFDB Web API: https://isfdb.org/wiki/index.php/Web_API
- Hardcover token: https://booklore-app.github.io/booklore-docs/docs/metadata/hardcover-token
- Amazon PA-API retirement: https://blog.freshstore.com/amazon-creators-api-pa-api-retirement/
- Goodreads keys: https://www.goodreads.com/topic/show/22303603-developer-keys
- OCLC WSKey eligibility: https://help.oclc.org/Librarian_Toolbox/OCLC_APIs/Troubleshooting/Can_students_non-library_staff_and_professors_use_WSKeys
- Books API overview (ISBNdb, Hardcover limits): https://api.market/blog/skycraft/books-api/best-books-api
- iTunes Search API: https://performance-partners.apple.com/resources/documentation/itunes-store-web-service-search-api/
- data.bnf.fr SPARQL: https://api.bnf.fr/fr/sparql-endpoint-de-databnffr
- DNB interfaces: https://www.dnb.de/librarylabapi
