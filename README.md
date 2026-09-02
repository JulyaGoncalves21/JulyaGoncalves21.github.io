# Julya Gonçalves — Professional Portfolio

Bilingual static portfolio at the intersection of communication, business transformation and data.

> **Where communication meets data.**

## Public site

<https://julyagoncalves21.github.io/>

## Design and accessibility

- English is the default; complete Portuguese copy is available through the EN/PT control.
- Semantic HTML, skip navigation, visible keyboard focus and reduced-motion support.
- Responsive editorial layout with no employer logos or brand assets.
- Eight project graphics are original, metadata-free conceptual SVGs built with synthetic data only.
- Accessible native dialogs present two compact case-study galleries without adding long screenshot sections to the main page.
- The English overview remains readable without JavaScript; JavaScript powers the language switch, mobile navigation and case-study dialogs.

## Featured case studies

- **Vehicle Operations Traceability Platform** — consultation, traceability, transfer timeline and generic document status using only fictional records.
- **Kaizen Portfolio Analytics** — portfolio overview, contribution map, diagnosis and improvement pipeline using only fictional initiatives, owners and values.
- **Data Analysis & Dashboards** — four synthetic analytical views covering performance evolution, lead flow, segmentation, campaign engagement and decision support.

Every project visual is a new public-safe derivative. Reference screenshots are intentionally excluded from the repository.

## Privacy

The original resume files are not published because they contain personal contact details, external links and document metadata. No phone, address or unconfirmed public email is present on this site.

## Local preview

Run any static HTTP server from the repository root, for example:

```bash
python -m http.server 8000
```

Then open <http://localhost:8000/>. Test both language states with the EN/PT control and open each case study from the project cards.

Run the browser regression check with Selenium installed:

```bash
python tests/portfolio_e2e.py
```

