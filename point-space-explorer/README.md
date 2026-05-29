# 3D / 4D Point Space Explorer

A simple Streamlit app for entering/pasting tabular data and rendering it as an interactive 3D point cloud.

It is built for datasets like:

```csv
ticker,consistencyscoreadjusted,mktcap,averagepositive,averagepositivecfos
AAPL,0.82,3000000000000,0.55,0.61
MSFT,0.77,2800000000000,0.50,0.58
```

## What it does

- Editable table similar to a lightweight Stata data editor
- Add/delete rows directly in the browser
- Upload a CSV
- Save current data to `data/point_space_data.csv`
- Download the current table as CSV
- Interactive draggable 3D Plotly scatter plot
- 4D support by using a variable as color
- Optional 5D support by using a variable as bubble size
- 2D bubble chart for cleaner Substack screenshots
- Download interactive charts as HTML

## Recommended mapping

For the stock-factor example:

- X-axis: `averagepositive`
- Y-axis: `averagepositivecfos`
- Z-axis: `consistencyscoreadjusted`
- Color / 4th dimension: `consistencyscoreadjusted` or `cluster4`
- Bubble size: `log_mktcap`

The app automatically creates `log_mktcap` from `mktcap` when `mktcap` exists.

## Run locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
streamlit run app.py
```

## Deploy on Streamlit Cloud

1. Upload these files to a GitHub repo.
2. Go to Streamlit Community Cloud.
3. Create a new app from the repo.
4. Set the main file path to:

```text
app.py
```

5. Deploy.

## Important storage note

The app saves edits to `data/point_space_data.csv` while running.

On Streamlit Cloud, local file changes can disappear if the app restarts or redeploys. For permanent multi-user storage, connect something like Supabase, Google Sheets, Airtable, or a small database later.

For personal use, the CSV upload/download buttons are usually enough.

## Substack use

Substack may not embed arbitrary Streamlit apps cleanly. The best workflow is:

1. Use the app to build the 3D/4D chart.
2. Take a screenshot or screen-recorded GIF for the post.
3. Add a link to the deployed Streamlit app.
4. Use the 2D bubble chart when you want a cleaner static image.
