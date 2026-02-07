"""
AI Service for intelligent menu engineering features using OpenRouter.

Supports multiple free models:
- deepseek/deepseek-chat (recommended)
- mistralai/mistral-7b-instruct
- meta-llama/llama-3-8b-instruct

Custom Instructions:
    All functions support a `custom_instructions` parameter to inject
    additional context or requirements into the prompts.
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Available free models on OpenRouter
MODELS = {
    "deepseek": "deepseek/deepseek-chat",
    "mistral": "mistralai/mistral-7b-instruct",
    "llama": "meta-llama/llama-3-8b-instruct",
}

# Default model
DEFAULT_MODEL = MODELS["deepseek"]

# Default system prompt (can be overridden)
DEFAULT_SYSTEM_PROMPT = """You are an expert restaurant consultant specializing in menu engineering and optimization. 
You provide actionable, data-driven recommendations to improve menu profitability and customer satisfaction.
Always respond with valid JSON as specified in the user's request."""


def get_client():
    """Get the OpenRouter client."""
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not configured")

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )


def chat_completion(prompt: str, system_prompt: str = None, model: str = None) -> str:
    """
    Send a chat completion request to OpenRouter.

    Args:
        prompt: The user prompt
        system_prompt: Optional system prompt to set AI behavior
        model: Optional model override
    """
    client = get_client()
    model = model or DEFAULT_MODEL
    system = system_prompt or DEFAULT_SYSTEM_PROMPT

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=1500,
    )

    return response.choices[0].message.content


def parse_json_response(text: str) -> dict:
    """Parse JSON from LLM response, handling markdown code blocks."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]

    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {"raw_response": text, "error": "Could not parse JSON"}


async def enhance_description(
    item_name: str,
    current_description: str,
    category: str,
    price: float,
    cuisine_type: str = "restaurant",
    custom_instructions: str = None,
    tone: str = "professional",
    include_allergens: bool = False,
    target_audience: str = None,
) -> dict:
    """
    Enhance a menu item description to be more appetizing.

    Args:
        item_name: Name of the menu item
        current_description: Existing description (can be empty)
        category: Menu engineering category (Star/Plowhorse/Puzzle/Dog)
        price: Item price
        cuisine_type: Type of cuisine (e.g., "Italian", "American")
        custom_instructions: Additional instructions to inject into the prompt
        tone: Writing tone ("professional", "casual", "playful", "elegant")
        include_allergens: Whether to mention common allergens
        target_audience: Target customer demographic

    Returns:
        dict with enhanced_description, key_selling_points, tips
    """

    # Build custom requirements section
    requirements = []
    if tone != "professional":
        requirements.append(f"- Use a {tone} tone")
    if include_allergens:
        requirements.append(
            "- Mention relevant allergen information (gluten, dairy, nuts, etc.)"
        )
    if target_audience:
        requirements.append(f"- Target audience: {target_audience}")
    if custom_instructions:
        requirements.append(f"- SPECIAL REQUIREMENTS: {custom_instructions}")

    requirements_text = "\n".join(requirements) if requirements else ""

    prompt = f"""Enhance this menu item description to be more appetizing and increase sales.

Item: {item_name}
Current Description: {current_description if current_description else "None provided"}
Category: {category}
Price: ${price:.2f}
Cuisine Type: {cuisine_type}

Standard Guidelines:
- Use sensory words (crispy, tender, aromatic, fresh)
- Highlight premium ingredients
- Keep it concise (2-3 sentences max)
- Match the price point expectation

{f"Additional Requirements:{chr(10)}{requirements_text}" if requirements_text else ""}

Respond ONLY with valid JSON:
{{"enhanced_description": "Your improved description", "key_selling_points": ["point1", "point2"], "tips": ["tip1", "tip2"]}}"""

    response = chat_completion(prompt)
    return parse_json_response(response)


async def analyze_menu_structure(
    menu_sections: list[dict],
    custom_instructions: str = None,
    focus_areas: list[str] = None,
) -> dict:
    """
    Analyze menu structure and suggest optimal layout.

    Args:
        menu_sections: List of sections with items
        custom_instructions: Additional instructions
        focus_areas: Specific areas to focus on (e.g., ["pricing", "layout", "naming"])
    """

    menu_summary = []
    for section in menu_sections:
        items = section.get("items", [])[:5]
        menu_summary.append(
            {
                "section": section.get("name"),
                "items": [
                    {
                        "name": i.get("name"),
                        "price": i.get("price"),
                        "category": i.get("category"),
                    }
                    for i in items
                ],
            }
        )

    focus_text = ""
    if focus_areas:
        focus_text = f"\nFocus specifically on: {', '.join(focus_areas)}"

    custom_text = ""
    if custom_instructions:
        custom_text = f"\n\nADDITIONAL REQUIREMENTS: {custom_instructions}"

    prompt = f"""Analyze this menu structure and provide optimization recommendations.

Menu:
{json.dumps(menu_summary, indent=2)}
{focus_text}{custom_text}

Respond ONLY with valid JSON:
{{"overall_score": 7, "section_order_recommendation": ["Section1", "Section2"], "items_to_highlight": ["item1"], "items_to_reconsider": ["item2"], "general_recommendations": ["rec1", "rec2"]}}"""

    response = chat_completion(prompt)
    return parse_json_response(response)


async def generate_sales_suggestions(
    item_name: str,
    category: str,
    price: float,
    cost: float,
    purchases: int,
    section_avg_price: float = None,
    section_avg_sales: float = None,
    custom_instructions: str = None,
    strategy: str = "balanced",
) -> dict:
    """
    Generate actionable sales suggestions for a menu item.

    Args:
        item_name: Name of the item
        category: Menu engineering category
        price: Current price
        cost: Item cost
        purchases: Number of purchases
        section_avg_price: Optional section average price
        section_avg_sales: Optional section average sales
        custom_instructions: Additional instructions
        strategy: "aggressive", "balanced", or "conservative"
    """

    margin = price - cost
    margin_pct = (margin / price * 100) if price > 0 else 0

    strategy_text = ""
    if strategy == "aggressive":
        strategy_text = (
            "\nUse an aggressive strategy: prioritize quick wins and bold changes."
        )
    elif strategy == "conservative":
        strategy_text = (
            "\nUse a conservative strategy: suggest gradual, low-risk changes."
        )

    custom_text = ""
    if custom_instructions:
        custom_text = f"\n\nADDITIONAL REQUIREMENTS: {custom_instructions}"

    prompt = f"""Generate specific sales suggestions for this menu item.

Item: {item_name}
Category: {category} (Star=high profit+sales, Plowhorse=low profit+high sales, Puzzle=high profit+low sales, Dog=low both)
Price: ${price:.2f}, Cost: ${cost:.2f}, Margin: ${margin:.2f} ({margin_pct:.1f}%)
Purchases: {purchases}
{f"Section Avg Price: ${section_avg_price:.2f}" if section_avg_price else ""}
{f"Section Avg Sales: {int(section_avg_sales)}" if section_avg_sales else ""}
{strategy_text}{custom_text}

Respond ONLY with valid JSON:
{{"priority": "high", "suggested_price": {price}, "immediate_actions": ["action1", "action2"], "marketing_tips": ["tip1"], "estimated_impact": "Expected outcome"}}"""

    response = chat_completion(prompt)
    return parse_json_response(response)


async def get_customer_recommendations(
    current_items: list[str],
    menu_items: list[dict],
    budget_remaining: float = None,
    preferences: list[str] = None,
    custom_instructions: str = None,
    upsell_aggressiveness: str = "medium",
) -> dict:
    """
    Generate personalized recommendations for customers.

    Args:
        current_items: Items already in cart
        menu_items: Available menu items
        budget_remaining: Optional remaining budget
        preferences: Dietary preferences
        custom_instructions: Additional instructions
        upsell_aggressiveness: "low", "medium", or "high"
    """

    menu_summary = [
        {
            "name": i.get("name"),
            "price": i.get("price"),
            "section": i.get("section", ""),
        }
        for i in menu_items[:20]
    ]

    upsell_text = ""
    if upsell_aggressiveness == "high":
        upsell_text = "\nBe enthusiastic about upsells and premium options."
    elif upsell_aggressiveness == "low":
        upsell_text = "\nBe subtle with upsells, focus on value."

    custom_text = ""
    if custom_instructions:
        custom_text = f"\n\nADDITIONAL REQUIREMENTS: {custom_instructions}"

    prompt = f"""Suggest items to pair with the customer's order.

Current Order: {current_items if current_items else "Nothing yet"}
{"Budget: $" + f"{budget_remaining:.2f}" if budget_remaining else ""}
{"Preferences: " + ", ".join(preferences) if preferences else ""}
{upsell_text}{custom_text}

Available Items:
{json.dumps(menu_summary, indent=2)}

Respond ONLY with valid JSON:
{{"top_recommendation": {{"item": "Item Name", "reason": "Why", "pitch": "Server pitch"}}, "alternatives": [{{"item": "Name", "reason": "Why"}}], "upsells": [{{"item": "Add-on", "pitch": "Quick pitch"}}]}}"""

    response = chat_completion(prompt)
    return parse_json_response(response)


async def generate_owner_report(
    summary_data: dict,
    period: str = "weekly",
    custom_instructions: str = None,
    report_style: str = "executive",
) -> dict:
    """
    Generate an AI-powered insights report for restaurant owners.

    Args:
        summary_data: Sales and performance data
        period: "daily", "weekly", or "monthly"
        custom_instructions: Additional instructions
        report_style: "executive" (brief) or "detailed" (comprehensive)
    """

    style_text = ""
    if report_style == "detailed":
        style_text = "\nProvide a detailed, comprehensive analysis with specific numbers and actionable steps."
    else:
        style_text = "\nKeep it brief and executive-focused with clear priorities."

    custom_text = ""
    if custom_instructions:
        custom_text = f"\n\nADDITIONAL REQUIREMENTS: {custom_instructions}"

    prompt = f"""Generate a {period} insights report for a restaurant owner.

Data:
{json.dumps(summary_data, indent=2)}
{style_text}{custom_text}

Respond ONLY with valid JSON:
{{"executive_summary": "2-3 sentence overview", "highlights": ["highlight1"], "concerns": ["concern1"], "top_recommendations": [{{"action": "What to do", "impact": "Result", "effort": "low"}}], "next_steps": ["step1"]}}"""

    response = chat_completion(prompt)
    return parse_json_response(response)


def is_gemini_available() -> bool:
    """Check if OpenRouter API is configured (kept for compatibility)."""
    return OPENROUTER_API_KEY is not None and len(OPENROUTER_API_KEY) > 0
