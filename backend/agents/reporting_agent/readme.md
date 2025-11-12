# 🧠 Medical Reporting Agent (Dermatology & Oral Health)

An AI-powered reporting service that generates **structured medical summaries** for dermatology and oral health consultations.  
It integrates **Vertex AI Gemini Vision**, **Firestore**, and **GCS** to analyze chat history, images, and metadata — delivering a detailed, empathetic report ready for end-user presentation.

---

## 🚀 Overview

This Reporting Agent acts as a backend microservice running on **Google Cloud Run**.  
It pulls chat, metadata, and image data from **Firebase** and **Google Cloud Storage (GCS)**, runs multimodal inference using **Vertex AI Gemini**, and returns a structured JSON report.

### Supported Specialties
- 🩺 **Dermatology** (skin diseases, rashes, lesions)
- 🦷 **Oral Health** (gum disease, dental issues, mouth abnormalities)

---

## 🧩 Architecture

**Core Components**
- **Flask REST API** (`app.py`)
- **Vertex AI Gemini Vision API** (for multimodal analysis)
- **Firestore + Firebase Storage** (for chat and metadata)
- **Dockerized Cloud Run Deployment** (`Dockerfile`, `deploy.sh`)

**Workflow**
1. Fetch latest chat and metadata from Firestore (via `chat_id`)
2. Retrieve most recent image from GCS
3. Run Gemini Vision analysis on the image
4. Use Gemini LLM to generate a structured JSON report
5. Return the result to frontend or downstream systems

---

## 🛠️ Tech Stack

| Component | Technology |
|------------|-------------|
| Backend Framework | Flask |
| AI Models | Google Vertex AI Gemini 2.0 Flash |
| Storage | Firestore / Firebase Storage |
| Cloud Platform | Google Cloud Run |
| Deployment | Docker + Cloud Build |
| Language | Python 3.10+ |

---

## ⚙️ Deployment (Cloud Run)

Run the following commands to deploy directly from your local machine:

```bash
chmod +x deploy.sh
./deploy.sh
