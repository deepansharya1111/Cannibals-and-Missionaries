#!/bin/bash
gcloud functions deploy analyze_gameplay \
    --runtime python39 \
    --trigger-http \
    --allow-unauthenticated \
    --region=us-central1 \
    --project=genai-lab-414409 \
    --service-account=genai-lab-414409@appspot.gserviceaccount.com \
    --source=. \
    --entry-point=analyze_gameplay 