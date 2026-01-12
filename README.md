# Credit-Risk Analysis Model

A comprehensive data pipeline and web application designed for credit risk analysis and personal finance management. This project processes credit application data to calculate risk scores, determines risk bands, computes personal finance metrics based on the 50/30/20 rule, and provides a user-friendly web dashboard.

## Features

- **ETL Pipeline**: Seamlessly extracts, transforms, and loads credit application data from CSV files into a MySQL database.
- **Credit Risk Scoring**: automated calculation of credit risk scores based on income, employment history, age, and family status. Assigns risk bands (Low, Medium, High).
- **Personal Finance Metrics**: Computes budget allocations (Essentials, Wants, Savings) for each applicant.
- **Web Dashboard**: A secure Flask-based web interface allowing users to:
  - Register and Login.
  - View their personal dashboard with financial overview.
  - Track income, expenses, and loans.
  - Manage bank accounts, credit cards, and stock investments.
  - Visualize financial health through key indicators.

## Project Structure

```
credit-risk-analysis-model/
├── data/
│   └── raw/                # Raw data files (e.g., application_record.csv)
├── src/
│   ├── db.py               # Database connection and table management
│   ├── etl.py              # ETL process implementation
│   ├── finance.py          # Personal finance metrics logic
│   └── risk.py             # Credit risk scoring logic
├── templates/              # HTML templates for the web application
├── app.py                  # Main Flask application entry point
├── main.py                 # Data pipeline entry point (ETL + Scoring)
├── requirements.txt        # Python dependencies
└── .env.example            # Example environment configuration
```

## Prerequisites

- **Python**: Version 3.8 or higher.
- **MySQL Server**: Ensure MySQL is installed and running.

## Installation

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd "credit-risk analysis model"
   ```

2. **Set Up Virtual Environment**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   Create a `.env` file in the root directory based on `.env.example`.
   ```bash
   cp .env.example .env
   ```
   Update the `.env` file with your MySQL credentials:
   ```ini
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=credit_engine
   SECRET_KEY=your_secret_key
   ```

## Usage

### 1. Run the Data Pipeline
Initialize the database, load data, and perform risk analysis.
```bash
python main.py
```
This script will:
- Create necessary database tables.
- Load data from `data/raw/application_record.csv`.
- Calculate risk scores and finance metrics for all applications.

### 2. Launch the Web Application
Start the Flask development server to access the dashboard.
```bash
python app.py
```
Open your browser and navigate to `http://127.0.0.1:5000`.

## Tech Stack

- **Backend**: Python, Flask
- **Database**: MySQL (PyMySQL)
- **Data Processing**: Pandas, NumPy
- **Security**: Werkzeug (Password Hashing), Cryptography
- **Configuration**: python-dotenv

## License

[MIT](LICENSE)
