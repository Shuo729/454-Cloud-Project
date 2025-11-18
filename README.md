# 454-Cloud-Project
Cloud-Based Photo Sharing System

## Steps to Run the Program:
1. Get the service-account-key.json from Discord
2. Put this json file in the project folder, right next to server.py
3. Install all the required packages using: pip install -r requirements.txt
4. Set the environment variable: \
        On Windows using Command Prompt: set GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json \
        On Mac: export GOOGLE_APPLICATION_CREDENTIALS="service-account-key.json"
5. Run server.py using: python server.py