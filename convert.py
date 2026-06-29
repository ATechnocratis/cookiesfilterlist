import re
from pathlib import Path
from datetime import datetime

input_file = Path("rules.js")
output_file = Path("i-still-dont-care-ublock.txt")


content = input_file.read_text(encoding="utf-8")

# ===================== EXTRACT COMMONS =====================

commons = {}
commons_match = re.search(r'const commons = \{(.+?)\n\};', content, re.DOTALL)
if commons_match:
    commons_str = commons_match.group(1)
    for m in re.finditer(r'(\d+):\s*["\'](.*?)(?:\'\,$|"$|",|\n)', commons_str, re.DOTALL):
        commons[m.group(1)] = m.group(2).strip()


# ===================== EXTRACT DOMAIN RULES =====================

rules_match = re.search(r'const rules = \{(.+?)\n\};', content, re.DOTALL)
rules_str = rules_match.group(1) if rules_match else ""

domain_rules = {}

pattern = r'"([^"]+)":\s*\{(.*?)\}(?:,|\s*(?="[\w\.-]+":|\n\s*\}))'
for match in re.finditer(pattern, rules_str, re.DOTALL):
    domain = match.group(1).strip()
    body = match.group(2).strip()
    
    selectors = []
    
    multipleLines = re.findall(r's:\s*["\'](.*?)\+\n', body, re.DOTALL)
    if(len(multipleLines)>0):
        allTogether = re.findall(r's:\s*["\'](.*?)(?:\'\,$|"$|",)', body, re.DOTALL)
        if (len(allTogether)>0):
            s_matches = re.sub("\s*\+\s*\n\s*", "" ,allTogether[0])
        else:
            s_matches = []
    else:
        s_matches = re.findall(r's:\s*["\'](.*?)(?:\'\,$|"$|",|\n)', body, re.DOTALL)
    delimiter = ","
    delimiter2 = "@"
    for s in s_matches:
        splits = []
        current = []
        depth = 0
        replaced =  s.replace("}", "}@@")
        prevChar = ""
        for char in replaced:
            if char == '(':
                depth += 1
                current.append(char)
            elif char == ')':
                depth -= 1
                current.append(char)
            elif char == delimiter and depth == 0:
                splits.append("".join(current).strip())
                current = []
            elif char == delimiter2 and prevChar == delimiter2:
                splits.append("".join(current[:-1]).strip())
                current = []
            else:
                current.append(char)
            prevChar = char
        splits.append("".join(current).strip())

        for ss in splits:
            if ss.strip():
                selectors.append(ss.strip().removesuffix("html"))
    
    c_matches = re.findall(r'c:\s*(\d+)', body)
    for c in c_matches:
        if c in commons:
            splits = re.split('@|,', commons[c].replace("}", "}@"))
            for ss in splits:
                selectors.append(ss)   
  
    if selectors:
        domain_rules[domain] = {"selectors": selectors}


# ===================== GENERATE UBLOCK LIST =====================

with open(output_file, "w", encoding="utf-8") as f:
    f.write("! =============================================\n")
    f.write("! I-Still-Dont-Care-About-Cookies → uBlock Origin\n")
    f.write("! Full Advanced Conversion\n")
    f.write("! Expires: 5 days\n")
    f.write(f"! Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    f.write("! =============================================\n\n")

    f.write("! === Generic Rules ===\n")
    f.write("##.cookies\n")
    f.write("##.cookie-banner\n")
    f.write("###cookies\n")
    f.write("##.cookie\n")
    f.write("###cookie\n")
    f.write("###consent\n")
    f.write("##.consent\n")
    f.write("##.gdpr\n")
    f.write("###gdpr\n")
    f.write("##.modal-backdrop\n")
    f.write("##.veil\n")
    f.write("##.overlay\n")
    f.write("##body > div:not([id]):not([class])[style*=\"fixed\"]\n\n")

    f.write("! === Site Specific Rules ===\n")

    for domain, data in sorted(domain_rules.items()):

        for sel in data["selectors"]:
            clean = sel.strip()
            if not clean or len(clean) < 5:
                continue
            clean = re.sub(r'\{[^}]*\}', '', clean).strip()
            if clean:
                f.write(f"{domain}##{clean}\n")


