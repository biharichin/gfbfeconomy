
import os
import re
import json
import requests

# Read configuration from environment variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
# Chat IDs should be a comma-separated string in the environment variable
CHAT_IDS = os.environ.get("CHAT_IDS", "").split(',')

QUESTIONS_FILE = "indian_economy.txt"
PROGRESS_FILE = "progress.txt"
QUESTIONS_PER_DAY = 20

def parse_questions():
    """Parses the questions file and returns a list of question objects."""
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    question_blocks = content.strip().split('\n\n')
    questions = []
    
    for block in question_blocks:
        lines = block.strip().split('\n')
        if len(lines) < 6:
            continue

        # The first line is the question, which may have a number.
        question_text = lines[0]
        
        # Extract options and find the correct one
        options = []
        correct_option_id = None
        answer_text = lines[-1].replace("Answer: ", "").strip()

        for i, line in enumerate(lines[1:-1]):
            # Remove the "a) ", "b) " etc. part for the poll option
            option_text = re.sub(r"^[a-d]\)\s+", "", line)
            options.append(option_text)
            if line.startswith(answer_text + ")"):
                correct_option_id = i
        
        questions.append({
            "question": question_text,
            "options": options,
            "correct_option_id": correct_option_id
        })
    return questions

def get_progress():
    """Reads the progress file and returns the next question index to send."""
    if not os.path.exists(PROGRESS_FILE):
        return 0
    with open(PROGRESS_FILE, "r") as f:
        try:
            return int(f.read().strip())
        except ValueError:
            return 0

def save_progress(index):
    """Saves the next question index to the progress file."""
    with open(PROGRESS_FILE, "w") as f:
        f.write(str(index))

def send_poll(chat_id, question_data):
    """Sends a single poll to a specified chat."""
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN is not set.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPoll"
    
    payload = {
        "chat_id": chat_id,
        "question": question_data["question"],
        "options": json.dumps(question_data["options"]),
        "is_anonymous": False,
        "type": "quiz",
        "correct_option_id": question_data["correct_option_id"]
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        print(f"Poll sent to {chat_id}: {question_data['question']}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending poll to {chat_id}: {e}")
        print(f"Response: {response.text}")

def send_message(chat_id, text):
    """Sends a text message to a specified chat."""
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN is not set.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        print(f"Message sent to {chat_id}: {text}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to {chat_id}: {e}")

def main():
    """Main function to run the bot."""
    all_questions = parse_questions()
    start_index = get_progress()
    
    if start_index >= len(all_questions):
        print("All questions have been sent.")
        for chat_id in CHAT_IDS:
            if chat_id:
                send_message(chat_id.strip(), "All questions have been sent. We are done!")
        return

    end_index = min(start_index + QUESTIONS_PER_DAY, len(all_questions))
    questions_to_send = all_questions[start_index:end_index]
    
    for question_data in questions_to_send:
        for chat_id in CHAT_IDS:
            if chat_id:  # Ensure chat_id is not an empty string
                send_poll(chat_id.strip(), question_data)
    
    save_progress(end_index)
    print(f"Successfully sent questions {start_index + 1} to {end_index}.")

if __name__ == "__main__":
    main()
