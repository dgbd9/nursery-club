# Research guide

This dossier holds the nursery-club project's original research sources and separately labelled working notes. The first backfill was assembled on 24 November 2026 from retained downloads and the identifiable core sources used in the conversation. It is not a complete chat transcript or a reconstruction of every search result.

## Find material

- [Dossier home](../README.md): topic folders and current archive coverage.
- [Source register](Source%20register.md): titles, local originals, readable text, original URLs and the finding each source supports.
- [Source register CSV](source-register.csv): sortable in Excel or other spreadsheet software.
- [Source register JSON](source-register.json): detailed metadata, capture status and checksums.
- [Open questions and evidence gaps](Open%20questions%20and%20evidence%20gaps.md): inaccessible sources and research questions still unresolved.

The main folders are: **01** group/ownership/funding; **02** site dossiers/property; **03** commercial model/marketing; **04** regulatory requirements; **05** comparable operators; **06** our analysis and the user's project brief. Reserved folders may be empty; their README says so.

## Save sources whenever researching

1. Save the core sources actually relied on as part of the research task, before reporting completion. Do not wait for a separate archive request. Search-result snippets alone are not sufficient evidence for precise claims.
2. Prefer original public PDFs, official filings, regulator documents and primary statements. For webpages, save the HTML response and readable text where practical. Do not imply that HTML is a fully bundled offline website or that a present-day capture reproduces its historical version.
3. File once in the most useful topic folder. Company filings belong under the legal entity, with cross-links from site dossiers. Identify entities by company number; record former names. Cross-topic relevance belongs in the register, not duplicate PDFs.
4. Use meaningful filenames. Where a verified date exists, use `YYYY-MM-DD_Publisher_Title.ext`; use a reporting year or an undated descriptive name when that is all that is established. Never invent a publication date from the capture date.
5. Register a stable source ID, title, publisher, original URL, publication/reporting date and its precision, capture date, evidence type, local path, supported finding and relevant pages. Preserve the distinction between publication, filing, reporting-period, adoption, inspection and opening dates.
6. Preserve dated historical versions when content changes materially. Add a new version/entry rather than overwrite evidence relied on previously. Keep the original URL even when it redirects; do not use temporary signed download URLs as the canonical reference.
7. Keep original sources separate from analysis, proposals and assumptions. Label company statements and investor claims as such. Label third-party reporting and attributed submissions appropriately; a council-hosted presentation does not turn every assertion into a council-verified fact.
8. If access fails, log the URL, attempt date and limitation. Do not save a login screen, challenge page or 404 as the requested evidence. If a browser/text fallback is used, state that it is an extract rather than the original downloaded document. Never bypass access controls.
9. Check new files open, verify expected titles/content and PDF validity, update the source register and relevant folder indexes, and record material contradictions or unanswered questions.

Readable `.txt` companions are search aids. OCR can misread digits and names; use the original PDF to verify financial figures and share terms. Cropped page images and temporary extraction files are not part of the main library unless they add necessary evidence.

## Maintaining this backfill

`scripts/research-sources.json` is the explicit catalogue; `scripts/archive_research.py` copies retained downloads or downloads pending public URLs and rebuilds the indexes. It does not crawl websites. Run it from the project root:

```sh
python3 scripts/archive_research.py
python3 scripts/archive_research.py --download
python3 scripts/archive_research.py --download --only SOURCE_ID
```

The first command needs no network and preserves existing captures. Network access may need environment approval. New research sources should be added to the catalogue before rebuilding; give materially changed versions a new source ID and filename. The script does not automatically revisit already archived sources.

## Interpretation boundaries

- Parent-only, nursery-company and consolidated/site accounts are different units of analysis.
- Profit, EBITDA, operating cash flow and cash balances are different measures.
- Children on roll are not FTE occupancy. Registration date is not necessarily first trading date.
- Headline club floor area and undimensioned member plans do not establish a nursery/club area allocation.
- A crèche or kids club is not evidence of a registered full-day nursery.
- A membership launch announcement proves an advertised offer, not marketing spend, conversion or demand.
