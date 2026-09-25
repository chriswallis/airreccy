import json
import re
import subprocess


text = subprocess.check_output(
    ["pdftotext", "-layout", "ACTO 104.pdf", "-"],
    text=True,
    encoding="utf-8",
)

sections = []
current = None
group = None
row = None


def finish_row():
    global row
    if row and group:
        group["aircraft"].append({
            "number": row["number"],
            "aircraft": " ".join(row["aircraft"]).strip(),
            "manufacturer": " ".join(row["manufacturer"]).strip(),
            "additional": " ".join(row["additional"]).strip(),
        })
    row = None


def finish_group():
    global group
    finish_row()
    if group and group["aircraft"] and current:
        current["groups"].append(group)
    group = None


for raw_line in text.splitlines():
    line = raw_line.rstrip()
    stripped = line.strip()

    list_match = re.match(r"Aircraft Recognition Syllabus List\s+(\d+)", stripped)
    if list_match:
        finish_group()
        current = {"list": int(list_match.group(1)), "groups": []}
        sections.append(current)
        continue

    if not current:
        continue

    group_match = re.search(r"Group\s+(\d+)\s*[:(]\s*(.*)", stripped)
    if group_match:
        finish_group()
        description = group_match.group(2).strip()
        if "(" in description and not description.endswith(")"):
            description += ")"
        group = {
            "number": int(group_match.group(1)),
            "description": description.rstrip(")").strip() + (")" if ")" in description else ""),
            "aircraft": [],
        }
        continue

    if not group:
        continue

    number_match = re.match(r"^\s{0,4}(\d+)\s{2,}", line)
    if number_match:
        finish_row()
        row = {
            "number": int(number_match.group(1)),
            "aircraft": [],
            "manufacturer": [],
            "additional": [],
        }

    if not row:
        continue

    for key, value in zip(
        ("aircraft", "manufacturer", "additional"),
        (line[5:29], line[29:59], line[59:]),
    ):
        if value.strip():
            row[key].append(value.strip())

finish_group()

with open("aircraft.json", "w", encoding="utf-8") as output:
    json.dump(sections, output, ensure_ascii=False, indent=2)
    output.write("\n")

print("Lists:", len(sections))
print("Entries:", [sum(len(item["aircraft"]) for item in section["groups"]) for section in sections])