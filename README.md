# 📝 OCR-AI-Engine

> Extract text from images and scanned documents using **Google Cloud Vision API**.  
> Designed as a foundation for AI-powered OCR pipelines and future RAG / LLM integrations.

---

## 📁 Project Structure


```
├── LICENSE            <- Open-source license if one is chosen
├── README.md          <- The top-level README for developers using this project
├── data
│   ├── external       <- Data from third party sources
│   ├── interim        <- Intermediate data that has been transformed
│   ├── processed      <- The final, canonical data sets for modeling
│   └── raw            <- The original, immutable data dump
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
└── src                         <- Source code for this project
    │
    ├── __init__.py             <- Makes src a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── dataset.py              <- Scripts to download or generate data
    │
    ├── features.py             <- Code to create features for modeling
    │
    │    
    ├── modeling                
    │   ├── __init__.py 
    │   ├── predict.py          <- Code to run model inference with trained models          
    │   └── train.py            <- Code to train models
    │
    ├── plots.py                <- Code to create visualizations 
    │
    └── services                <- Service classes to connect with external platforms, tools, or APIs
        └── __init__.py 
```

--------

# 📝 OCR-AI-Engine

![Python](https://img.shields.io/badge/python-3.12-blue)
![Google Cloud](https://img.shields.io/badge/GCP-Vision_API-orange)
![License](https://img.shields.io/badge/license-MIT-green)

> Extract text from images and scanned documents using **Google Cloud Vision API**.  
> Designed as a foundation for AI-powered OCR pipelines and future RAG / LLM integrations.

---

## 📁 Project Structure

├── LICENSE <- Open-source license if one is chosen
├── README.md <- This file
├── data
│ ├── external <- Data from third party sources
│ ├── interim <- Intermediate data that has been transformed
│ ├── processed <- The final, canonical data sets for modeling
│ └── raw <- Original, immutable data dump (images for OCR)
│
├── models <- Trained and serialized models, model predictions, or summaries
│
├── notebooks <- Jupyter notebooks (optional)
│
├── references <- Data dictionaries, manuals, explanatory materials
│
├── reports <- Generated analysis (HTML, PDF, LaTeX, etc.)
│ └── figures <- Graphics and figures
│
├── requirements.txt <- Optional dependencies list
│
└── src <- Source code
├── init.py <- Makes src a Python module
├── google_cloud_vision.py <- Main OCR script
├── my_timer.py <- Helper timer
├── vision_key.json <- Google Cloud Vision API credentials (ignored in git)
└── services <- Optional service modules for API connections

yaml
Copy code

---

## ⚙️ Environment Setup

1. **Create and activate Conda environment**
```bash
conda create -n gcp-cloud-vision python=3.12 -y
conda activate gcp-cloud-vision
Install required packages

bash
Copy code
conda install -c conda-forge pillow=10.1.0 pandas=2.1.2 google-cloud-vision=3.4.5 scikit-learn=1.3.2 ipykernel jupyterlab notebook -y
Register the environment in Jupyter (optional)

bash
Copy code
python -m ipykernel install --user --name=gcp-cloud-vision
🔑 Google Cloud Vision Setup
Go to Google Cloud Console

Create a project and enable Vision API

Under IAM & Admin → Service Accounts, create a service account key

Download the JSON key and rename it to:

pgsql
Copy code
vision_key.json
Place it in:

bash
Copy code
ocr-ai-engine/src/
Ensure .gitignore includes:

bash
Copy code
# Google Cloud Vision API key
vision_key.json
🖼️ Add Images
Place all images in:

bash
Copy code
ocr-ai-engine/data/raw/
Supported formats: .jpg, .jpeg, .png, .tif, .bmp

Example:

bash
Copy code
data/raw/
├── patent1.jpg
├── document2.png
├── receipt3.jpeg
▶️ Run the OCR Script
From the project root, run:

bash
Copy code
conda activate gcp-cloud-vision
python src/google_cloud_vision.py
The program prints each image name and extracted text.

Execution time is displayed at the end.

🧾 Example Output
vbnet
Copy code
==============================
Image: patent1.jpg
Detected text:
United States Patent Office
...
Elapsed time to run main: 5.4321 seconds
⚠️ Troubleshooting
Error	Fix
DefaultCredentialsError	Ensure vision_key.json path is correct in src/
403 Permission Denied	Enable Vision API & billing in GCP
FileNotFoundError	Confirm images are in data/raw/
ModuleNotFoundError: google.cloud	Reinstall: conda install -c conda-forge google-cloud-vision

🌟 Future Enhancements
Docker container for reproducibility

Integration with LangChain / RAG for text analysis

Store OCR results in database / JSON

Large-scale batch processing with Google Cloud Storage

🛡️ Security
Never commit vision_key.json

Always include it in .gitignore

