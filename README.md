# Laptop Price Prediction Project

This project aims to develop a complete data analysis cycle focused on predicting laptop prices. It includes data scraping, processing, training machine learning models, and serving predictions via a web application. All content in this project is created for the IT4142E module at Hanoi University of Science and Technology.

## 🚀 How to Run the Project

This project is containerized using Docker.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) installed on your machine.

### Steps
1. **Clone the repository:**
   ```bash
   git clone https://github.com/trinhminh11/Project_DS.git
   cd Project_DS
   ```

2. **Build and Run with Docker Compose:**
   ```bash
   docker compose up -d --build
   ```

   *Note: Ensure the `app/entrypoint.sh` file has LF (Unix) line endings if you encounter errors on Windows.*

### Accessing the Applications
- **Flask Web Application**: [http://localhost:8000](http://localhost:8000)
- **Airflow Webserver**: [http://localhost:8080](http://localhost:8080) (User/Pass: `admin`/`admin`)

## ⚠️ Important: First Run Setup

When you first launch the application, the database will be empty. If you visit the Flask app ([localhost:8000](http://localhost:8000)), you will see a "Database Not Initialized" page.

**You must populate the data by running an Airflow DAG.**

1. Go to Airflow at [http://localhost:8080](http://localhost:8080) and login with `admin` / `admin`.
2. Unpause and trigger **one** of the following DAGs depending on your needs:

   - **`load_db_dag`** (~1 min): ⚡ **Recommended for quick start.** Loads pre-existing data, trains models, and prepares EDA. Use this to get the app running primarily.
   - **`main_dag`** (~5-15 mins): Loads data, retrains models, and runs EDA. Useful if you want to verify the training pipeline.
   - **`run_all_dag`** (~10 hours): 🕷️ **Full Cycle.** Scrapes *new* data from the web, loads it, trains models, and runs EDA. Only use this if you want to refresh the entire dataset from scratch.

3. Wait for the DAG to complete (check "Graph View" for progress).
4. Refresh the [Flask App](http://localhost:8000) to see the prediction interface.

## 📱 Web Application Features

- **Predictor**: Estimate laptop prices based on specifications (CPU, RAM, Storage, etc.).
- **Data Analysis**: View generated Exploratory Data Analysis (EDA) reports in HTML or download as PDF.
- **Database**: Explore the raw data stored in the database and download as CSV.

## 📂 Project Structure & Source Code

For examination purposes, here is how the project is organized:

### 1. Scraped Data
- Located in: `app/data_analysis/data`
- Stored as CSV files, organized by month/year.
- Raw temporary data is in `app/temp`.

### 2. Analysis (EDA)
- **Source**: `app/data_analysis/EDA.ipynb` (Jupyter Notebook).
- **Output**: `app/data_analysis/results/eda` (Generated HTML reports).

### 3. Machine Learning Models
- **Location**: `app/data_analysis/results/trained_models`
- **Format**: `.joblib` files.
- **Code**:
  - Training: `app/data_analysis/train.py`
  - Preprocessing: `app/data_analysis/preprocess.py`
  - Prediction: `app/data_analysis/predict.py`

### 4. Database
- **Schema & SQL**: `app/airflow/dags/database/sql_helper.py` handles table creation and data insertion.

### 5. Web Scraper
- **Location**: `app/scraper`
- **Spiders**: `app/scraper/scraper/spiders`
  - `base_laptopshop_spider.py`: Base class.
  - Specific spiders for different retailers.
- **Pipelines**: `app/scraper/scraper/pipelines` for data transformation.

---
We hope you enjoy exploring our project!
