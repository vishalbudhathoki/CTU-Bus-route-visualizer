import fitz

doc = fitz.open("TimeTableLocal_060425.pdf")
with open("timetable_text.txt", "w", encoding="utf-8") as f:
    for i in range(len(doc)):
        f.write(f"--- PAGE {i+1} ---\n")
        f.write(doc[i].get_text())
        f.write("\n")
