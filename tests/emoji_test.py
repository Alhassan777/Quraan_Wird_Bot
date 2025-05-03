def check_emoji(text, check_marks):
    """Check if the given text contains any of the check mark emojis."""
    detected = []
    for mark in check_marks:
        if mark in text:
            # Convert to hex representation for logging
            hex_repr = ' '.join(hex(ord(c)) for c in mark)
            detected.append(f"{mark} (hex: {hex_repr})")
    return detected

def bot_check_logic(text, check_marks):
    """Simulate the actual logic in the bot's handle_checkmark function."""
    return any(mark in text for mark in check_marks)

def main():
    # Define all possible check mark symbols across different platforms
    check_marks = [
        "✅",  # White Heavy Check Mark (U+2705)
        "✔️",  # Heavy Check Mark with variation selector (U+2714 U+FE0F)
        "✔",   # Heavy Check Mark without variation selector (U+2714)
        "✓",   # Check Mark (U+2713)
        "☑️",  # Ballot Box with Check with variation selector (U+2611 U+FE0F)
        "☑",   # Ballot Box with Check without variation selector (U+2611)
        "🗸",   # Light Check Mark (U+1F5F8)
    ]
    
    # Test each check mark individually
    print("INDIVIDUAL EMOJI TESTS")
    print("======================")
    for i, mark in enumerate(check_marks):
        # Create a unique text for each emoji to avoid overlapping matches
        text = f"Test{i} {mark} in text"
        
        # Test the emoji with the bot's logic
        is_detected = bot_check_logic(text, [mark])
        
        # Print detailed info about the emoji
        print(f"Emoji #{i+1}: {mark}")
        print(f"Character(s): {' '.join(hex(ord(c)) for c in mark)}")
        print(f"Test string: {text}")
        print(f"Detected by bot: {'Yes' if is_detected else 'No'}")
        print()
    
    # Test sample messages that would be sent to the bot
    print("\nSAMPLE MESSAGE TESTS")
    print("===================")
    
    sample_messages = [
        "I just finished reading! ✅",
        "Done with my daily reading ✔️",
        "Finished ✓",
        "Read the Quran today ☑️",
        "Completed my daily portion 🗸",
        "Just the emoji by itself: ✅",
        "Today I read Quran \u2705", # Unicode White Heavy Check Mark
        "Finished reading \U0001F5F8", # Unicode Light Check Mark
    ]
    
    for i, message in enumerate(sample_messages):
        print(f"Message #{i+1}: {message}")
        
        # Check using the bot's detection logic
        is_detected = bot_check_logic(message, check_marks)
        
        # Find which specific emoji(s) triggered the detection
        found_marks = []
        for mark in check_marks:
            if mark in message:
                found_marks.append(f"{mark} ({' '.join(hex(ord(c)) for c in mark)})")
        
        print(f"Detected by bot: {'Yes' if is_detected else 'No'}")
        if found_marks:
            print(f"Found emoji(s): {', '.join(found_marks)}")
        print()

if __name__ == "__main__":
    main() 