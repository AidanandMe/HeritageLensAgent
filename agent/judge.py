import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
# client initialization moved inside evaluate_layer_3 to prevent early failure

def evaluate_layer_3(layer_3_text: str) -> tuple[bool, str]:
    """
    Judges the transparency report for specificity.
    Returns (is_valid: bool, feedback_if_weak: str)
    """
    client = OpenAI()
    prompt = f"""You are the internal Judge for the Heritage Lens Agent.
Your job is to read the 'Layer 3 Epistemic Transparency' report and determine if it is specific to the retrieved data or if it uses generic boilerplate.

GENERIC BOILERPLATE EXAMPLES (WEAK):
- "AI systems can be biased"
- "Some sources may carry an academic viewpoint"
- "Various perspectives might be missing"

SPECIFIC GROUNDING EXAMPLES (VALID):
- "3 of 4 sources are Western academic papers"
- "No indigenous oral traditions are present"
- "The term 'ritual' reflects UNAM academic classification"

Review the following Layer 3 text:
'''
{layer_3_text}
'''

Output a JSON object with:
"is_valid": true if specific and grounded, false if generic
"explanation": Focus purely on what is generic so the generator knows what exact clauses to replace with data-driven claims. Keep it under 3 sentences.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    
    result = json.loads(response.choices[0].message.content)
    return result.get("is_valid", False), result.get("explanation", "Failed to parse judge output.")
