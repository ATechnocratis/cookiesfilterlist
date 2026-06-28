import re
from pathlib import Path
from datetime import datetime

input_file = Path("rules.js")
output_file = Path("i-still-dont-care-ublock.txt")

print("🔄 Loading rules.js...")

content = input_file.read_text(encoding="utf-8")

# ===================== EXTRACT COMMONS =====================
print("📦 Extracting common CSS rules...")

commons = {}
commons_match = re.search(r'const commons = \{(.+?)\n\};', content, re.DOTALL)
if commons_match:
    commons_str = commons_match.group(1)
    for m in re.finditer(r'(\d+):\s*["\'](.*?)["\']', commons_str, re.DOTALL):
        commons[m.group(1)] = m.group(2).strip()

print(f"Found {len(commons)} common rules")

# ===================== EXTRACT DOMAIN RULES =====================
print("📋 Extracting domain-specific rules...")

rules_match = re.search(r'const rules = \{(.+?)\n\};', content, re.DOTALL)
rules_str = rules_match.group(1) if rules_match else ""

domain_rules = {}

pattern = r'"([^"]+)":\s*\{(.*?)\}(?:,|\s*(?="[\w\.-]+":|\n\s*\}))'
for match in re.finditer(pattern, rules_str, re.DOTALL):
    domain = match.group(1).strip()
    body = match.group(2).strip()
    
    selectors = []
    js_handlers = []
    
    s_matches = re.findall(r's:\s*["\'](.*?)["\']', body, re.DOTALL)
    for s in s_matches:
        if s.strip():
            selectors.append(s.strip())
    
    c_matches = re.findall(r'c:\s*(\d+)', body)
    for c in c_matches:
        if c in commons:
            selectors.append(commons[c])
        else:
            selectors.append(f"__COMMON_{c}")
    
    j_matches = re.findall(r'j:\s*["\']?([\w\d]+)', body)
    for j in j_matches:
        js_handlers.append(j.strip())
    
    if selectors or js_handlers:
        domain_rules[domain] = {"selectors": selectors, "js": js_handlers}

print(f"✅ Extracted {len(domain_rules):,} domain rules")

# ===================== GENERATE UBLOCK LIST =====================
print("💾 Writing uBlock filter list...")

with open(output_file, "w", encoding="utf-8") as f:
    f.write("! =============================================\n")
    f.write("! I-Still-Dont-Care-About-Cookies → uBlock Origin\n")
    f.write("! Full Advanced Conversion\n")
    f.write(f"! Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    f.write("! =============================================\n\n")

    f.write("! === Generic Rules ===\n")
    f.write("##.cookie,###cookie,##.cookies,###cookies,##.gdpr,###gdpr,##.consent,###consent\n")
    f.write("##.modal-backdrop,##.veil,##.overlay\n")
    f.write("##body > div:not([id]):not([class])[style*=\"fixed\"]\n\n")

    f.write("! === Site Specific Rules ===\n")

    for domain, data in sorted(domain_rules.items()):
        for js in data["js"]:
            handler_map = {"5": "click-handler", "8": "google-handler", "6": "cookie-handler"}
            handler = handler_map.get(js, f"click-handler")
            f.write(f"{domain}##+js({handler})\n")

        for sel in data["selectors"]:
            clean = sel.strip()
            if not clean or len(clean) < 5:
                continue
            clean = re.sub(r'\{[^}]*\}', '', clean).strip()
            if clean:
                f.write(f"{domain}##{clean}\n")

    f.write("\n! End of conversion\n")

print(f"🎉 Done! Total domains: {len(domain_rules):,}")
