import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const tablesDir = path.join(root, "outputs", "tables");
const outputDir = path.join(root, "outputs");
const previewDir = path.join(root, "tmp", "workbook_previews");

const [payload, summary, quality] = await Promise.all([
  readJson(path.join(tablesDir, "workbook_payload.json")),
  readJson(path.join(tablesDir, "summary_metrics.json")),
  readJson(path.join(tablesDir, "data_quality_summary.json")),
]);

const workbook = Workbook.create();
const dashboard = workbook.worksheets.add("CMI Dashboard");
const analysisSummary = workbook.worksheets.add("Analysis Summary");
const weekly = workbook.worksheets.add("Weekly Tracker");
const pain = workbook.worksheets.add("Pain Points");
const needs = workbook.worksheets.add("Need States");
const scents = workbook.worksheets.add("Scent Families");
const brands = workbook.worksheets.add("Brand Scorecard");
const price = workbook.worksheets.add("Price Bands");
const segments = workbook.worksheets.add("Segments");
const formats = workbook.worksheets.add("Formats");
const repurchase = workbook.worksheets.add("Repurchase");
const dictionary = workbook.worksheets.add("Metric Dictionary");
const sources = workbook.worksheets.add("Source Notes");

const C = {
  navy: "#20364D",
  blue: "#3567A8",
  blueLight: "#DCE8F5",
  gold: "#C89632",
  goldLight: "#F7EBCF",
  orange: "#D97841",
  orangeLight: "#F9E2D5",
  ink: "#24313D",
  muted: "#647181",
  grid: "#DDE3E9",
  white: "#FFFFFF",
  bg: "#F7F9FB",
};

buildAnalysisSummary();
buildWeekly();
buildTagSheet(pain, payload.pain_points, "Pain-point analysis", "PainPointTable");
buildTagSheet(needs, payload.need_states, "Need-state analysis", "NeedStateTable");
buildTagSheet(scents, payload.scent_families, "Scent-family analysis", "ScentFamilyTable");
buildBrandSheet();
buildPriceSheet();
buildDistributionSheet(segments, payload.behavior_segments, "Behavioral segments", "behavior_segment", "SegmentTable");
buildDistributionSheet(formats, payload.product_formats, "Fragrance formats", "product_format", "FormatTable");
buildDistributionSheet(repurchase, payload.repurchase_intent, "Repurchase intent", "repurchase_intent", "RepurchaseTable");
buildDictionary();
buildSources();
buildDashboard();

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });

const dashboardCheck = await workbook.inspect({
  kind: "table",
  range: "CMI Dashboard!A1:N40",
  include: "values,formulas",
  tableMaxRows: 40,
  tableMaxCols: 14,
});
console.log(dashboardCheck.ndjson);

const formulaErrors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
console.log(formulaErrors.ndjson);

for (const sheet of [dashboard, analysisSummary, weekly, pain, needs, scents, brands, price, segments, formats, repurchase, dictionary, sources]) {
  const preview = await workbook.render({
    sheetName: sheet.name,
    autoCrop: "all",
    scale: sheet.name === "CMI Dashboard" ? 1 : 0.8,
    format: "png",
  });
  const safe = sheet.name.replaceAll(" ", "_").toLowerCase();
  await fs.writeFile(path.join(previewDir, `${safe}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
const outputPath = path.join(outputDir, "fragrance_cmi_weekly_tracker.xlsx");
await output.save(outputPath);
await fs.rm(`${outputPath}.inspect.ndjson`, { force: true });
console.log(JSON.stringify({ outputPath, previewDir, sheets: 13 }, null, 2));

async function readJson(file) {
  return JSON.parse(await fs.readFile(file, "utf8"));
}

function setTitle(sheet, title, subtitle, endCol) {
  sheet.showGridLines = false;
  sheet.mergeCells(`A1:${endCol}2`);
  sheet.getRange("A1").values = [[title]];
  sheet.getRange(`A1:${endCol}2`).format = {
    fill: C.navy,
    font: { bold: true, color: C.white, size: 18 },
    verticalAlignment: "center",
    horizontalAlignment: "left",
  };
  sheet.mergeCells(`A3:${endCol}3`);
  sheet.getRange("A3").values = [[subtitle]];
  sheet.getRange(`A3:${endCol}3`).format = {
    fill: C.blueLight,
    font: { color: C.muted, size: 10 },
    verticalAlignment: "center",
  };
  sheet.getRange("1:1").format.rowHeight = 24;
  sheet.getRange("2:2").format.rowHeight = 22;
  sheet.getRange("3:3").format.rowHeight = 26;
}

function styleHeader(range) {
  range.format = {
    fill: C.blue,
    font: { bold: true, color: C.white },
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "inside", style: "thin", color: C.white },
  };
  range.format.rowHeight = 30;
}

function styleBody(range) {
  range.format = {
    font: { color: C.ink, size: 10 },
    verticalAlignment: "center",
    borders: { insideHorizontal: { style: "thin", color: C.grid } },
  };
}

function addTable(sheet, range, name) {
  const table = sheet.tables.add(range, true, name);
  table.style = "TableStyleMedium2";
  table.showFilterButton = true;
  return table;
}

function buildAnalysisSummary() {
  setTitle(
    analysisSummary,
    "Analysis summary",
    "Source-backed values used by the dashboard; formulas on the dashboard reference this sheet.",
    "D",
  );
  const rows = [
    ["Metric", "Value", "Display format", "Definition"],
    ["Data as of", summary.data_as_of, "yyyy-mm-dd", "Latest valid review date in the fragrance subset"],
    ["Analysis reviews", summary.analysis_review_rows, "#,##0", "Deduplicated fragrance reviews with valid date and rating"],
    ["Fragrance products", summary.analysis_product_rows, "#,##0", "Distinct reviewed parent ASINs"],
    ["Text-eligible reviews", summary.text_eligible_rows, "#,##0", "At least 20 characters and 4 tokens, excluding pure promo for text cuts"],
    ["Verified purchase share", summary.verified_purchase_share, "0.0%", "Source verified_purchase flag"],
    ["Price coverage share", summary.price_coverage_share, "0.0%", "Reviews linked to non-null item list price"],
    ["Average rating", summary.average_rating, "0.00", "Mean 1–5 star rating"],
    ["Positive review share", summary.positive_review_share, "0.0%", "Share with rating 4 or 5"],
    ["Negative review share", summary.negative_review_share, "0.0%", "Share with rating 1 or 2"],
    ["Matched review rows", quality.matched_review_rows, "#,##0", "Reviews matched to the fragrance product set before deduplication"],
    ["Duplicate review rows", quality.duplicate_review_rows, "#,##0", "Composite-key duplicates removed"],
    ["Negative eligible reviews", summary.negative_text_eligible_rows, "#,##0", "Pain-point denominator"],
    ["Explicit repurchase rows", summary.explicit_repurchase_rows, "#,##0", "Reviews with explicit positive/negative buy-again language"],
  ];
  analysisSummary.getRange(`A5:D${4 + rows.length}`).values = rows;
  styleHeader(analysisSummary.getRange("A5:D5"));
  styleBody(analysisSummary.getRange(`A6:D${4 + rows.length}`));
  analysisSummary.getRange("B6").setNumberFormat("yyyy-mm-dd");
  analysisSummary.getRange("B7:B9").setNumberFormat("#,##0");
  analysisSummary.getRange("B10:B11").setNumberFormat("0.0%");
  analysisSummary.getRange("B12").setNumberFormat("0.00");
  analysisSummary.getRange("B13:B14").setNumberFormat("0.0%");
  analysisSummary.getRange("B15:B18").setNumberFormat("#,##0");
  analysisSummary.getRange("A:D").format.columnWidth = 18;
  analysisSummary.getRange("D:D").format.columnWidth = 58;
  analysisSummary.freezePanes.freezeRows(5);
  addTable(analysisSummary, `A5:D${4 + rows.length}`, "AnalysisSummaryTable");
}

function buildWeekly() {
  setTitle(
    weekly,
    "52-week consumer voice tracker",
    "Historical template using the final 52 observed calendar weeks in Amazon Reviews 2023.",
    "N",
  );
  const headers = [
    "Week", "Review volume", "Average rating", "Positive reviews", "Negative reviews",
    "Verified reviews", "Helpful votes", "Price discussions", "Text-eligible reviews",
    "Positive share", "Negative share", "Verified share", "Price discussion share", "Week label (chart)",
  ];
  weekly.getRange("A5:N5").values = [headers];
  const sourceRows = payload.weekly_tracker.map((r) => [
    new Date(r.review_week), r.review_volume, r.average_rating, r.positive_reviews,
    r.negative_reviews, r.verified_reviews, r.helpful_votes, r.price_discussions,
    r.text_eligible_reviews, null, null, null, null, null,
  ]);
  const end = 5 + sourceRows.length;
  weekly.getRange(`A6:N${end}`).values = sourceRows;
  weekly.getRange("J6:N6").formulas = [[
    "=IFERROR(D6/B6,0)", "=IFERROR(E6/B6,0)", "=IFERROR(F6/B6,0)", "=IFERROR(H6/I6,0)", "=TEXT(A6,\"mmm d\")",
  ]];
  weekly.getRange(`J6:N${end}`).fillDown();
  styleHeader(weekly.getRange("A5:N5"));
  styleBody(weekly.getRange(`A6:N${end}`));
  weekly.getRange(`A6:A${end}`).setNumberFormat("yyyy-mm-dd");
  weekly.getRange(`B6:B${end}`).setNumberFormat("#,##0");
  weekly.getRange(`C6:C${end}`).setNumberFormat("0.00");
  weekly.getRange(`D6:I${end}`).setNumberFormat("#,##0");
  weekly.getRange(`J6:M${end}`).setNumberFormat("0.0%");
  weekly.getRange("A:A").format.columnWidth = 13;
  weekly.getRange("B:M").format.columnWidth = 15;
  weekly.getRange("N:N").format.columnWidth = 15;
  weekly.freezePanes.freezeRows(5);
  addTable(weekly, `A5:N${end}`, "WeeklyTrackerTable");
}

function buildTagSheet(sheet, records, title, tableName) {
  setTitle(sheet, title, "Multi-label text matches; rates do not sum to 100%.", "G");
  const headers = ["Category", "Mentions", "Denominator", "Mention rate", "Share of tag mentions", "Cumulative share", "Denominator definition"];
  sheet.getRange("A5:G5").values = [headers];
  const rows = records.map((r) => [pretty(r.category), r.mentions, r.denominator, null, null, null, r.denominator_definition]);
  const end = 5 + rows.length;
  sheet.getRange(`A6:G${end}`).values = rows;
  sheet.getRange("D6:F6").formulas = [[
    "=IFERROR(B6/C6,0)", `=IFERROR(B6/SUM($B$6:$B$${end}),0)`, "=SUM($E$6:E6)",
  ]];
  sheet.getRange(`D6:F${end}`).fillDown();
  styleHeader(sheet.getRange("A5:G5"));
  styleBody(sheet.getRange(`A6:G${end}`));
  sheet.getRange(`B6:C${end}`).setNumberFormat("#,##0");
  sheet.getRange(`D6:F${end}`).setNumberFormat("0.0%");
  sheet.getRange("A:A").format.columnWidth = 25;
  sheet.getRange("B:F").format.columnWidth = 17;
  sheet.getRange("G:G").format.columnWidth = 62;
  sheet.getRange(`G6:G${end}`).format.wrapText = true;
  sheet.freezePanes.freezeRows(5);
  addTable(sheet, `A5:G${end}`, tableName);
}

function buildBrandSheet() {
  setTitle(brands, "Brand scorecard", "Brands with at least 20 reviews; review footprint is not market share.", "M");
  const headers = [
    "Brand", "Review volume", "Products", "Average rating", "Median price (USD)", "Price coverage",
    "Verified share", "Helpful votes", "Positive share", "Negative share", "Longevity mentions",
    "Value mentions", "Authenticity mentions",
  ];
  brands.getRange("A5:M5").values = [headers];
  const rows = payload.brand_scorecard.map((r) => [
    r.brand, r.review_volume, r.product_count, r.average_rating, r.median_price_usd,
    r.price_coverage, r.verified_share, r.helpful_votes, r.positive_share, r.negative_share,
    r.longevity_mentions, r.value_mentions, r.authenticity_mentions,
  ]);
  const end = 5 + rows.length;
  brands.getRange(`A6:M${end}`).values = rows;
  styleHeader(brands.getRange("A5:M5"));
  styleBody(brands.getRange(`A6:M${end}`));
  brands.getRange(`B6:C${end}`).setNumberFormat("#,##0");
  brands.getRange(`D6:D${end}`).setNumberFormat("0.00");
  brands.getRange(`E6:E${end}`).setNumberFormat("$#,##0.00");
  brands.getRange(`F6:G${end}`).setNumberFormat("0.0%");
  brands.getRange(`H6:H${end}`).setNumberFormat("#,##0");
  brands.getRange(`I6:J${end}`).setNumberFormat("0.0%");
  brands.getRange(`K6:M${end}`).setNumberFormat("#,##0");
  brands.getRange("A:A").format.columnWidth = 27;
  brands.getRange("B:M").format.columnWidth = 16;
  brands.freezePanes.freezeRows(5);
  addTable(brands, `A5:M${end}`, "BrandScorecardTable");
}

function buildPriceSheet() {
  setTitle(price, "Price-band sentiment", "USD item list price; reviews without a matched price are excluded.", "G");
  const headers = ["Price band", "Review volume", "Products", "Average rating", "Positive share", "Negative share", "Price discussion share"];
  price.getRange("A5:G5").values = [headers];
  const rows = payload.price_bands.map((r) => [
    r.price_band, r.review_volume, r.product_count, r.average_rating,
    r.positive_share, r.negative_share, r.price_discussion_share,
  ]);
  const end = 5 + rows.length;
  price.getRange(`A6:G${end}`).values = rows;
  styleHeader(price.getRange("A5:G5"));
  styleBody(price.getRange(`A6:G${end}`));
  price.getRange(`B6:C${end}`).setNumberFormat("#,##0");
  price.getRange(`D6:D${end}`).setNumberFormat("0.00");
  price.getRange(`E6:G${end}`).setNumberFormat("0.0%");
  price.getRange("A:A").format.columnWidth = 18;
  price.getRange("B:G").format.columnWidth = 19;
  price.freezePanes.freezeRows(5);
  addTable(price, `A5:G${end}`, "PriceBandTable");
}

function buildDistributionSheet(sheet, records, title, key, tableName) {
  setTitle(sheet, title, "Review-level distribution with rating and sentiment context.", "F");
  const headers = ["Category", "Review volume", "Average rating", "Positive share", "Negative share", "Share of reviews"];
  sheet.getRange("A5:F5").values = [headers];
  const rows = records.map((r) => [pretty(r[key]), r.review_volume, r.average_rating, r.positive_share, r.negative_share, r.share_of_reviews]);
  const end = 5 + rows.length;
  sheet.getRange(`A6:F${end}`).values = rows;
  styleHeader(sheet.getRange("A5:F5"));
  styleBody(sheet.getRange(`A6:F${end}`));
  sheet.getRange(`B6:B${end}`).setNumberFormat("#,##0");
  sheet.getRange(`C6:C${end}`).setNumberFormat("0.00");
  sheet.getRange(`D6:F${end}`).setNumberFormat("0.0%");
  sheet.getRange("A:A").format.columnWidth = 28;
  sheet.getRange("B:F").format.columnWidth = 18;
  sheet.freezePanes.freezeRows(5);
  addTable(sheet, `A5:F${end}`, tableName);
}

function buildDictionary() {
  setTitle(dictionary, "Metric dictionary", "Definitions and denominators used throughout the workbook.", "D");
  const rows = [
    ["Metric", "Definition", "Denominator / grain", "Notes"],
    ["Analysis review", "Valid fragrance-linked review after composite-key deduplication", "One review_key", "Raw user id and review text are not stored"],
    ["Text-eligible review", "At least 20 normalized characters and 4 tokens", "Analysis reviews", "Pure promotional noise excluded from text cuts"],
    ["Positive review share", "Rating is 4 or 5", "Reviews in the selected cut", "Observed rating sentiment, not NLP sentiment"],
    ["Negative review share", "Rating is 1 or 2", "Reviews in the selected cut", "3-star reviews are neutral"],
    ["Pain mention rate", "At least one lexicon phrase for the pain category", "Negative eligible reviews", "Multi-label; rates do not sum to 100%"],
    ["Need-state mention rate", "At least one use-case or emotional phrase", "Eligible reviews", "Multi-label"],
    ["Scent-family mention rate", "At least one consumer scent word", "Eligible reviews", "Not official brand fragrance taxonomy"],
    ["Explicit repurchase share", "Positive or negative buy-again phrase", "Explicit repurchase reviews only", "Not an observed repeat-purchase rate"],
    ["Brand review footprint", "Count of linked reviews", "Brand/store normalized from item metadata", "Not sales or market share"],
    ["Price-band sentiment", "Rating sentiment by metadata list price", "Reviews with non-null USD price", "Price captured at source crawl time"],
    ["Behavior segment", "Mutually exclusive deterministic rule label", "One eligible review", "No demographic inference"],
  ];
  const end = 4 + rows.length;
  dictionary.getRange(`A5:D${end}`).values = rows;
  styleHeader(dictionary.getRange("A5:D5"));
  styleBody(dictionary.getRange(`A6:D${end}`));
  dictionary.getRange("A:A").format.columnWidth = 28;
  dictionary.getRange("B:D").format.columnWidth = 52;
  dictionary.getRange(`B6:D${end}`).format.wrapText = true;
  dictionary.getRange(`A6:D${end}`).format.rowHeight = 42;
  dictionary.freezePanes.freezeRows(5);
  addTable(dictionary, `A5:D${end}`, "MetricDictionaryTable");
}

function buildSources() {
  setTitle(sources, "Source notes", "Public research data, privacy handling and refresh guidance.", "D");
  const rows = [
    ["Item", "Value", "Status", "Implication"],
    ["Dataset", "Amazon Reviews 2023 / All_Beauty — McAuley Lab", "Public research source", "Historical consumer review evidence"],
    ["Project page", "https://amazon-reviews-2023.github.io/", "Source URL", "Dataset fields, coverage and citation"],
    ["Review URL", "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/review_categories/All_Beauty.jsonl.gz", "Source URL", "Raw file is downloaded locally and not committed"],
    ["Metadata URL", "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/meta_categories/meta_All_Beauty.jsonl.gz", "Source URL", "Provides title, brand/store and list price"],
    ["Data as of", summary.data_as_of, "Historical", "Not a 2026 real-time market monitor"],
    ["Raw review rows", quality.source_review_rows, "Validated", "All source JSONL rows parsed"],
    ["Raw metadata rows", quality.source_metadata_rows, "Validated", "All source JSONL rows parsed"],
    ["Privacy", quality.privacy, "Applied", "Processed outputs contain no full review text or raw user ids"],
    ["Refresh", "Run download_data.py, then run_pipeline.py, then build_tracker.mjs", "Reproducible", "Replace source adapters for approved social/e-commerce feeds"],
  ];
  const end = 4 + rows.length;
  sources.getRange(`A5:D${end}`).values = rows;
  styleHeader(sources.getRange("A5:D5"));
  styleBody(sources.getRange(`A6:D${end}`));
  sources.getRange("A:A").format.columnWidth = 22;
  sources.getRange("B:B").format.columnWidth = 78;
  sources.getRange("C:C").format.columnWidth = 22;
  sources.getRange("D:D").format.columnWidth = 55;
  sources.getRange(`B6:D${end}`).format.wrapText = true;
  sources.getRange(`A6:D${end}`).format.rowHeight = 40;
  sources.getRange("B10").setNumberFormat("yyyy-mm-dd");
  sources.getRange("B11:B12").setNumberFormat("#,##0");
  sources.freezePanes.freezeRows(5);
  addTable(sources, `A5:D${end}`, "SourceNotesTable");
}

function buildDashboard() {
  setTitle(
    dashboard,
    "Fragrance Consumer Insight — Weekly Tracker",
    `Decision view | Amazon Reviews 2023 | data through ${summary.data_as_of} | historical portfolio analysis`,
    "N",
  );
  dashboard.getRange("A:N").format.columnWidth = 11;
  dashboard.getRange("A:A").format.columnWidth = 13;
  dashboard.getRange("N:N").format.columnWidth = 13;

  const cards = [
    { label: "Analysis reviews", labelRange: "A5:C5", valueRange: "A6:C7", formula: "='Analysis Summary'!B7", format: "#,##0", color: C.blueLight },
    { label: "Fragrance products", labelRange: "D5:F5", valueRange: "D6:F7", formula: "='Analysis Summary'!B8", format: "#,##0", color: C.blueLight },
    { label: "Verified purchase", labelRange: "H5:J5", valueRange: "H6:J7", formula: "='Analysis Summary'!B10", format: "0.0%", color: C.goldLight },
    { label: "Negative review share", labelRange: "K5:N5", valueRange: "K6:N7", formula: "='Analysis Summary'!B14", format: "0.0%", color: C.orangeLight },
  ];
  for (const card of cards) {
    dashboard.mergeCells(card.labelRange);
    dashboard.getRange(card.labelRange.split(":")[0]).values = [[card.label]];
    dashboard.getRange(card.labelRange).format = { fill: card.color, font: { bold: true, color: C.muted }, horizontalAlignment: "center", verticalAlignment: "center" };
    dashboard.mergeCells(card.valueRange);
    const anchor = card.valueRange.split(":")[0];
    dashboard.getRange(anchor).formulas = [[card.formula]];
    dashboard.getRange(card.valueRange).format = {
      fill: C.white,
      font: { bold: true, color: C.ink, size: 20 },
      horizontalAlignment: "center",
      verticalAlignment: "center",
      borders: { preset: "outside", style: "thin", color: C.grid },
    };
    dashboard.getRange(anchor).setNumberFormat(card.format);
  }

  dashboard.mergeCells("A10:F10");
  dashboard.getRange("A10").values = [["Data quality gate"]];
  dashboard.getRange("A10:F10").format = { fill: C.blue, font: { bold: true, color: C.white }, verticalAlignment: "center" };
  const qualityRows = [
    ["Matched reviews before dedupe", "='Analysis Summary'!B15", "#,##0"],
    ["Duplicates removed", "='Analysis Summary'!B16", "#,##0"],
    ["Text-eligible reviews", "='Analysis Summary'!B9", "#,##0"],
    ["Price coverage", "='Analysis Summary'!B11", "0.0%"],
    ["Pain-point denominator", "='Analysis Summary'!B17", "#,##0"],
  ];
  qualityRows.forEach((row, index) => {
    const r = 11 + index;
    dashboard.mergeCells(`A${r}:D${r}`);
    dashboard.getRange(`A${r}`).values = [[row[0]]];
    dashboard.mergeCells(`E${r}:F${r}`);
    dashboard.getRange(`E${r}`).formulas = [[row[1]]];
    dashboard.getRange(`E${r}`).setNumberFormat(row[2]);
  });
  dashboard.getRange("A11:F15").format = { borders: { insideHorizontal: { style: "thin", color: C.grid } }, verticalAlignment: "center" };

  dashboard.mergeCells("H10:N10");
  dashboard.getRange("H10").values = [["Decision hypotheses to validate"]];
  dashboard.getRange("H10:N10").format = { fill: C.gold, font: { bold: true, color: C.white }, verticalAlignment: "center" };
  const recommendations = [
    "1. Reduce scent-selection risk with a paid discovery / travel-size route.",
    "2. Build content as occasion × scent family × performance expectation.",
    "3. Judge competitors on review footprint and satisfaction together.",
  ];
  recommendations.forEach((text, i) => {
    const start = 11 + i * 2;
    dashboard.mergeCells(`H${start}:N${start + 1}`);
    dashboard.getRange(`H${start}`).values = [[text]];
    dashboard.getRange(`H${start}:N${start + 1}`).format = {
      fill: i % 2 === 0 ? C.goldLight : C.white,
      font: { color: C.ink },
      wrapText: true,
      verticalAlignment: "center",
      borders: { preset: "outside", style: "thin", color: C.grid },
    };
  });

  const weeklyChart = dashboard.charts.add("line", { chartType: "line", title: "Weekly review volume" });
  const weeklySeries = weeklyChart.series.add("Review volume");
  weeklySeries.categoryFormula = "'Weekly Tracker'!$N$6:$N$57";
  weeklySeries.formula = "'Weekly Tracker'!$B$6:$B$57";
  weeklySeries.fill = C.blue;
  weeklyChart.title = "Weekly review volume (52 weeks)";
  weeklyChart.hasLegend = false;
  weeklyChart.xAxis = { axisType: "textAxis", textStyle: { fontSize: 9 }, tickLabelInterval: 4 };
  weeklyChart.yAxis = { numberFormatCode: "#,##0" };
  weeklyChart.setPosition("A19", "G35");

  const painEnd = 5 + payload.pain_points.length;
  const painChart = dashboard.charts.add("bar", { chartType: "bar", title: "Pain-point mention rate" });
  const painSeries = painChart.series.add("Mention rate");
  painSeries.categoryFormula = `'Pain Points'!$A$6:$A$${painEnd}`;
  painSeries.formula = `'Pain Points'!$D$6:$D$${painEnd}`;
  painSeries.fill = C.orange;
  painChart.title = "Pain-point mention rate";
  painChart.hasLegend = false;
  painChart.yAxis = { numberFormatCode: "0%" };
  painChart.setPosition("H19", "N35");

  dashboard.mergeCells("A38:N40");
  dashboard.getRange("A38").values = [[
    "Read with care: this is historical public e-commerce review evidence, not 2026 China market share. Need, pain and scent tags are multi-label. See Metric Dictionary and Source Notes before using a percentage.",
  ]];
  dashboard.getRange("A38:N40").format = {
    fill: C.bg,
    font: { italic: true, color: C.muted, size: 9 },
    wrapText: true,
    verticalAlignment: "center",
    borders: { preset: "outside", style: "thin", color: C.grid },
  };
  dashboard.freezePanes.freezeRows(3);
}

function pretty(value) {
  return String(value ?? "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
