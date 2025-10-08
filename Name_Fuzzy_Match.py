
from thefuzz import process, fuzz
import pandas as pd
import re

def extract_column_from_excel(file_path, column_name):
    try:
        df = pd.read_excel(file_path)
        return df[column_name].dropna().tolist()
    except (FileNotFoundError, KeyError) as e:
        print(f"⚠️ Error reading file: {e}")
        return []

def normalize_name(name):
    # Remove punctuation, lowercase, split, sort tokens
    import re
    tokens = re.sub(r'[^\w\s]', '', name.lower()).split()
    return ' '.join(sorted(tokens))

def normalize_name(name):
    tokens = re.split(r'[\s,]+', name.lower())
    cleaned_tokens = [re.sub(r'\W', '', token) for token in tokens if token]
    return ' '.join(sorted(cleaned_tokens))

def fuzzy_match_names(input_names, name_list, threshold=85):
    normalized_names = [normalize_name(n) for n in name_list]
    results = []
    for name in input_names:
        norm_name = normalize_name(name)
        # Compare normalized input to normalized list
        matches = process.extract(norm_name, normalized_names, scorer=fuzz.ratio)
        filtered = [(name_list[i], score) for i, (_, score) in enumerate(matches) if score >= threshold]
        results.append((name, filtered))
    return results


if __name__ == "__main__":
  ##test data
  input_names=['Roberts,Kimberly Tabitha', 'Inga, Forda', 'Alroomi,Abdullah Gabriel A', 'Jane Goodall']
  ##
  name_list = extract_column_from_excel('PRISM_Data_Extract_v1.xlsx','Name')
  matches = fuzzy_match_names(input_names, name_list, threshold=85)
  for inp, found in matches:
    print(f"\nMatches for '{inp}':")
    for candidate, score in found:
        print(f"  - {candidate} (score: {score})")