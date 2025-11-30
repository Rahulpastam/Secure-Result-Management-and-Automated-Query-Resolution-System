Project summary
- Purpose: A Streamlit-based Secure Result Management System with role-based UI (student/admin), complaint submission, ML-assisted complaint categorization, duplicate detection (SBERT), SLA (survival) risk prediction, anomaly detection, and results upload/management. See `PROJECT_REPORT.md` for the high-level project report.

Top-level layout (paths)
- `PROJECT_REPORT.md` — full project report & documentation.
- `requirements.txt` — packages required to run.
- `data/db.sqlite3` — application SQLite DB: `data/db.sqlite3`.
- secure_result/ — application code and ML models:
  - `secure_result/app.py`
  - `secure_result/db.py`
  - `secure_result/model_loader.py`
  - `secure_result/utils.py`
  - `secure_result/models` — serialized model files, SBERT model folder and notebooks.
  - `secure_result/page_modules` — Streamlit page modules.
- uploads/ — uploaded files storage.

Files & modules — purpose and key internals

1) `secure_result/app.py` — application entry, session & routing
- File: `secure_result/app.py`
- Key responsibilities:
  - Streamlit configuration and startup, session check and login gating.
  - Role-based navigation: builds page list and maps user role -> page set.
  - Calls application init: `db.init_db()` at startup.
- Key symbols:
  - `app.main` — main function wiring navigation and calling the selected page `run()` (see pages).
  - Authentication helpers: `require_login()`, `show_login_page()`, `do_logout()` (all in file).
- Behavior:
  - If not authenticated, shows login page and stops Streamlit script.
  - After login, sets `session_state['username']` and `['role']` and renders pages appropriate to role.

2) `secure_result/db.py` — database layer (SQLite)
- File: `secure_result/db.py`
- Responsibilities:
  - Connection factory: `get_conn()` returns sqlite3 Connection with row factory for dict‑like rows.
  - DB initialization: `init_db()` creates tables and indexes when first run.
  - User management: `create_user()`, `get_user_by_username()`, `verify_user()` — password hashing / verification.
  - Complaint management: `add_complaint()` stores complaints and returns inserted id.
  - Result management: `add_result()`, `get_results_by_student()` (used in UI).
- Implementation notes:
  - DB path: DB_PATH at top points to `data/db.sqlite3`.
  - `add_complaint` accepts metadata: predicted_category, confidence, file_path, course_code, semester, duplicate_reference; commits and returns `lastrowid`.

3) `secure_result/model_loader.py` — Machine Learning layer, loading & inference
- File: `secure_result/model_loader.py`
- Purpose: centralizes model loading, cached embeddings, and inference functions for:
  - Category classification (sklearn classifier + TF-IDF vectorizer + label encoder)
  - Duplicate detection (Sentence-BERT embeddings & cached embeddings)
  - SLA prediction (survival model using lifelines CoxPHFitter)
  - Anomaly detection (IsolationForest)
- Key constants and paths:
  - `MODEL_DIR = secure_result/models`
  - `CLASSIFIER_PATH`, `VECTORIZER_PATH`, `LABEL_ENCODER_PATH`
  - `SBERT_MODEL_PATH = MODEL_DIR / 'sbert_duplicate_model'` (SBERT local folder)
  - `SURVIVAL_MODEL_PATH = MODEL_DIR / 'sla_survival_model.pkl'`
  - `SLA_FEATURES_PATH = MODEL_DIR / 'sla_features.json'`
  - CACHE_EMBEDDINGS_PATH, CACHE_TEXTS_PATH, CACHE_METADATA_PATH for resolved embeddings cache.
- Loading logic:
  - `model_loader.load_model` tries to load classifier, vectorizer, label encoder, SBERT model (if sentence-transformers available), survival model (if lifelines available), anomaly model (joblib), encoders. Keeps `_model_info` with flags (classifier_loaded, sbert_loaded, etc).
  - Graceful degradation: collects errors list and continues; non‑essential models are optional.
- Prediction functions:
  - `model_loader.predict_category` — cleans text (clean_text), vectorizes with TF-IDF, predicts class (+confidence via predict_proba or decision_function heuristic). Returns dict with prediction and confidence.
  - `model_loader.find_similar_complaint` — computes embedding for input text (via SBERT), computes cosine similarity against cached resolved embeddings, and returns top_k similar entries with score and index. Uses caching of embeddings in `models/cache`.
  - `model_loader.predict_sla` — transforms complaint metadata to features, uses survival model to estimate median resolution and breach probability at time t (e.g., 7 days). Returns breach probability and predicted median days.
  - `model_loader.detect_anomaly` — uses the anomaly model decision_function and predicts if an outlier case.
  - `model_loader.model_status` — returns `_model_info` and counts for loaded datasets/embeddings.
- Preprocessing:
  - `clean_text` uses regex, NLTK stopwords when available. NLTK resources are checked and downloaded if missing.
- Caching:
  - `_load_or_compute_embeddings()` builds/validates cached embedding arrays for resolved complaints and writes `resolved_embeddings.npy` etc under cache.
- Important symbols: `model_loader.load_model`, `model_loader.predict_category`, `model_loader.find_similar_complaint`, `model_loader.predict_sla`, `model_loader.model_status`

4) secure_result/page_modules/ — Streamlit pages (UI)
Each module exposes a `run()` function and calls DB & model functions to render UI.

- `secure_result/page_modules/1_Student_Dashboard.py`
  - Symbol: `1_Student_Dashboard.run`
  - Displays summary metrics, recent results and recent complaints for logged-in student. Uses `db.get_results_by_student` and model insights rendering functions.

- `secure_result/page_modules/2_Submit_Complaint.py`
  - Symbol: `2_Submit_Complaint.run`
  - Complaint submission form (text area, course/semester selection, file upload). Shows ML prediction preview:
    - Calls `model_loader.predict_category` to display predicted category & confidence.
    - Calls `model_loader.find_similar_complaint` to show similar resolved cases; uses similarity thresholds (>=0.8 duplicate).
    - Calls `model_loader.predict_sla` to compute breach probability and median resolution time to assign risk level (Low/Medium/High).
  - On submission, calls `db.add_complaint` to store complaint.

- `secure_result/page_modules/3_My_Results.py`
  - Symbol: `3_My_Results.run`
  - Shows full results, export options, individual result details.

- `secure_result/page_modules/4_Admin_Dashboard.py`
  - Symbol: `4_Admin_Dashboard.run`
  - Admin analytics & quick actions:
    - Summary metrics (total complaints, pending, resolved).
    - Plots: category distribution and complaints over time (Plotly).
    - SLA risk analytics computed by calling `model_loader.predict_sla` across complaints.
    - Pulls results summary directly via SQLite queries in file or via `db` helper functions.

- `secure_result/page_modules/5_Admin_View_Complaints.py`
  - Symbol: `5_Admin_View_Complaints.run`
  - Detailed complaint management UI:
    - Shows cards & table views filtered/sorted by status, category or SLA risk.
    - In complaint detail: shows file downloads (from uploads path), duplicate insights (calls `model_loader.find_similar_complaint`), SLA panel (calls `model_loader.predict_sla`).
    - Communication thread rendering and admin actions: update status, override category, add resolution notes, upload resolution files.
    - Export all complaints CSV function.

- `secure_result/page_modules/6_Admin_Upload_Results.py`
  - Symbol: `6_Admin_Upload_Results.run`
  - CSV upload form (preview, validation, bulk import). Uses `db.import_results_from_dataframe()` (in db.py) to persist rows.

- `secure_result/page_modules/7_Admin_Model_Insights.py`
  - Symbol: `7_Admin_Model_Insights.run`
  - Shows model load status (`model_loader.model_status`), SLA model coefficients and top features (loads `sla_survival_model.pkl`, `sla_features.json`), dataset stats for complaints/resolved CSVs, export predictions.

Models & datasets — locations, purpose, formats
- Model folder: `secure_result/models`
  - SBERT model folder: `secure_result/models/sbert_duplicate_model/README.md` — includes a local copy of "all‑MiniLM‑L6‑v2" repository files for offline use.
  - Survival model: `sla_survival_model.pkl` (path referenced in model_loader).
  - Classifier/vectorizer/label encoder: `classifier.pkl`, `vectorizer.pkl`, `label_encoder.pkl` under models.
  - Anomaly model: `anomaly_model.pkl`
  - Datasets used for ML:
    - `data/complaints.csv` and `data/resolved_complaints.csv` inside models/data. Paths referenced by `COMPLAINTS_CSV` and `RESOLVED_COMPLAINTS_CSV` in model_loader.
    - Resolved embeddings cached: `models/cache/resolved_embeddings.npy` etc.
  - Notebooks for model development: `secure_result/models/API.ipynb`, `secure_result/models/Survival_Analysis.ipynb`.

ML stacks & algorithms
- Text classification: Scikit‑learn classifier (likely logistic regression per report) trained on TF‑IDF features saved as `classifier.pkl` + `vectorizer.pkl`.
- Duplicate detection: Sentence‑BERT (sentence-transformers) embedding model "all‑MiniLM‑L6‑v2". Embeddings computed and cached; search uses cosine similarity and thresholds: >=0.8 high duplicate, >=0.6 related.
- SLA risk: Cox Proportional Hazards model (lifelines CoxPHFitter) used to predict median resolution time & probability of breaching 7 day SLA.
- Anomaly detection: IsolationForest (scikit-learn) trained on features such as resolution time, encoded program, encoded faculty department.

Dataflow (typical complaint submission)
1. Student fills complaint form in `2_Submit_Complaint.run`.
2. On typing, system runs `predict_category` → shows predicted category & confidence; runs `find_similar_complaint` → shows similar resolved cases; runs `predict_sla` → shows predicted median days and breach probability.
3. Student submits; code calls `db.add_complaint` to insert into DB, storing predicted metadata (category/confidence/duplicate_reference).
4. Admin can view and manage in `5_Admin_View_Complaints.run` and update status or resolution.

Key outputs & return shapes (from code)
- `predict_category(text)` returns a dict with keys like `'prediction'` (category name), `'confidence'` (float) and possibly class index.
- `find_similar_complaint(text, top_k)` returns a list of dicts for top_k similar items like `{'score': 0.87, 'index': <resolved id>, 'text': '...'}`.
- `predict_sla(complaint_dict)` returns dict with `'breach_prob_at_t'` and `'predicted_median_days'`.
- `model_status()` returns `_model_info` dict with booleans and counts for loaded models/datasets.

Deployment & running
- Install dependencies: `pip install -r requirements.txt`.
- Place model files under `secure_result/models` matching expected names (`classifier.pkl`, `vectorizer.pkl`, `label_encoder.pkl`, `sbert_duplicate_model` folder, `sla_survival_model.pkl`, `sla_features.json`, `anomaly_model.pkl`).
- Initialize DB: `db.init_db()` is called by `secure_result/app.py` when run; you can run streamlit which will auto initialize if needed.
- Run app: `streamlit run secure_result/app.py`
- Note: SBERT requires sentence-transformers package; survival requires lifelines. `model_loader` handles optional availability with graceful errors; check `model_loader.load_model`.

Testing & debugging tips
- View model status in UI: open Model Insights page (admin) which calls `model_loader.model_status` and shows loaded flags and dataset rows.
- If SBERT fails to load: check `SENTENCE_TRANSFORMERS_AVAILABLE` and install `sentence-transformers`.
- If lifelines not installed: install `lifelines`.
- Check `secure_result/models/cache` for embedding cache files.
- Use the notebooks under `secure_result/models` to reproduce embedding generation (API.ipynb) or survival analysis experiments.

Security & robustness notes (from report & code)
- Passwords hashed in `db.create_user` / `verify_user`.
- File size validation on uploads (10 MB) in the complaint submission page.
- SQL parameterization: DB inserts use parameterized queries (prevents SQL injection).
- Graceful degradation: `model_loader` captures missing models and continues to serve UI with warnings.

Where to look for details (quick links)
- Application entry and routing: `secure_result/app.py` — see `main`.
- DB functions: `secure_result/db.py` — see `init_db`, `add_complaint`, `verify_user`.
- ML loading/inference: `secure_result/model_loader.py` — see `load_model`, `predict_category`, `find_similar_complaint`, `predict_sla`, `model_status`.
- UI pages: `secure_result/page_modules` — files `secure_result/page_modules/1_Student_Dashboard.py` .. `secure_result/page_modules/7_Admin_Model_Insights.py`.
- Models & cached data: `secure_result/models` and `secure_result/models/sbert_duplicate_model/README.md`.
- Project documentation: `PROJECT_REPORT.md`.

If you want, I can:
- Produce a plain-text architecture diagram mapping functions & DB tables to pages.
- Generate a checklist for deployment (packages, model files, dataset placement).
- Extract and list all DB schema SQL executed by `db.init_db()`.

Which of those would you like next?
