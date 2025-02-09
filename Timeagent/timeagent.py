import os
from datetime import datetime
import anthropic
import tzlocal

class ClaudeTimeBot:
    def __init__(self, api_key: str):
        """
        Initialize the Claude Time Bot with your API key.
        
        Args:
            api_key (str): Your Anthropic API key
        """
        self.client = anthropic.Client(api_key=api_key)

    def get_system_timezone(self) -> str:
        """
        Get the system's local timezone.
        
        Returns:
            str: System timezone name
        """
        try:
            return str(tzlocal.get_localzone())
        except Exception:
            return 'UTC'

    def get_formatted_time(self) -> str:
        """
        Get the current time in the system timezone.
        
        Returns:
            str: Formatted time string
        """
        system_tz = self.get_system_timezone()
        current_time = datetime.now()
        return current_time.strftime("%Y-%m-%d %H:%M:%S") + f" {system_tz}"

    def get_time_response(self, user_message: str) -> str:
        """
        Get a response from Claude about the current time.
        
        Args:
            user_message (str): The user's message/question
            
        Returns:
            str: Claude's response including the current time
        """
        current_time = self.get_formatted_time()
        
        system_prompt = f"""You are a helpful assistant that provides time-related information. You have extensive knowledge 
        of world geography, countries, cities, and their respective timezones. When a location is mentioned in the question, 
        you should determine the appropriate timezone and convert the time accordingly. If no location is specified, use the 
        provided system time.
        
        The current system time is: {current_time}
        
        When responding:
        1. If a location is mentioned, identify its timezone and convert the time appropriately
        2. Include both the time and the timezone/location in your response, ensure you get the accurate current timezone, before perfoming operations and factor in daylight savings also ensure you dont confuse GMT and UTC, use UTC at all times, very important
        3. Use a natural, conversational tone while being precise about the time
        4. For time differences or durations, do not explain your calculations """
        
        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            )
            return response.content[0].text
        except Exception as e:
            return f"Error communicating with Claude: {str(e)}"

def main():
    """
    Main function to run the interactive time bot.
    Continuously prompts for user input and provides responses until the user types 'quit'.
    """
    # Replace with your actual API key
    api_key = "m8AAA"
    bot = ClaudeTimeBot(api_key)
    
    print("Welcome to the Time Bot! Type 'quit' to exit.")
    print("Ask me about the time anywhere in the world!")
    
    while True:
        # Get user input
        user_input = input("\nYour question: ").strip()
        
        # Check if user wants to quit
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        # Get and display response
        if user_input:
            response = bot.get_time_response(user_input)
            print("\nResponse:", response)
        else:
            print("Please ask a question about time!")

if __name__ == "__main__":
    main()
