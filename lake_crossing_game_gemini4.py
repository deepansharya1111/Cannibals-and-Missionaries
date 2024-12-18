import pygame
import sys
import os
import google.generativeai as genai
import textwrap
from google.api_core import retry
from google.api_core.exceptions import ResourceExhausted
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import datetime
from google.cloud import texttospeech
import pygame.mixer
import tempfile
import os
from google.oauth2 import service_account

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class LakeCrossingGame:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.music.set_volume(1.0)  # Set volume to maximum
        print(f"Pygame mixer initialized. Volume: {pygame.mixer.music.get_volume()}")  # Debug print
        self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Lake Crossing Game")
        
        # Initialize db to None before setup_firebase
        self.db = None
        
        self.reset_game()
        
        self.font = pygame.font.Font(None, 36)
        self.button_font = pygame.font.Font(None, 24)  # Smaller font for buttons
        self.hint_font = pygame.font.Font(None, 24)  # Smaller font for hints and narration
        self.load_images()
        self.create_buttons()
        self.setup_gemini()
        self.narration = ""
        self.hint = ""
        self.hint_timer = 0
        self.narration_timer = 0
        self.narration_enabled = True
        self.last_move_state = self.get_game_state_string()
        
        # Initialize Firebase after everything else
        self.setup_firebase()
        
        self.setup_text_to_speech()
        self.audio_playing = False
        
    def setup_firebase(self):
        try:
            print("Starting Firebase setup...")  # Debug print
            # Initialize Firebase with your credentials
            cred = credentials.Certificate('YOUR_FIREBASE_CREDENTIALS_JSON')
            print("Credentials loaded")  # Debug print
            
            firebase_admin.initialize_app(cred)
            print("Firebase app initialized")  # Debug print
            
            # Initialize Firestore
            self.db = firestore.client()
            print("Firestore client created")  # Debug print
            
            # Test the connection
            test_ref = self.db.collection('test').document()
            test_ref.set({'test': 'connection'})
            print("Test document created successfully")  # Debug print
            
            print("Firebase setup completed successfully")
        except Exception as e:
            print(f"Detailed error in Firebase setup: {str(e)}")  # More detailed error
            self.db = None

    def save_moves_to_firebase(self):
        if self.db is None:
            print("Database connection is None, cannot save data")  # Debug print
            return
            
        try:
            # Create a game session document
            game_ref = self.db.collection('game_sessions').document()
            
            # Create data to save
            data = {
                'moves': self.moves,
                'timestamp': datetime.datetime.now(),
                'win': self.win,
                'game_state': self.get_game_state_string()
            }
            print(f"Attempting to save data to Firebase: {data}")  # Debug print
            
            # Save game data
            game_ref.set(data)
            print(f"Successfully saved game session with {self.moves} moves to Firebase")
        except Exception as e:
            print(f"Detailed error saving to Firebase: {str(e)}")  # More detailed error

    def reset_game(self):
        self.left_shore = {"priests": 3, "carnivores": 3}
        self.right_shore = {"priests": 0, "carnivores": 0}
        self.boat_position = "left"
        self.boat = {"priests": 0, "carnivores": 0}
        self.moves = 0
        self.boat_x = 200
        self.boat_speed = 5
        self.moving_boat = False
        self.game_over = False
        self.win = False
        
        # Fetch best score when starting new game
        self._best_score = self.fetch_best_score_from_firebase()

    def load_images(self):
        self.background = pygame.transform.scale(pygame.image.load(resource_path("background.png")).convert(), (self.width, self.height))
        self.priest_img = self.load_and_scale("priest.png", (50, 50))
        self.carnivore_img = self.load_and_scale("carnivore.png", (50, 50))
        self.boat_img = self.load_and_scale("boat.png", (100, 60))
        self.button_img = self.load_and_scale("button.png", (120, 50))

    def load_and_scale(self, image_name, size):
        return pygame.transform.scale(pygame.image.load(resource_path(image_name)).convert_alpha(), size)

    def create_buttons(self):
        self.move_boat_button = pygame.Rect(340, 20, 120, 50)
        self.try_again_button = pygame.Rect(250, 300, 120, 50)
        self.end_game_button = pygame.Rect(430, 300, 120, 50)
        self.hint_button = pygame.Rect(580, 20, 120, 50)
        self.narrate_button = pygame.Rect(580, 80, 120, 50)

    def setup_gemini(self):
        genai.configure(api_key='YOUR_GEMINI_API_KEY_HERE')
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.retry_config = retry.Retry(
            initial=1.0,  # Initial retry delay in seconds
            maximum=60.0,  # Maximum retry delay
            multiplier=2.0,  # Delay multiplier
            predicate=retry.if_exception_type(ResourceExhausted),
            deadline=300.0  # Overall deadline for retries
        )

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        
        self.draw_shore(self.left_shore, 50, True)
        self.draw_shore(self.right_shore, 700, False)
        
        self.screen.blit(self.boat_img, (self.boat_x, 500))
        
        for i, character in enumerate(["carnivores", "priests"]):
            for j in range(self.boat[character]):
                self.screen.blit(self.carnivore_img if character == "carnivores" else self.priest_img,
                                 (self.boat_x + 10 + j * 55, 460 + i * 50))
        
        self.draw_button(self.move_boat_button, "Move Boat")
        
        # Combined Firebase status and moves counter
        if self.db is not None:
            moves_text = self.font.render(f"Moves: {self.moves} | Firebase: Connected", True, (255, 255, 255))
            self.screen.blit(moves_text, (10, 10))
        else:
            error_text = self.font.render("Firebase: Disconnected", True, (255, 0, 0))  # Red text
            self.screen.blit(error_text, (10, 10))
        
        # Add scores display
        self.draw_scores()
        
        if self.game_over:
            print("Drawing game over screen")  # Debug print
            self.draw_game_over_screen()
        
        self.draw_button(self.hint_button, "Hint")
        self.draw_button(self.narrate_button, "Narration: ON" if self.narration_enabled else "Narration: OFF")
        
        self.draw_hint()
        self.draw_narration()
        
        pygame.display.flip()

    def draw_shore(self, shore, x, is_left):
        for i, character in enumerate(["carnivores", "priests"]):
            for j in range(shore[character]):
                if is_left:
                    pos_x = x - 30 + j * 60  # Moved left side sprites 30 pixels to the left
                else:
                    pos_x = x + 100 - (j + 1) * 60
                self.screen.blit(self.carnivore_img if character == "carnivores" else self.priest_img,
                                 (pos_x, 400 + i * 60))

    def draw_button(self, button_rect, text):
        self.screen.blit(self.button_img, button_rect)
        text_surf = self.button_font.render(text, True, (255, 255, 255))  # White text
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.screen.blit(text_surf, text_rect)

    def draw_game_over_screen(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        if self.win:
            text = self.font.render(f"Congratulations! You've won in {self.moves} moves.", True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.width // 2, 200))
            self.screen.blit(text, text_rect)
            
            play_again_button = pygame.Rect(0, 0, 120, 50)
            play_again_button.center = (self.width // 2, 300)  # Centered and moved down by 150 pixels
            self.draw_button(play_again_button, "Play Again")
            self.try_again_button = play_again_button  # Update the button rect for click detection
        else:
            text = self.font.render("Game over! The carnivores have eaten the priests.", True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.width // 2, 200))
            self.screen.blit(text, text_rect)
            
            self.draw_button(self.try_again_button, "Try Again")
            self.draw_button(self.end_game_button, "End Game")

    def handle_click(self, pos):
        x, y = pos
        if self.game_over:
            if self.try_again_button.collidepoint(pos):
                self.reset_game()
            elif self.end_game_button.collidepoint(pos) and not self.win:
                pygame.quit()
                sys.exit()
        else:
            if self.move_boat_button.collidepoint(pos) and not self.moving_boat:
                self.start_boat_movement()
            else:
                self.handle_character_click(x, y)
        
        if self.hint_button.collidepoint(pos):
            self.get_hint()
        elif self.narrate_button.collidepoint(pos):
            self.narration_enabled = not self.narration_enabled

    def handle_character_click(self, x, y):
        shore = self.left_shore if self.boat_position == "left" else self.right_shore
        shore_x = 20 if self.boat_position == "left" else 800  # Adjusted left shore x to match new position
        boat_chars = sum(self.boat.values())

        print(f"Click at ({x}, {y})")  # Debug print

        # Check if clicking on the boat
        if self.boat_x < x < self.boat_x + 100 and 460 < y < 560:
            print("Clicked on boat")  # Debug print
            if 460 < y < 510 and self.boat["carnivores"] > 0:
                self.move_character("carnivores", from_boat=True)
            elif 510 < y < 560 and self.boat["priests"] > 0:
                self.move_character("priests", from_boat=True)
        # Check if clicking on the shore
        else:
            shore_width = 210  # Increased to account for the wider clickable area on the left
            shore_start = shore_x - shore_width if self.boat_position == "right" else shore_x
            shore_end = shore_start + shore_width

            print(f"Shore area: {shore_start} to {shore_end}")  # Debug print
            
            if shore_start <= x <= shore_end:
                print("Clicked on shore")  # Debug print
                if 400 <= y < 450 and shore["carnivores"] > 0 and boat_chars < 2:
                    self.move_character("carnivores", from_boat=False)
                elif 450 <= y < 500 and shore["priests"] > 0 and boat_chars < 2:
                    self.move_character("priests", from_boat=False)

        print(f"After click - Boat: {self.boat}, Left Shore: {self.left_shore}, Right Shore: {self.right_shore}")  # Debug print

    def move_character(self, character, from_boat=False):
        shore = self.left_shore if self.boat_position == "left" else self.right_shore
        if from_boat:
            if self.boat[character] > 0:
                self.boat[character] -= 1
                shore[character] += 1
                print(f"Moved {character} from boat to shore")  # Debug print
        else:
            if shore[character] > 0 and sum(self.boat.values()) < 2:
                shore[character] -= 1
                self.boat[character] += 1
                print(f"Moved {character} from shore to boat")  # Debug print
            else:
                print(f"Failed to move {character} - Shore: {shore[character]}, Boat: {sum(self.boat.values())}")  # Debug print
        
        self.check_game_state()  # Check game state after every movement
        
        # Get narration after the move if enabled
        if self.narration_enabled:
            self.get_narration()
        
        # Update last move state
        self.last_move_state = self.get_game_state_string()

    def start_boat_movement(self):
        if sum(self.boat.values()) > 0:
            self.moving_boat = True

    def update_boat_position(self):
        if self.moving_boat:
            if self.boat_position == "left":
                self.boat_x += self.boat_speed
                if self.boat_x >= 500:
                    self.finish_boat_movement()
            else:
                self.boat_x -= self.boat_speed
                if self.boat_x <= 200:
                    self.finish_boat_movement()
        
        if self.hint_timer > 0:
            self.hint_timer -= 1
        if self.narration_timer > 0:
            self.narration_timer -= 1

    def finish_boat_movement(self):
        if self.db is None:
            print("Cannot update moves - Firebase not connected")
            return
            
        self.boat_position = "right" if self.boat_position == "left" else "left"
        self.moves += 1
        self.moving_boat = False
        print(f"Boat movement finished. Position: {self.boat_position}, Moves: {self.moves}")
        self.check_game_state()
        
        # Save moves after each boat movement
        self.save_moves_to_firebase()
        
        if self.narration_enabled:
            self.get_narration()
        
        self.last_move_state = self.get_game_state_string()

    def check_game_state(self):
        if self.is_win_state():
            self.game_over = True
            self.win = True
            # Save final game state to Firebase
            self.save_moves_to_firebase()
            print("Game over: Win state")
        elif not self.is_valid_state():
            self.game_over = True
            self.win = False
            # Save final game state to Firebase
            self.save_moves_to_firebase()
            print("Game over: Invalid state")
        print(f"Game state checked - Game over: {self.game_over}, Win: {self.win}")
        print(f"Current state - Left: {self.left_shore}, Right: {self.right_shore}, Boat: {self.boat}, Boat position: {self.boat_position}")

    def is_valid_state(self):
        for shore in [self.left_shore, self.right_shore]:
            shore_priests = shore["priests"]
            shore_carnivores = shore["carnivores"]
            if self.boat_position == "left" and shore == self.left_shore:
                shore_priests += self.boat["priests"]
                shore_carnivores += self.boat["carnivores"]
            elif self.boat_position == "right" and shore == self.right_shore:
                shore_priests += self.boat["priests"]
                shore_carnivores += self.boat["carnivores"]
            if shore_priests > 0 and shore_carnivores > shore_priests:
                return False
        return True

    def is_win_state(self):
        win_condition = (self.right_shore["priests"] == 3 and 
                         self.right_shore["carnivores"] == 3 and
                         self.left_shore["priests"] == 0 and 
                         self.left_shore["carnivores"] == 0 and
                         self.boat["priests"] == 0 and 
                         self.boat["carnivores"] == 0 and
                         self.boat_position == "right")
        print(f"Win state check:")
        print(f"Right shore: {self.right_shore}")
        print(f"Left shore: {self.left_shore}")
        print(f"Boat: {self.boat}")
        print(f"Boat position: {self.boat_position}")
        print(f"Win condition met: {win_condition}")
        return win_condition

    def get_hint(self):
        game_state = self.get_game_state_string()
        
        prompt = f"""
        You are an AI assistant for the Lake Crossing Game. The current game state is:

        {game_state}

        Provide a strategic hint for the player's next move. The hint should:
        1. Be very concise (max 100 characters)
        2. Guide the player towards a valid and safe move
        3. Consider these rules:
           - The boat can carry at most two characters
           - There must always be at least as many priests as carnivores on each shore, unless there are no priests
           - The goal is to move all characters to the right shore.
        4. Never suggest moving both priests first, as this leads to an immediate loss
        5. Focus on maintaining balance and safety on both shores

        Hint (max 100 characters):
        """

        try:
            response = self.retry_config(self.model.generate_content)(prompt)
            self.hint = response.text.strip()
            self.hint_timer = 300  # Display hint for 5 seconds (60 fps * 5)
            
            # Add this line to speak the hint
            self.speak_text(self.hint)
            
        except Exception as e:
            print(f"Error getting hint: {e}")
            self.hint = "Consider balancing priests and carnivores on both shores."
            self.hint_timer = 300
            # Speak the default hint if there's an error
            self.speak_text(self.hint)

    def get_narration(self):
        current_state = self.get_game_state_string()
        
        prompt = f"""
        You are a creative narrator for the Lake Crossing Game. The current game state is:

        {current_state}

        Provide a brief, engaging narration about the current situation. Your narration should:
        1. Be very concise (max 100 characters)
        2. Focus on the tension between the carnivores and priests
        3. Avoid repetitive phrases and questioning tones
        4. Be varied in tone (sometimes humorous, sometimes tense)
        5. Portray the carnivores as predators eager to outnumber the priests

        Narration (max 100 characters):
        """

        try:
            response = self.retry_config(self.model.generate_content)(prompt)
            self.narration = response.text.strip()
            self.narration_timer = 300
            
            # Add this line to speak the narration
            self.speak_text(self.narration)
            
        except Exception as e:
            print(f"Error getting narration: {e}")
            self.narration = "The tension rises as the journey continues..."
            self.narration_timer = 300
            self.speak_text(self.narration)

    def get_game_state_string(self):
        return f"""
        Left shore: {self.left_shore}
        Right shore: {self.right_shore}
        Boat: {self.boat}
        Boat position: {self.boat_position}
        Moves: {self.moves}
        """

    def draw_hint(self):
        if self.hint and self.hint_timer > 0:
            hint_surface = pygame.Surface((600, 100), pygame.SRCALPHA)
            hint_surface.fill((0, 0, 0, 180))
            wrapped_text = textwrap.wrap(self.hint, width=70)  # Increased width for wrapping
            y_offset = 10
            for line in wrapped_text:
                hint_text = self.hint_font.render(line, True, (255, 255, 255))
                hint_rect = hint_text.get_rect(center=(300, 20 + y_offset))
                hint_surface.blit(hint_text, hint_rect)
                y_offset += 25  # Reduced vertical spacing
            self.screen.blit(hint_surface, (100, 450))

    def draw_narration(self):
        if self.narration and self.narration_timer > 0:
            narration_surface = pygame.Surface((700, 100), pygame.SRCALPHA)
            narration_surface.fill((0, 0, 0, 180))
            wrapped_text = textwrap.wrap(self.narration, width=80)  # Increased width for wrapping
            y_offset = 10
            for line in wrapped_text:
                narration_text = self.hint_font.render(line, True, (255, 255, 255))
                narration_rect = narration_text.get_rect(center=(350, 20 + y_offset))
                narration_surface.blit(narration_text, narration_rect)
                y_offset += 25  # Reduced vertical spacing
            self.screen.blit(narration_surface, (50, 50))

    def draw_scores(self):
        """Draw best score and recent games on screen"""
        if not hasattr(self, '_best_score'):
            self._best_score = self.fetch_best_score_from_firebase()
        
        if self._best_score is not None:
            best_score_text = self.font.render(f"Best: {self._best_score}", True, (255, 255, 255))
            self.screen.blit(best_score_text, (10, 50))

    def fetch_best_score_from_firebase(self):
        """Fetch the best (lowest) number of moves from winning games"""
        if self.db is None:
            return None
            
        try:
            # Query winning games, ordered by moves
            games_ref = self.db.collection('game_sessions')
            query = games_ref.where('win', '==', True).order_by('moves').limit(1)
            docs = query.get()
            
            for doc in docs:
                best_score = doc.to_dict()
                print(f"Best score fetched: {best_score['moves']} moves")
                return best_score['moves']
            
            return None  # Return None if no winning games found
        except Exception as e:
            print(f"Error fetching best score: {e}")
            return None

    def fetch_recent_games_from_firebase(self, limit=5):
        """Fetch the most recent game sessions"""
        if self.db is None:
            return []
            
        try:
            # Query recent games, ordered by timestamp
            games_ref = self.db.collection('game_sessions')
            query = games_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
            docs = query.get()
            
            recent_games = []
            for doc in docs:
                game_data = doc.to_dict()
                recent_games.append(game_data)
                print(f"Recent game: {game_data['moves']} moves, Won: {game_data['win']}")
            
            return recent_games
        except Exception as e:
            print(f"Error fetching recent games: {e}")
            return []

    def setup_text_to_speech(self):
        """Initialize the Text-to-Speech client"""
        try:
            # Load credentials explicitly
            tts_credentials = service_account.Credentials.from_service_account_file(
                'YOUR_TEXT_TO_SPEECH_SERVICE_ACCOUNT_CREDENTIALS_JSON'
            )
            self.tts_client = texttospeech.TextToSpeechClient(credentials=tts_credentials)
            self.voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="en-IN-Standard-B",
                ssml_gender=texttospeech.SsmlVoiceGender.MALE
            )
            self.audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            print("Text-to-Speech setup successful")
        except Exception as e:
            print(f"Error setting up Text-to-Speech: {e}")
            self.tts_client = None

    def speak_text(self, text):
        """Convert text to speech and play it"""
        if self.tts_client is None or not self.narration_enabled:
            print("Speech skipped - TTS client is None or narration disabled")  # Debug print
            return
            
        try:
            print(f"Attempting to speak text: {text}")  # Debug print
            
            # Stop any currently playing audio
            if self.audio_playing:
                pygame.mixer.music.stop()
            
            # Create synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Perform text-to-speech request
            print("Requesting speech synthesis...")  # Debug print
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=self.voice,
                audio_config=self.audio_config
            )
            print("Speech synthesis completed")  # Debug print
            
            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio:
                temp_audio.write(response.audio_content)
                temp_audio_path = temp_audio.name
                print(f"Audio saved to temporary file: {temp_audio_path}")  # Debug print
            
            # Play the audio
            print("Attempting to play audio...")  # Debug print
            pygame.mixer.music.load(temp_audio_path)
            pygame.mixer.music.play()
            print("Audio playback started")  # Debug print
            self.audio_playing = True
            
            # Delete the temporary file after a delay
            def cleanup_audio():
                pygame.time.wait(5000)  # Wait 5 seconds
                try:
                    os.remove(temp_audio_path)
                    print("Temporary audio file cleaned up")  # Debug print
                except:
                    print("Failed to clean up temporary audio file")  # Debug print
                    pass
                self.audio_playing = False
            
            # Start cleanup in a new thread
            import threading
            threading.Thread(target=cleanup_audio).start()
            
        except Exception as e:
            print(f"Detailed error in text-to-speech: {str(e)}")  # More detailed error message
            print(f"Error type: {type(e)}")  # Print error type

    def run(self):
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
            
            self.update_boat_position()
            self.draw()
            clock.tick(60)

if __name__ == "__main__":
    game = LakeCrossingGame()
    game.run()
