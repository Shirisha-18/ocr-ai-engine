# OCR-AI-Engine

![Python](https://img.shields.io/badge/python-3.12-blue)
![Google Cloud](https://img.shields.io/badge/GCP-Vision_API-orange)
![License](https://img.shields.io/badge/license-MIT-green)

> Extract text from images and scanned documents using **Google Cloud Vision API**.  
> Designed as a foundation for AI-powered OCR pipelines and future RAG / LLM integrations.


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


## Environment Setup

**1. Create and activate Conda environment**

```
conda create -n gcp-cloud-vision python=3.12 -y
conda activate gcp-cloud-vision
```

**2. Install required packages**
```
Install required packages
```

## Google Cloud Vision Setup

1. Go to Google Cloud Console
2. Create a project and **enable Vision API**
3. Under **IAM & Admin → Service Accounts**, create a **service account key**
4. Download the **JSON key file**


## Add Images
Place all images in: `ocr-ai-engine/data/raw/`
Supported formats: `.jpg`, `.jpeg`, `.png`, `.tif`, `.bmp`

## Run the Code
From the **project root**, run:

```
conda activate gcp-cloud-vision
python src/google_cloud_vision.py
```

## Future Enhancements

1. Docker container for reproducibility
2. Integration with **LangChain / RAG** for text analysis
3. Store OCR results in database / JSON
4. Large-scale batch processing with **Google Cloud Storage**


