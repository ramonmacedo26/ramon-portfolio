const dataset = [
  { revenue: 1000, cost: 1050 },
  { revenue: 1125, cost: 1150 },
  { revenue: 1087, cost: 1213 },
  { revenue: 1070, cost: 1275 },
  { revenue: 1100, cost: 1300 },
  { revenue: 1150, cost: 1300 },
  { revenue: 1250, cost: 1400 },
  { revenue: 1150, cost: 1400 },
  { revenue: 1100, cost: 1250 },
  { revenue: 1350, cost: 1830 },
  { revenue: 1275, cost: 1350 },
  { revenue: 1375, cost: 1450 },
  { revenue: 1175, cost: 1300 },
  { revenue: 1200, cost: 1300 },
  { revenue: 1175, cost: 1275 },
  { revenue: 1300, cost: 1375 },
  { revenue: 1260, cost: 1285 },
  { revenue: 1330, cost: 1400 },
  { revenue: 1325, cost: 1400 },
  { revenue: 1200, cost: 1285 },
  { revenue: 1225, cost: 1275 },
  { revenue: 1090, cost: 1135 },
  { revenue: 1075, cost: 1250 },
  { revenue: 1080, cost: 1275 },
  { revenue: 1080, cost: 1150 },
  { revenue: 1180, cost: 1250 },
  { revenue: 1225, cost: 1275 },
  { revenue: 1175, cost: 1225 },
  { revenue: 1250, cost: 1280 },
  { revenue: 1250, cost: 1300 },
  { revenue: 750, cost: 1250 },
  { revenue: 1125, cost: 1175 },
  { revenue: 700, cost: 1300 },
  { revenue: 900, cost: 1250 },
  { revenue: 900, cost: 1300 },
  { revenue: 850, cost: 1200 },
];

const rangeInput = document.querySelector("#revenueRange");
const numberInput = document.querySelector("#revenueInput");
const currentRevenueLabel = document.querySelector("#currentRevenueLabel");
const predictedCostEl = document.querySelector("#predictedCost");
const predictionTextEl = document.querySelector("#predictionText");
const insightCardEl = document.querySelector("#insightCard");
const metricObservationsEl = document.querySelector("#metricObservations");
const metricAvgRevenueEl = document.querySelector("#metricAvgRevenue");
const metricAvgCostEl = document.querySelector("#metricAvgCost");
const metricR2El = document.querySelector("#metricR2");
const coefficientValueEl = document.querySelector("#coefficientValue");
const interceptValueEl = document.querySelector("#interceptValue");
const datasetBodyEl = document.querySelector("#datasetBody");
const chartEl = document.querySelector("#chart");
const rangeLabelEl = document.querySelector("#rangeLabel");
const tabButtons = document.querySelectorAll(".tab-button");
const tabPanels = document.querySelectorAll(".tab-panel");

function mean(values) {
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function formatBRL(value) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(value);
}

function linearRegression(rows) {
  const xs = rows.map((row) => row.revenue);
  const ys = rows.map((row) => row.cost);
  const xMean = mean(xs);
  const yMean = mean(ys);

  let numerator = 0;
  let denominator = 0;

  for (let index = 0; index < rows.length; index += 1) {
    numerator += (xs[index] - xMean) * (ys[index] - yMean);
    denominator += (xs[index] - xMean) ** 2;
  }

  const slope = numerator / denominator;
  const intercept = yMean - slope * xMean;
  const predictions = xs.map((x) => slope * x + intercept);

  let residualSum = 0;
  let totalSum = 0;
  for (let index = 0; index < ys.length; index += 1) {
    residualSum += (ys[index] - predictions[index]) ** 2;
    totalSum += (ys[index] - yMean) ** 2;
  }

  return {
    slope,
    intercept,
    r2: 1 - residualSum / totalSum,
  };
}

const model = linearRegression(dataset);
const avgRevenue = mean(dataset.map((row) => row.revenue));
const avgCost = mean(dataset.map((row) => row.cost));
const minRevenue = Math.min(...dataset.map((row) => row.revenue));
const maxRevenue = Math.max(...dataset.map((row) => row.revenue));
const minCost = Math.min(...dataset.map((row) => row.cost));
const maxCost = Math.max(...dataset.map((row) => row.cost));

function predictCost(revenue) {
  return model.slope * revenue + model.intercept;
}

function updateInputs(revenue) {
  rangeInput.value = String(revenue);
  numberInput.value = String(revenue);
}

function renderMetrics() {
  metricObservationsEl.textContent = String(dataset.length);
  metricAvgRevenueEl.textContent = formatBRL(avgRevenue);
  metricAvgCostEl.textContent = formatBRL(avgCost);
  metricR2El.textContent = model.r2.toFixed(3);
  coefficientValueEl.textContent = model.slope.toFixed(4);
  interceptValueEl.textContent = model.intercept.toFixed(4);
  rangeLabelEl.textContent = `${formatBRL(minRevenue)} to ${formatBRL(maxRevenue)}`;
}

function renderDataset() {
  datasetBodyEl.innerHTML = dataset
    .map(
      (row) => `
        <tr>
          <td>${formatBRL(row.revenue)}</td>
          <td>${formatBRL(row.cost)}</td>
        </tr>
      `,
    )
    .join("");
}

function xScale(value, chartWidth, marginLeft, marginRight) {
  return (
    marginLeft +
    ((value - minRevenue) / (maxRevenue - minRevenue)) *
      (chartWidth - marginLeft - marginRight)
  );
}

function yScale(value, chartHeight, marginTop, marginBottom) {
  return (
    chartHeight -
    marginBottom -
    ((value - minCost) / (maxCost - minCost)) *
      (chartHeight - marginTop - marginBottom)
  );
}

function renderChart(revenue) {
  const predictedCost = predictCost(revenue);
  const width = 860;
  const height = 420;
  const margin = { top: 36, right: 28, bottom: 44, left: 62 };
  const x1 = minRevenue;
  const x2 = maxRevenue;
  const y1 = predictCost(x1);
  const y2 = predictCost(x2);

  const axisColor = "rgba(19, 41, 61, 0.25)";
  const gridColor = "rgba(19, 41, 61, 0.08)";

  const circles = dataset
    .map((row) => {
      const cx = xScale(row.revenue, width, margin.left, margin.right);
      const cy = yScale(row.cost, height, margin.top, margin.bottom);
      return `<circle cx="${cx}" cy="${cy}" r="6" fill="#1b4965" stroke="#ffffff" stroke-width="2" />`;
    })
    .join("");

  const gridLines = Array.from({ length: 5 }, (_, index) => {
    const y = margin.top + index * ((height - margin.top - margin.bottom) / 4);
    return `<line x1="${margin.left}" y1="${y}" x2="${width - margin.right}" y2="${y}" stroke="${gridColor}" stroke-width="1" />`;
  }).join("");

  chartEl.innerHTML = `
    <rect x="0" y="0" width="${width}" height="${height}" rx="24" fill="transparent" />
    ${gridLines}
    <line x1="${margin.left}" y1="${height - margin.bottom}" x2="${width - margin.right}" y2="${height - margin.bottom}" stroke="${axisColor}" stroke-width="1.5" />
    <line x1="${margin.left}" y1="${margin.top}" x2="${margin.left}" y2="${height - margin.bottom}" stroke="${axisColor}" stroke-width="1.5" />

    <line
      x1="${xScale(x1, width, margin.left, margin.right)}"
      y1="${yScale(y1, height, margin.top, margin.bottom)}"
      x2="${xScale(x2, width, margin.left, margin.right)}"
      y2="${yScale(y2, height, margin.top, margin.bottom)}"
      stroke="#ff7b00"
      stroke-width="4"
      stroke-linecap="round"
    />

    ${circles}

    <circle
      cx="${xScale(revenue, width, margin.left, margin.right)}"
      cy="${yScale(predictedCost, height, margin.top, margin.bottom)}"
      r="9"
      fill="#2a9d8f"
      stroke="#ffffff"
      stroke-width="3"
    />

    <text x="${margin.left}" y="${height - 10}" fill="#58667d" font-size="12">Annual revenue</text>
    <text x="14" y="${margin.top - 12}" fill="#58667d" font-size="12">Initial cost</text>
  `;
}

function renderPrediction(revenue) {
  const predictedCost = predictCost(revenue);
  const difference = predictedCost - avgCost;
  const direction = difference >= 0 ? "above" : "below";

  currentRevenueLabel.textContent = formatBRL(revenue);
  predictedCostEl.textContent = formatBRL(predictedCost);
  predictionTextEl.textContent =
    `Based on an annual revenue scenario of ${formatBRL(revenue)}, ` +
    `the model estimates a startup cost near ${formatBRL(predictedCost)}.`;
  insightCardEl.innerHTML =
    `<strong>Quick read:</strong> this estimate is ${direction} the sample average by ` +
    `<strong>${formatBRL(Math.abs(difference))}</strong>.`;

  renderChart(revenue);
}

function activateTab(targetTab) {
  tabButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.tab === targetTab);
  });

  tabPanels.forEach((panel) => {
    const isActive = panel.dataset.panel === targetTab;
    panel.classList.toggle("is-active", isActive);
    panel.hidden = !isActive;
  });
}

function handleRevenueChange(value) {
  const revenue = Number(value);
  updateInputs(revenue);
  renderPrediction(revenue);
}

rangeInput.addEventListener("input", (event) => {
  handleRevenueChange(event.target.value);
});

numberInput.addEventListener("input", (event) => {
  let revenue = Number(event.target.value);
  if (Number.isNaN(revenue)) {
    return;
  }
  revenue = Math.min(Math.max(revenue, Number(numberInput.min)), Number(numberInput.max));
  handleRevenueChange(revenue);
});

tabButtons.forEach((button) => {
  button.addEventListener("click", () => activateTab(button.dataset.tab));
});

renderMetrics();
renderDataset();
handleRevenueChange(Number(numberInput.value));
