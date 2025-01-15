import anthropic
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

api_key_ant = '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'
client = anthropic.Anthropic(api_key= api_key_ant)

TELEGRAM_BOT_TOKEN = '6723409693:AAFNJRzcsfHSYt7zcYIXpd07BuXN2baavZA'

# File reading
FILE_PATH = '/home/koded/Desktop/VA-AI/schedule.json'
with open(FILE_PATH, 'r') as file:
    json_content = file.read()

# System prompt
SYSTEM_PROMPT = '''You are a professional virtual assistant helping clients book appointments. 
Your goal is to:
- Sound natural and conversational
- Understand the client's scheduling needs
- Check availability based on a pre-defined schedule
- Be helpful and guide the client to find a suitable time slot
- Avoid revealing the internal structure of the scheduling system
- Do not provide details of the schedule, of the other events on the schedule as it is confidential and not to be accessed by the client, only thing client is entitled to is to know the free times
- When a requested time is occupied, strictly state that, do not reveal the confidential nature of the event to the client
- Do not tell the client the details are confidential.
- do not answer to questions other than about scheduling meetings

Communicate as if you're a friendly, but strict efficient scheduling assistant.'''

# User conversation histories
user_conversations = {}

def update_schedule_with_ai(conversation_history, FILE_PATH):
    """
    Use Claude to analyze conversation history and update JSON schedule
    """
    try:
        # Prepare extraction prompt
        EXTRACTION_PROMPT = '''You are an expert at extracting scheduling details from conversation history. 
        Your task is to carefully identify:
        1. The day of the week for the appointment
        2. The specific time slot of the appointment
        3. The client's name (if provided)

        Respond ONLY with a JSON object containing these fields:
        {
            "day": "monday/tuesday/etc",
            "time": "HH:MM",
            "client_name": "Client Name"
        }

        If any information is missing or unclear, return null for that field.
        Do not make up information. Only return what you can definitively extract.'''

        # Prepare messages for API call
        messages = [
            {"role": "user", "content": f"Conversation History: {json.dumps(conversation_history)}\n\n{EXTRACTION_PROMPT}"}
        ]

        # Make API call to extract booking details
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            temperature=0.2,
            system=EXTRACTION_PROMPT,
            messages=messages
        )

        # Parse the response
        try:
            booking_details = json.loads(response.content[0].text)
        except (json.JSONDecodeError, IndexError):
            print("Could not parse booking details from AI response")
            return False

        # Validate booking details
        if not booking_details or not booking_details.get('day') or not booking_details.get('time'):
            print("Insufficient booking details extracted")
            return False

        # Read existing JSON schedule
        with open(FILE_PATH, 'r') as file:
            schedule = json.load(file)

        # Find and update the specific time slot
        day = booking_details['day'].lower()
        time = booking_details['time']
        client_name = booking_details.get('client_name', 'Unknown Client')

        for time_slot in schedule['weeklySchedule'][day]:
            if time_slot['time'] == time:
                if time_slot['status'] == 'free':
                    time_slot['status'] = 'occupied'
                    time_slot['event'] = f"Meeting with {client_name}"
                    
                    # Write updated schedule back to file
                    with open(FILE_PATH, 'w') as file:
                        json.dump(schedule, file, indent=4)
                    
                    print(f"Successfully booked {day} at {time}")
                    return True
                else:
                    print(f"Time slot {time} on {day} is already occupied")
                    return False

        print(f"Could not find time slot {time} on {day}")
        return False

    except Exception as e:
        print(f"Error updating schedule with AI: {e}")
        return False

async def start(update: Update, context):
    """Send a message when the command /start is issued."""
    welcome_message = get_ai_response(update.effective_user.id, "/start")
    await update.message.reply_text(welcome_message)

async def handle_message(update: Update, context):
    """Handle incoming messages."""
    user_id = update.effective_user.id
    user_message = update.message.text.lower()

    # Check for conversation end conditions
    if user_message in ['exit', 'quit', 'bye', "that's all", 'done']:
        # Attempt to update schedule before ending conversation
        update_result = update_schedule_with_ai(user_conversations.get(user_id, []), FILE_PATH)
        
        # Prepare farewell message based on update result
        if update_result:
            farewell_message = "Thank you! Your appointment has been booked successfully. Have a great day!"
        else:
            farewell_message = "Thank you for your interest. No appointment was booked. Have a great day!"
        
        await update.message.reply_text(farewell_message)
        
        # Clear this user's conversation history
        if user_id in user_conversations:
            del user_conversations[user_id]
        return

    # Get AI response for regular messages
    ai_response = get_ai_response(user_id, user_message)
    
    # Send response back to user
    await update.message.reply_text(ai_response)

def get_ai_response(user_id, user_message):
    """Get AI response using Anthropic's Claude"""
    # Initialize conversation history for this user if not exists
    if user_id not in user_conversations:
        user_conversations[user_id] = []

    # Add user message to conversation history
    user_conversations[user_id].append({"role": "user", "content": user_message})

    # Read schedule JSON
    try:
        with open(FILE_PATH, 'r') as file:
            json_content = file.read()
    except Exception as e:
        print(f"Error reading schedule file: {e}")
        json_content = "{}"

    # Prepare API messages
    api_messages = [
        *user_conversations[user_id],
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": json_content
                },
                {
                    "type": "text",
                    "text": f"User's latest message: {user_message}"
                }
            ]
        }
    ]

    # Make API call to Claude
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            temperature=0.7,
            system=SYSTEM_PROMPT,
            messages=api_messages
        ).content[0].text
    except Exception as e:
        print(f"Error getting AI response: {e}")
        response = "Sorry, I'm experiencing technical difficulties."

    # Add AI response to conversation history
    user_conversations[user_id].append({"role": "assistant", "content": response})

    return response

def main():
    """Start the bot."""
    try:
        # Create the Application and pass it your bot's token
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Register command and message handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Start the Bot
        print("Bot is starting...")
        application.run_polling(drop_pending_updates=True)
        print("Bot is running. Press Ctrl+C to stop.")
    except Exception as e:
        print(f"Error starting bot: {e}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot stopped.")
    except Exception as e:
        print(f"Unexpected error: {e}")