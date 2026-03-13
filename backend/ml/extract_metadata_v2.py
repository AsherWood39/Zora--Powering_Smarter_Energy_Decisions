"""
Zora — Natural Language Metadata Extraction
===========================================
Phase 1: Foundation & Context
Zora-DOC Reference: Lesson 8 (Advanced Feature Context)

Data Science is not just about numbers! Real-world datasets often have crucial 
information hidden in text files (like NASA's README.txt). We use the Groq LLM API 
to scan the text, understand physical battery chemistry parameters, and transform 
it into structured JSON data for our pipeline.
"""
import os
import pandas as pd
import glob
import requests
import json
from dotenv import load_dotenv
from tqdm import tqdm

# 1. SETUP
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

EXTRA_INFO_DIR = os.path.join(BASE_DIR, "dataset/cleaned_dataset/extra_infos")
OUTPUT_JSON = os.path.join(BASE_DIR, "ml/results/battery_groups_metadata.json")

os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def extract_metadata_with_groq(text):
    """
    Step 1: The Prompt Engineering
    Zora-DOC Lesson 8 (Context & Ground Truth)
    
    Calls Groq API to extract experimental parameters from README text.
    We instruct the LLM specifically to separate "Rated Capacity" (Original) 
    from "EOL Threshold" (When the battery dies).
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    You are an expert battery researcher. Analyze the following project README text and extract experimental parameters.
    
    CRITICAL INSTRUCTIONS:
    1. Rated Capacity is the ORIGINAL capacity of the battery. Look for phrases like "rated capacity", "from X Ahr", or similar. 
       - In most NASA Li-ion datasets, the rated capacity is 2.0 Ahr.
    2. EOL Threshold is the capacity when the experiment STOPS. Look for "reduced to X Ahr" or "fade".
       - Do NOT confuse Rated Capacity with EOL Threshold. If it says "from 2Ahr to 1.4Ahr", Rated Capacity = 2.0, EOL = 1.4.
    3. Return ONLY a valid JSON object.
    
    STRUCTURE:
    {{
        "battery_ids": ["B0005", "B0006", ...],
        "ambient_temp": value_in_C (number),
        "discharge_current_A": value_in_A (number or "multiple"),
        "rated_capacity_Ahr": value_in_Ahr (number),
        "eol_threshold_Ahr": value_in_Ahr (number),
        "charge_protocol": "string",
        "discharge_cutoff_voltage": {{ "B0005": 2.7, ... }} or number
    }}
    
    README TEXT:
    {text}
    """
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error calling Groq: {e}")
        return None

def run_metadata_extraction():
    readme_files = glob.glob(os.path.join(EXTRA_INFO_DIR, "README_*.txt"))
    all_metadata = []
    
    print(f"Found {len(readme_files)} README files. Extracting metadata...")
    
    for fpath in tqdm(readme_files):
        with open(fpath, 'r', encoding='utf-8') as f:
            text = f.read()
            
        result_json = extract_metadata_with_groq(text)
        if result_json:
            try:
                data = json.loads(result_json)
                all_metadata.append(data)
            except:
                print(f"Failed to parse JSON for {os.path.basename(fpath)}")
                
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(all_metadata, f, indent=4)
        
    print(f"[DONE] Metadata saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    run_metadata_extraction()