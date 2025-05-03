import os
import requests
import json
import re
import gc
from .arabic_utils import normalize_arabic_text, extract_quran_reference
from .gemini_config import GEMINI_API_KEY, GEMINI_MODEL, TAFSIR_RESOURCES, DEFAULT_TAFSIR_SOURCES

# Updated API endpoint URL format
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

def get_gemini_api_url(model):
    """
    Build the Gemini API URL for the specified model.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in environment variables")
    return f"{GEMINI_API_BASE_URL}/models/{model}:generateContent?key={GEMINI_API_KEY}"

def get_gemini_headers():
    """
    Return the headers for Gemini API requests.
    """
    return {"Content-Type": "application/json"}

def identify_quran_verse(verse_text):
    """
    Use Gemini API to identify the Quran verse from text input.
    
    Args:
        verse_text (str): Arabic text of the Quran verse
        
    Returns:
        dict: Information about the verse including surah, ayah, and normalized text
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in environment variables")
    
    # Normalize the input text
    normalized_text = normalize_arabic_text(verse_text)
    
    # Check if the text contains a reference (like 2:255)
    reference = extract_quran_reference(normalized_text)
    
    try:
        url = get_gemini_api_url(GEMINI_MODEL)
        headers = get_gemini_headers()
        
        # First, validate if this is actually a Quranic verse
        validation_prompt = f"""
        Determine if this text is a verse from the Quran: "{normalized_text}"
        
        If it is a Quranic verse, return "Yes" and identify which verse it is.
        If it is NOT a Quranic verse, return "No" and explain why.
        
        Return your answer in the following JSON format:
        {{
          "is_quran_verse": true/false,
          "confidence": <0-100>,
          "explanation": "<brief explanation>",
          "surah_number": <number or null if not a verse>,
          "ayah_number": <number or null if not a verse>,
          "surah_name_arabic": "<surah name in Arabic or null if not a verse>",
          "surah_name_english": "<surah name in English or null if not a verse>",
          "match_confidence": <0-100 or 0 if not a verse>
        }}
        """
        
        validation_data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": validation_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "topK": 32,
                "topP": 1,
                "maxOutputTokens": 1024,
            }
        }
        
        # Send validation request
        validation_response = requests.post(url, headers=headers, json=validation_data)
        
        # Clear prompt from memory
        validation_prompt = None
        
        if validation_response.status_code != 200:
            raise Exception(f"Error calling Gemini API for validation: {validation_response.text}")
        
        validation_result = validation_response.json()
        validation_text = validation_result['candidates'][0]['content']['parts'][0]['text']
        
        # Extract the JSON part from the validation response
        validation_json_match = re.search(r'(\{.*\})', validation_text, re.DOTALL)
        if not validation_json_match:
            raise ValueError("Could not extract JSON data from Gemini validation response")
            
        validation_info = json.loads(validation_json_match.group(1))
        
        # If it's not a Quranic verse, return with low confidence
        if not validation_info.get('is_quran_verse', False):
            return {
                'surah_number': 0,
                'ayah_number': 0,
                'surah_name_arabic': '',
                'surah_name_english': '',
                'match_confidence': 0,
                'normalized_text': normalized_text,
                'is_quran_verse': False,
                'explanation': validation_info.get('explanation', 'This does not appear to be a Quranic verse.')
            }
        
        # If we have the verse information from validation, use it
        if validation_info.get('surah_number') and validation_info.get('ayah_number'):
            validation_info['normalized_text'] = normalized_text
            validation_info['is_quran_verse'] = True
            return validation_info
        
        # If validation passed but we don't have specific verse info, proceed with identification
        # Define the identification prompt
        prompt = f"""
        This is an Arabic Quran verse: "{normalized_text}"
        
        Identify the exact Surah number and Ayah number of this verse.
        Return only the result in the following JSON format:
        {{
          "surah_number": <number>,
          "ayah_number": <number>,
          "surah_name_arabic": "<surah name in Arabic>",
          "surah_name_english": "<surah name in English>",
          "match_confidence": <0-100>
        }}
        """
        
        data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "topK": 32,
                "topP": 1,
                "maxOutputTokens": 1024,
            }
        }
        
        # Send request
        response = requests.post(url, headers=headers, json=data)
        
        # Clear prompt from memory
        prompt = None
        
        if response.status_code != 200:
            raise Exception(f"Error calling Gemini API: {response.text}")
        
        result = response.json()
        
        # Extract text from response
        response_text = result['candidates'][0]['content']['parts'][0]['text']
        
        # Extract the JSON part from the response
        # Find JSON in the response
        json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
        if json_match:
            verse_info = json.loads(json_match.group(1))
            verse_info['normalized_text'] = normalized_text
            verse_info['is_quran_verse'] = True
            return verse_info
        else:
            raise ValueError("Could not extract JSON data from Gemini response")
                
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise Exception(f"Error parsing Gemini API response: {e}")
    finally:
        # Clear any sensitive data from memory
        response = None
        result = None
        response_text = None
        validation_response = None
        validation_result = None
        validation_text = None
        gc.collect()

def summarize_tafsir_content(tafsir_content, verse_info, language="en"):
    """
    Use Gemini API to summarize and condense the tafsir content into a unified explanation
    in simple, easy-to-understand language. Output is in the requested language (en/ar).
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in environment variables")

    url = get_gemini_api_url(GEMINI_MODEL)
    headers = get_gemini_headers()

    if language == "ar":
        prompt = f'''
أنت باحث متخصص في علم التفسير، ومتمرس في تبسيط المعاني العميقة بأسلوب روحاني، مؤثر، وواضح لغير المتخصصين.

سيُقدَّم لك الآن محتوى من تفاسير كبار العلماء للآية {verse_info['surah_number']}:{verse_info['ayah_number']} ({verse_info['surah_name_arabic']} - {verse_info['surah_name_english']}). مهمتك هي تلخيص هذه التفاسير في **شرح موحد ومترابط**، مع الحفاظ على **تعدّد الآراء التفسيرية** وذكرها **بنَسَقٍ متّزن**.

## تعليمات الإخراج:

1. **الطول والتنظيم**:
   - اكتب **من 10 إلى 15 جملة متصلة**، بأسلوب سردي متماسك.

2. **اللغة والتوقير**:
   - استخدم: **"النبي محمد ﷺ"** عند الإشارة إلى الرسول.
   - واكتب: **"الله جل جلاله"** عند الإشارة إلى الخالق عز وجل.
   - احرص على أن تكون اللغة روحانية، رزينة، خالية من التبسيط المُخلّ أو التعقيد الأكاديمي.

3. **عرض الآراء التفسيرية**:
   - **اذكر أسماء المفسرين صراحة**، مثل:
     - "يرى ابن كثير أن..."
     - "أما القرطبي فيرى..."
     - "ويُفسّر الطبري هذا الموضع بـ..."
   - إذا وُجدت آراء متعدّدة، **اعرضها بشكل واضح دون دمجها أو ترجيح أحدها**.

4. **البعد البلاغي والعقَدي**:
   - أبرز الرموز، الصور البلاغية، أو الأسلوب التحدّي إن وُجد.
   - أظهر الرسائل الإيمانية والعقَدية والتربوية المستفادة من الآية.

5. **الجمهور المستهدف**:
   - اكتب بأسلوب يناسب القارئ العام المُحب للتدبّر، دون الحاجة لخلفية شرعية متعمقة.
   - **تجنّب الجدل الفقهي، التفاصيل النحوية، أو السرد الإسنادي**.
   - لا تذكر الأحاديث النبوية أو مصادر خارج ما ورد في التفسير.

ابدأ التلخيص بناءً على المحتوى التالي:
"""
{tafsir_content}
"""
        '''
    else:
        pprompt = f'''
You are a specialist in Qur'anic exegesis and a skilled communicator who can distill profound meanings in a spiritual, engaging, and accessible style for non‑experts.

You will receive excerpts from classical tafsirs on verse {verse_info['surah_number']}:{verse_info['ayah_number']} ({verse_info['surah_name_arabic']} – {verse_info['surah_name_english']}). Your task is to craft **one unified explanation** that preserves the **full range of scholarly opinions** while presenting them in clear, respectful English.

## Output guidelines

1. **Length & flow**
   - Write **5 – 15 connected sentences** in smooth narrative form (no bullet points).

2. **Respectful language**
   - Refer to Allah as **"Allah (Glorified and Exalted is He)"**.
   - Refer to the Prophet as **"the Prophet Muhammad (peace be upon him)"**.
   - Keep the tone spiritual, dignified, and free from both colloquial oversimplification and academic jargon.

3. **Presenting scholarly views**
   - **Name each scholar explicitly**, for example:
     - "Ibn Kathir explains …"
     - "Al‑Qurtubi, on the other hand, holds …"
     - "Al‑Tabari interprets this as …"
   - When interpretations differ, present them **side‑by‑side without merging or favouring one**, using graceful transitions.

4. **Rhetorical & spiritual layers**
   - Highlight any **symbolism, rhetorical challenge, or emotional/faith‑building themes** noted by the scholars.
   - Emphasise the **core theological and moral lessons** that emerge from the verse.

5. **Audience focus**
   - Write for thoughtful readers who love to reflect on the Qur'an but lack formal training.
   - **Avoid intricate linguistic debates, legal disputes, or isnād chains**.
   - Do **not** quote ḥadiths or sources outside the tafsir excerpts provided.

Begin your summary using the tafsir content below:
"""
{tafsir_content}
"""
        '''

    data = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "topK": 32,
            "topP": 1,
            "maxOutputTokens": 1024,
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            raise Exception(f"Error calling Gemini API for summarization: {response.text}")
        result = response.json()
        summary = result['candidates'][0]['content']['parts'][0]['text']
        return summary
    except (KeyError, IndexError) as e:
        raise Exception(f"Error parsing Gemini API summarization response: {e}")
    finally:
        response = None
        result = None
        gc.collect()

def get_tafsir(verse_info, tafsir_sources=None, language="en"):
    """
    Use Gemini API to get tafsir for the identified Quran verse, in the requested language.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in environment variables")
    if tafsir_sources is None:
        tafsir_sources = DEFAULT_TAFSIR_SOURCES
    try:
        url = get_gemini_api_url(GEMINI_MODEL)
        headers = get_gemini_headers()
        if language == "ar":
            prompt = f'''
قدم تفسيرًا مبسطًا للآية {verse_info['surah_number']}:{verse_info['ayah_number']} ({verse_info['surah_name_arabic']} - {verse_info['surah_name_english']}).\n\nالنص الأصلي للآية: "{verse_info['normalized_text']}"\n\nيرجى تقديم التفسير من المصادر التالية: {', '.join(tafsir_sources)}\n\nاستخدم الهيكل التالي:\n1. لكل مصدر، قدم شرحًا موجزًا لما قاله المفسر عن هذه الآية.\n2. اجعل الشروحات مختصرة وتركز على المعاني الأساسية.\n3. قدم الموضوعات والدروس الرئيسية من هذه الآية.\n\nالمصادر المرجعية: {', '.join(TAFSIR_RESOURCES)}
            '''
        else:
            prompt = f"""
Provide the tafsir (exegesis) for Quran verse {verse_info['surah_number']}:{verse_info['ayah_number']} ({verse_info['surah_name_arabic']} - {verse_info['surah_name_english']}).

Original verse text: "{verse_info['normalized_text']}"

Please provide tafsir from the following sources: {', '.join(tafsir_sources)}

Use the following structure:
1. For each tafsir source, provide a brief explanation of what the scholar said about this verse.
2. Keep the explanations concise, focusing on the main interpretations.
3. Provide the primary themes and lessons from this verse.

Reference the following tafsir resources: {', '.join(TAFSIR_RESOURCES)}
            """
        data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topK": 32,
                "topP": 1,
                "maxOutputTokens": 4096,
            }
        }
        response = requests.post(url, headers=headers, json=data)
        prompt = None
        if response.status_code != 200:
            raise Exception(f"Error calling Gemini API: {response.text}")
        result = response.json()
        tafsir_response = result['candidates'][0]['content']['parts'][0]['text']
        # Summarize the tafsir content (now only plain summary)
        condensed_tafsir = summarize_tafsir_content(
            tafsir_response,
            verse_info,
            language
        )
        return {
            "verse_info": verse_info,
            "tafsir_sources": tafsir_sources,
            "tafsir_content": tafsir_response,
            "condensed_tafsir": condensed_tafsir
        }
    except (KeyError, IndexError) as e:
        raise Exception(f"Error parsing Gemini API response: {e}")
    finally:
        response = None
        result = None
        gc.collect()

def process_text_input(verse_text, tafsir_sources=None, language="en"):
    """
    Process a text input containing a Quran verse and return the tafsir in the requested language.
    
    Args:
        verse_text (str): Text input that may contain a Quran verse
        tafsir_sources (list): Optional list of tafsir sources to use
        language (str): Language code ('en' for English, 'ar' for Arabic)
        
    Returns:
        dict: Tafsir information or error information if not a Quranic verse
        
    Raises:
        Exception: If there's an error in processing
    """
    try:
        # Identify the verse
        verse_info = identify_quran_verse(verse_text)
        
        # Check if it's a valid Quranic verse
        if not verse_info.get('is_quran_verse', True) or verse_info.get('match_confidence', 0) < 30:
            # Return a structured response for non-Quranic text
            return {
                'verse_info': {
                    'surah_number': 0,
                    'ayah_number': 0,
                    'surah_name_arabic': '',
                    'surah_name_english': '',
                    'match_confidence': verse_info.get('match_confidence', 0),
                    'normalized_text': verse_info.get('normalized_text', verse_text),
                    'is_quran_verse': False
                },
                'error': 'not_quran_verse',
                'explanation': verse_info.get('explanation', 'The provided text does not appear to be a Quranic verse.'),
                'confidence': verse_info.get('match_confidence', 0)
            }
        
        # If it's a valid verse, get the tafsir
        tafsir_result = get_tafsir(verse_info, tafsir_sources, language=language)
        return tafsir_result
    finally:
        # Clear the input text from memory as we no longer need it
        verse_text = None
        gc.collect() 