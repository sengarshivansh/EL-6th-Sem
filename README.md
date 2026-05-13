# Smart Grid Digital Twin (Streamlit)

Streamlit dashboards that simulate a microgrid using an LSTM load forecaster (V1) and a hybrid LSTM + XGBoost solar/load setup (V2).

## Prerequisites

- **Python 3.10–3.12** (pick a version that has a [TensorFlow pip wheel](https://www.tensorflow.org/install/pip) for your OS).
- **Git** (to clone this repository).

## 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO


If your folder path contains spaces (e.g. EL 5th Sem), keep the path in quotes on Windows:

    cd "C:\path\to\EL 5th Sem"

2. Create a virtual environment
    Using venv (recommended):

        Windows (PowerShell)

            python -m venv venv
            .\venv\Scripts\Activate.ps1
        Windows (Command Prompt)

            python -m venv venv
            venv\Scripts\activate.bat


        macOS / Linux

            python3 -m venv venv
            source venv/bin/activate
            You should see (venv) in your shell prompt.

3. Upgrade pip and install dependencies
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    This installs: Streamlit, pandas, NumPy, joblib, XGBoost, and TensorFlow.

Optional: silence pandas warnings
If pandas warns about numexpr or bottleneck, you can install:

        python -m pip install "numexpr>=2.10.2" "bottleneck>=1.4.2"


4. Required data and model files
        Place these files in the project root (same folder as app_v2.py):

        File	Used by
        clean_solar_15min.csv
        V2 (simulation_engine_v2.py)
        BR02_final_data.csv
        V1 and V2
        lstm_model.h5
        V1 and V2
        scaler.pkl
        V1 and V2
        solar_xgb_model.pkl
        V2 only
        If any file is missing, the app will fail on startup with a file-not-found or load error.

        GitHub: Large binaries (.h5, .pkl, big .csv) may exceed GitHub limits. Use Git LFS, a release asset, or a shared drive—and document where teammates should download them.

5. Run the Streamlit app
Always use python -m streamlit so you use the same interpreter as your venv (avoids accidentally using another Python, e.g. Anaconda, on your PATH).

V2 — Hybrid AI (LSTM + XGBoost)

python -m streamlit run app_v2.py
V1 — LSTM only

python -m streamlit run app.py
Then open the URL shown in the terminal (usually http://localhost:8501).

6. Stop the app
Press Ctrl+C in the terminal. To leave the virtual environment:

Windows: deactivate (after activate.bat) or close the terminal.
macOS/Linux: deactivate.
Troubleshooting
Problem	What to try
ModuleNotFoundError (e.g. xgboost)
Activate the venv, then python -m pip install -r requirements.txt, then python -m streamlit run ....
Streamlit runs but imports come from Anaconda paths
You ran streamlit instead of venv’s Python. Use python -m streamlit run app_v2.py after activating venv.
TensorFlow install fails
Match Python version to a supported TensorFlow build; see official install docs.
Port 8501 in use
python -m streamlit run app_v2.py --server.port 8502
Project layout (main pieces)
app_v2.py — Streamlit UI for the hybrid V2 twin.
simulation_engine_v2.py — Loads CSVs, LSTM, scaler, and XGBoost solar model.
app.py / simulation_engine.py — Earlier single-LSTM version.
Replace YOUR_USERNAME / YOUR_REPO in the clone URL with your real GitHub repository.

---
**Summary:** I added a matching **`requirements.txt`** in the instructions 