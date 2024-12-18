# Cannibals and Missionaries Gemini Powered Game

## Description
Lake Crossing Game is a puzzle game based on the classic "Missionaries and Cannibals" problem, enhanced with AI features. The objective is to move all the priests and carnivores from one side of a lake to the other using a boat, while following specific rules. The game features AI-powered hints, voice narration, and real-time analytics.

## Features
- Interactive gameplay with intuitive controls
- AI-powered hints using Google's Gemini API
- Voice narration using Google Text-to-Speech
- Real-time game analytics using Google Cloud Functions
- Firebase integration for game state persistence
- Performance tracking and statistics
- Best score tracking

## Requirements
- Python 3.9 or higher
- Required Python packages (install via `pip install -r requirements.txt`):
  ```
  pygame==2.1.2
  google-generativeai
  google-api-core
  firebase-admin
  google-cloud-texttospeech
  functions-framework
  ```

## Google Cloud Setup
1. Enable the following APIs in your GCP project:
   - Gemini API
   - Cloud Functions
   - Text-to-Speech API
   - Firebase/Firestore
   - Gemini API

2. Create Service Account Keys for text to speech and firebase:
   - **Firebase:** Create a "Firebase Admin SDK service account" key with Role: "Firebase Admin SDK Administrator Service Agent". Download the JSON key file (e.g., `firebase_adminsdk.json`).
   - **Text-to-Speech:** Create a Google Cloud Text-to-Speech service account key with Role: "Cloud Speech-to-Text Service Agent" and "Editor". Download the JSON key file (e.g., `text_to_speech.json`).

3. Get Gemini API Key:
   - Go to the Google AI Studio.
   - Create a new project or select an existing one.
   - Enable the Gemini API.
   - Create an API key.  Keep this key secure; do not commit it to version control.

4. Required Credentials (Place in project root):
   - Firebase Admin SDK credentials (`genai-lab-414409-firebase-adminsdk-h2gqi-49e8c4dcd6.json`)
   - Google Cloud Text-to-Speech credentials (`genai-lab-414409-c2259d949e8c.json`)
   - Gemini API key

5. Authenticate for Text-to-Speech:
   Before deploying the cloud function, authenticate with your Google Cloud account for Text-to-Speech:
   ```bash
   gcloud auth login
   ```


## Installation
1. Clone the repository
2. Install requirements:
   ```
   pip3 install -r requirements.txt
   ```
3. Place credential files in project root
4. Deploy the analytics cloud function:
   ```
   cd cloud_functions/analytics
   chmod +x deploy.sh
   ./deploy.sh
   ```

## Game Rules
1. Move all characters (3 priests and 3 carnivores) across the lake
2. The boat can carry maximum 2 characters
3. Carnivores cannot outnumber priests on any shore
4. Perfect solution takes 11 moves
5. The game tracks mistakes and provides analytics

## Game Controls
- Click characters to move them to/from the boat
- "Move Boat" button to cross the lake
- "Hint" button for AI-powered suggestions
- "Narration" toggle for voice feedback
- "Show Stats" for game analytics
- "Try Again"/"Play Again" to restart after game over

## Project Structure
```
lake-crossing-game/
├── lake_crossing_game_gemini7.py  # Final game 
├── requirements.txt
├── README.md
├── cloud_functions/
│   └── analytics/
│       ├── main.py                
│       ├── requirements.txt
│       └── deploy.sh
├── background.png
├── boat.png
├── button.png
├── carnivore.png
└── priest.png
```

## Features in Detail

### AI-Powered Hints
- Context-aware suggestions using Gemini API
- Based on optimal solution path
- Adapts to current game state

### Voice Narration
- Real-time game state narration
- Uses Google Text-to-Speech
- Toggle-able during gameplay

### Game Analytics
- Tracks game sessions and moves
- Analyzes common mistakes
- Shows performance metrics:
  - Success rate
  - Average moves
  - Perfect games count
  - Game duration

### Firebase Integration
- Stores game sessions
- Tracks moves and mistakes
- Maintains best scores
- Real-time data updates

## Troubleshooting

1. Firebase Connection:
   - Check credential file paths
   - Verify project ID and permissions

2. Cloud Function:
   - Ensure function is deployed
   - Check function URL in game code
   - Verify IAM permissions

3. Voice Narration:
   - Check Text-to-Speech API is enabled
   - Verify credential file
   - Check audio device settings

## Development Notes
- Game uses Pygame for graphics and interaction
- Cloud function analyzes gameplay patterns
- Firebase stores game state and analytics
- Gemini API provides intelligent hints
- Text-to-Speech adds audio feedback

## Credits

Sarthak Kesarwani [LinkedIN](https://www.linkedin.com/in/sarthak-kesarwani/), [Github](https://github.com/operator670)\
<br>
Deepansh Singh [LinkedIN](https://www.linkedin.com/in/deepansharya1111/)

Created using:
- Python/Pygame
- Google Cloud Platform
- Firebase
- Gemini API - gemini-2.0-flash-exp
- Cloud Run Functions
- Text-to-Speech API


## License
MIT License

Copyright (c) [year] [fullname]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Enjoy your childhood memories with this Lake crossing Game with AI features with Gemini and GCP!
