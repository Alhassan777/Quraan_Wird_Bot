def main():
    """Display the different messages a user would receive when using check mark emojis."""
    print("MESSAGES SENT TO USERS WHEN USING CHECK MARK EMOJIS")
    print("===================================================")
    
    # Scenario 1: First time user marks completion
    streak = 1
    print("\nSCENARIO 1: First time marking completion")
    print("----------------------------------------")
    response = (
        f"بارك الله فيك! 🌟 لقد أكملت وردك اليومي. "
        f"سلسلة استمراريتك الحالية: {streak} {'يوم' if streak == 1 else 'أيام'}!"
    )
    print(f"Arabic: {response}")
    print(f"English translation: \"May Allah bless you! 🌟 You have completed your daily portion. "
          f"Your current streak: {streak} {'day' if streak == 1 else 'days'}!\"")
    
    # Scenario 2: User with a streak of more than 1 day
    streak = 5
    print("\nSCENARIO 2: User with a streak of 5 days")
    print("---------------------------------------")
    response = (
        f"بارك الله فيك! 🌟 لقد أكملت وردك اليومي. "
        f"سلسلة استمراريتك الحالية: {streak} {'يوم' if streak == 1 else 'أيام'}!"
    )
    print(f"Arabic: {response}")
    print(f"English translation: \"May Allah bless you! 🌟 You have completed your daily portion. "
          f"Your current streak: {streak} {'day' if streak == 1 else 'days'}!\"")
    
    # Scenario 3: User tries to mark completion twice in one day
    print("\nSCENARIO 3: Duplicate check mark in the same day (anti-spam)")
    print("-----------------------------------------------------------")
    response = "لقد سجلت وردك بالفعل اليوم! 🙏"
    print(f"Arabic: {response}")
    print(f"English translation: \"You have already marked your portion for today! 🙏\"")
    
    # Scenario 4: Error occurs during check mark handling
    print("\nSCENARIO 4: Error occurs during check mark handling")
    print("--------------------------------------------------")
    response = "حدث خطأ أثناء تسجيل وردك. يرجى المحاولة مرة أخرى."
    print(f"Arabic: {response}")
    print(f"English translation: \"An error occurred while recording your reading. Please try again.\"")
    
    # Scenario 5: User breaks streak and starts over
    print("\nSCENARIO 5: User breaks streak and starts over")
    print("--------------------------------------------")
    streak = 1
    response = (
        f"بارك الله فيك! 🌟 لقد أكملت وردك اليومي. "
        f"سلسلة استمراريتك الحالية: {streak} {'يوم' if streak == 1 else 'أيام'}!"
    )
    print(f"Arabic: {response}")
    print(f"English translation: \"May Allah bless you! 🌟 You have completed your daily portion. "
          f"Your current streak: {streak} {'day' if streak == 1 else 'days'}!\"")
    
    print("\nNOTE: The bot will return the same success message regardless of which check mark variant is used.")

if __name__ == "__main__":
    main() 