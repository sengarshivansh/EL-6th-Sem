# Smart Grid Digital Twin

A Streamlit-based dashboard that simulates a **microgrid** using AI models for load and solar power forecasting.

Two versions are included:
- **V1** — LSTM-based load forecasting only
- **V2** — Hybrid LSTM + XGBoost for both load and solar forecasting

---

## 🗂️ Project Structure

```
EL-6th-Sem/
├── app.py                    # V1 — Streamlit UI (LSTM only)
├── app_v2.py                 # V2 — Streamlit UI (LSTM + XGBoost)
├── simulation_engine.py      # V1 — simulation logic
├── simulation_engine_v2.py   # V2 — simulation logic
├── filter_data.py            # Data preprocessing script
├── lstm_model.h5             # Pre-trained LSTM model
├── scaler.pkl                # Scaler used with LSTM
├── solar_xgb_model.pkl       # Pre-trained XGBoost solar model (V2 only)
├── BR02_final_data.csv       # Load data (used by V1 and V2)
├── clean_solar_15min.csv     # 15-min solar data (used by V2 only)
└── requirements.txt          # Python dependencies
```

---

## ✅ Prerequisites

Before you begin, make sure you have:

- **Python 3.10–3.12** — TensorFlow only supports specific versions. Check the [official TensorFlow install guide](https://www.tensorflow.org/install/pip) for your OS.
- **Git** — to clone this repository

---

## 🚀 Getting Started

### Step 1 — Clone the Repository

```bash
git clone https://github.com/sengarshivansh/EL-6th-Sem.git
cd EL-6th-Sem
```

> **Windows tip:** If your folder path has spaces, wrap it in quotes:
> ```cmd
> cd "C:\path\to\EL-6th-Sem"
> ```

---

### Step 2 — Create a Virtual Environment

Using a virtual environment keeps dependencies isolated from your system Python.

**Windows (PowerShell)**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt)**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

Once activated, you'll see `(venv)` at the start of your terminal prompt.

---

### Step 3 — Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

This installs: **Streamlit, pandas, NumPy, joblib, XGBoost, and TensorFlow**.

> **Optional:** If pandas shows warnings about missing packages, run:
> ```bash
> python -m pip install "numexpr>=2.10.2" "bottleneck>=1.4.2"
> ```

---

### Step 4 — Check Required Files

Make sure all the following files are present in the project root before running the app:

| File | Required by |
|---|---|
| `BR02_final_data.csv` | V1 and V2 |
| `lstm_model.h5` | V1 and V2 |
| `scaler.pkl` | V1 and V2 |
| `clean_solar_15min.csv` | V2 only |
| `solar_xgb_model.pkl` | V2 only |

> ⚠️ If any file is missing, the app will crash on startup with a file-not-found error.

> 📌 **Note for collaborators:** Large binary files (`.h5`, `.pkl`) and big CSVs may exceed GitHub's file size limits. If they are missing from the repo, download them from the shared drive link provided by the project owner, and place them in the project root.

---

### Step 5 — Run the App

Always use `python -m streamlit` (not just `streamlit`) to ensure it runs in your virtual environment.

**Run V2 — Hybrid AI (LSTM + XGBoost)** *(recommended)*
```bash
python -m streamlit run app_v2.py
```

**Run V1 — LSTM only**
```bash
python -m streamlit run app.py
```

Then open the URL shown in the terminal — usually **http://localhost:8501** — in your browser.

---

### Step 6 — Stop the App

Press `Ctrl+C` in the terminal to stop the server.

To exit the virtual environment:
```bash
deactivate
```

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` (e.g. `xgboost`) | Make sure your venv is activated, then run `python -m pip install -r requirements.txt` |
| Imports loading from Anaconda instead of venv | Use `python -m streamlit run app_v2.py` instead of just `streamlit run app_v2.py` |
| TensorFlow installation fails | Check that your Python version is supported — see [TensorFlow install docs](https://www.tensorflow.org/install/pip) |
| Port 8501 already in use | Run on a different port: `python -m streamlit run app_v2.py --server.port 8502` |

---

## 🧠 How It Works

The project simulates a small-scale power grid (microgrid) with the following components:

- **Load Forecasting** — An LSTM (Long Short-Term Memory) neural network predicts electricity demand based on historical load data (`BR02_final_data.csv`).
- **Solar Forecasting** (V2 only) — An XGBoost model predicts solar power generation using 15-minute interval solar data (`clean_solar_15min.csv`).
- **Simulation Engine** — Combines forecasted load and solar generation to simulate grid behavior, showing surplus/deficit in real time on the Streamlit dashboard.

---

## 📦 Tech Stack

| Tool | Purpose |
|---|---|
| [Streamlit](https://streamlit.io) | Interactive web dashboard |
| [TensorFlow / Keras](https://www.tensorflow.org) | LSTM model for load forecasting |
| [XGBoost](https://xgboost.readthedocs.io) | Solar generation forecasting |
| [pandas](https://pandas.pydata.org) | Data loading and manipulation |
| [NumPy](https://numpy.org) | Numerical computations |
| [joblib](https://joblib.readthedocs.io) | Loading saved model files (`.pkl`) |
