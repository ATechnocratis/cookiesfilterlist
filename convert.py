import re
from datetime import datetime

content = open("rules.js", encoding="utf-8").read()

# Commons
commons = {}
cm = re.search(r"const commons = \{(.+?)\n\};", content, re.DOTALL)
if cm:
    for m in re.finditer(r"(\d+):\s*[\"''](.*?)[\"'']", cm.group(1), re.DOTALL):
        commons[m.group(1)] = m.group(2).strip()

# Rules
rules_match = re.search(r"const rules = \{(.+?)\n\};", content, re.DOTALL)
if rules_match:
    rules_str = rules_match.group(1)
    with open("i-still-dont-care-ublock.txt", "w", encoding="utf-8") as f:
        f.write(f"! I-Still-Dont-Care-About-Cookies → uBlock Origin\n")
        f.write(f"! Updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n")
        f.write("! Source: https://github.com/OhMyGuus/I-Still-Dont-Care-About-Cookies\n\n")
        f.write("##.cookie,###cookie,##.gdpr,###gdpr,##.consent,###consent\n\n")

        count = 0
        for m in re.finditer(r'"([^"]+)":\s*\{(.*?)\}(?:,|\s*(?="|\n\s*\}))', rules_str, re.DOTALL):
            domain = m.group(1)
            body = m.group(2)
            count += 1

            # CSS
            for s in re.findall(r's:\s*["\'](.*?)["\']', body, re.DOTALL):
                clean = re.sub(r'\{[^}]+\}', '', s).strip()
                if clean and len(clean) > 5:
                    f.write(f"{domain}##{clean}\n")

            # Commons
            for c in re.findall(r'c:\s*(\d+)', body):
                if c in commons:
                    f.write(f"{domain}##{commons[c]}\n")

            # JS
            for j in re.findall(r'j:\s*["\']?(\d+)', body):
                handler = {"5": "click-handler", "8": "google-handler", "6": "cookie-handler"}.get(j, "click-handler")
                f.write(f"{domain}##+js({handler})\n")

        print(f"✅ Processed {count} domains")
