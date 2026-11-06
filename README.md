# Famille Burais website

This repository contains the Famille Burais website, built with Pelican. Content
is written in reStructuredText and rendered with the custom theme in
`themes/global`.

## Requirements

- Python 3
- Packages listed in [`requirements.txt`](requirements.txt)

## Setup

Create and activate a virtual environment, then install the project dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Build and preview

Build the development site into `output/`:

```sh
make html
```

Serve the generated site locally:

```sh
make serve PORT=8000
```

The site is then available at <http://localhost:8000>. To build with production
settings, use:

```sh
invoke preview
```

## Project structure

- `content/pages/` contains standalone pages.
- `content/articles/` contains articles; nested source directories are mirrored
  under `output/articles/`.
- `themes/global/templates/` contains the page templates.
- `themes/global/static/` contains theme stylesheets and images.
- `plugins/` contains the local Pelican plugins.

Trip cards open a printable trip book with a cover, contents and route; companions
appear on the cover. The contents links to each footprint article in trip order.
Route transport statistics show an icon for each transport type above its distance.
The trip book uses square pages and a table of contents with up to 20 steps per
column; columns wrap on narrow screens and long page contents can be scrolled.
The itinerary uses the trip's `TripSatelliteMap` when available, falling back
to `TripMap` for older trips or when satellite imagery could not be generated.

The `weasypdf` plugin generates one PDF per `findpenguins` trip, including its
`footprint` articles. With the default filename, PDFs are written to
`output/voyages-<trip-slug>.pdf`.

The production site URL is configured in `publishconf.py`. Set
`DEPLOY_TARGET=github` when building for GitHub Pages; otherwise the production
configuration uses the primary domain.
