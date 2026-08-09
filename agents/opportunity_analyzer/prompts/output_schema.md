Extract structured information from the opportunity text below.

Opportunity text:
---
{opportunity_text}
---

OUTPUT FORMAT:
Respond with ONLY a valid, raw JSON object. Do not include markdown formatting (like ```json), commentary, or leading/trailing prose.

SECTOR INFERENCE RULES (IMPORTANT):
- You MUST infer "sector" from the tender title + description + requirements context.
- Do NOT leave "sector" as null when meaningful domain clues exist.
- Only use null when the text is genuinely too vague/insufficient.
- Choose exactly ONE sector from this fixed taxonomy:
  ["IT Services","Construction","Healthcare","Education","Energy","Transport","Agriculture","Finance","Public Administration","Other"]
- If your inferred sector confidence is low, prefer "Other" instead of overconfident misclassification.

Output Schema:
{
  "sector": string or null,          // MUST be one value from the taxonomy above, or null if truly insufficient
  "sector_confidence": 0.0,          // number between 0 and 1 for confidence in inferred sector
  "country": string or null,         // primary country named or null
  "deadline": string or null,        // ISO date YYYY-MM-DD if stated, else null
  "key_requirements": [string],      // short list of concrete requirements (max 5 items)
  "opportunity_type": string or null // e.g., "tender", "grant", "partnership", "RFP", "contract"
}
