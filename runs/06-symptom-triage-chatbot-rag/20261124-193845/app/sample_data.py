# Synthetic, hand-crafted guideline sections for demo purposes.
GUIDELINES = [
    {
        "section_id": "s001",
        "title": "Shortness of breath - emergency signs",
        "text": "If shortness of breath is sudden, severe, or accompanied by chest pain, fainting, or blue lips, seek emergency care immediately.",
        "documented_urgency": "emergency"
    },
    {
        "section_id": "s002",
        "title": "Fever in adults",
        "text": "For adults, a fever over 39C (102F) that persists or is accompanied by severe headache, stiff neck, rash, or confusion warrants urgent evaluation.",
        "documented_urgency": "urgent"
    },
    {
        "section_id": "s003",
        "title": "Mild fever with no other symptoms",
        "text": "A mild fever without other concerning features can often be observed at home with rest, fluids, and symptomatic care; contact your healthcare provider if it worsens or lasts more than 72 hours.",
        "documented_urgency": "low"
    },
    {
        "section_id": "s004",
        "title": "Headache - red flags",
        "text": "Severe sudden-onset headache, headache with fever and stiff neck, or neurological deficits requires immediate medical attention.",
        "documented_urgency": "emergency"
    },
    {
        "section_id": "s005",
        "title": "Minor cuts and abrasions",
        "text": "Small cuts that stop bleeding and are not deep can be cleaned and dressed at home; seek medical care for deep wounds or if signs of infection appear.",
        "documented_urgency": "low"
    },
]

# Expand to ~20 items by duplicating with variations
for i in range(6, 21):
    GUIDELINES.append({
        "section_id": f"s{str(i).zfill(3)}",
        "title": f"Sample guideline section {i}",
        "text": f"This is a synthetic guideline paragraph number {i}. It describes typical advice and triage level for testing retrieval and RAG behavior.",
        "documented_urgency": "low" if i % 5 != 0 else "urgent"
    })
