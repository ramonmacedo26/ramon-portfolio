# Franchise Cost Prediction

Static portfolio demo that predicts franchise startup cost from annual revenue using a linear regression model calculated directly in the browser.

## Overview

This project was converted from a Python demo into a pure HTML, CSS, and JavaScript experience so it can be published easily on GitHub Pages and embedded into a portfolio site.

It demonstrates a compact end-to-end flow:

- structured business dataset
- regression logic in the frontend
- interactive scenario simulation
- visual presentation of model output
- portfolio-friendly static deployment

## Tech stack

- HTML
- CSS
- JavaScript

## Features

- responsive static frontend
- revenue slider plus numeric input
- regression-based prediction in real time
- business summary cards
- custom SVG chart
- dataset table
- project notes tab for portfolio framing

## Dataset

The sample dataset source remains in `slr12.csv` with two fields:

- `FrqAnual`: annual franchise revenue
- `CusInic`: initial franchise cost

The frontend uses the same values embedded in `app.js` for static delivery.

## Run locally

Because this is a static project, you can open `index.html` directly in the browser.

For a cleaner local preview, you can also serve the folder with any simple local server.

## Project structure

```text
franchise_cost_prediction/
  index.html
  styles.css
  app.js
  slr12.csv
  README.md
  .gitignore
```

## Publishing

This project is now a good fit for:

- GitHub Pages
- a personal portfolio site
- static hosting providers

## Next improvements

- move the dataset to JSON and load it dynamically
- add screenshot assets for the repository card
- include model limitations and assumptions section
