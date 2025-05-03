from supabase import create_client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_message_templates():
    """Check and display message templates by type and threshold."""
    
    # Get all templates
    response = supabase.table("message_templates").select("*").execute()
    templates = response.data
    
    if not templates:
        print("No templates found in the database.")
        return
    
    # Organize templates by type and threshold
    templates_by_type = {}
    for template in templates:
        template_type = template.get("template_type")
        threshold_days = template.get("threshold_days")
        
        if template_type not in templates_by_type:
            templates_by_type[template_type] = {}
        
        if threshold_days not in templates_by_type[template_type]:
            templates_by_type[template_type][threshold_days] = []
        
        templates_by_type[template_type][threshold_days].append(template)
    
    # Print summary and details
    print(f"Found {len(templates)} total templates:")
    
    for template_type, thresholds in sorted(templates_by_type.items()):
        print(f"\n{template_type.upper()} TEMPLATES:")
        
        for threshold, template_list in sorted(thresholds.items()):
            print(f"  Threshold: {threshold} days - {len(template_list)} templates")
            
            # Print a sample of each language
            if template_list:
                for i, template in enumerate(template_list):
                    print(f"    Template {i+1}:")
                    
                    # Safe handling of potentially None values
                    eng_text = template.get('text_used_english', 'None')
                    eng_text_display = eng_text[:50] + "..." if eng_text else "None"
                    
                    eng_msg = template.get('message_english_translation', 'None')
                    eng_msg_display = eng_msg[:50] + "..." if eng_msg else "None"
                    
                    ar_text = template.get('text_used_arabic', 'None')
                    ar_text_display = ar_text[:50] + "..." if ar_text else "None"
                    
                    ar_msg = template.get('message_arabic_translation', 'None')
                    ar_msg_display = ar_msg[:50] + "..." if ar_msg else "None"
                    
                    print(f"      English text: {eng_text_display}")
                    print(f"      English message: {eng_msg_display}")
                    print(f"      Arabic text: {ar_text_display}")
                    print(f"      Arabic message: {ar_msg_display}")
                    print()

if __name__ == "__main__":
    check_message_templates() 