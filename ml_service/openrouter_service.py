"""
File: openrouter_service.py
Authors: Hamdy El-Madbouly
Description: Core integration logic for OpenRouter API.
Contains the specific prompt engineering and context injection logic for
each AI feature. It combines the raw AI capabilities with the robust
psychological frameworks defined in `psychology_constants.py`.

Supports multiple models (DeepSeek, Mistral, Llama) and handles
mock responses when the API key is not configured.
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Import psychological and mathematical optimization principles
try:
    try:
        from .psychology_constants import (
            MENU_ENGINEERING_SYSTEM_PROMPT,
            CATEGORY_PSYCHOLOGY,
            DESCRIPTION_ENHANCEMENT_CONTEXT,
            SALES_SUGGESTIONS_CONTEXT,
            MENU_ANALYSIS_CONTEXT,
            CUSTOMER_RECOMMENDATIONS_CONTEXT,
            OWNER_REPORT_CONTEXT,
            PRICE_PSYCHOLOGY,
            MARGIN_CLASSIFICATION,
            WASTE_IMPACT,
            OPTIMIZATION_WEIGHTS,
            ANALYSIS_OUTPUT_TEMPLATE,
        )
    except (ImportError, ValueError):
        from psychology_constants import (
            MENU_ENGINEERING_SYSTEM_PROMPT,
            CATEGORY_PSYCHOLOGY,
            DESCRIPTION_ENHANCEMENT_CONTEXT,
            SALES_SUGGESTIONS_CONTEXT,
            MENU_ANALYSIS_CONTEXT,
            CUSTOMER_RECOMMENDATIONS_CONTEXT,
            OWNER_REPORT_CONTEXT,
            PRICE_PSYCHOLOGY,
            MARGIN_CLASSIFICATION,
            WASTE_IMPACT,
            OPTIMIZATION_WEIGHTS,
            ANALYSIS_OUTPUT_TEMPLATE,
        )
except ImportError as e:
    print(f"ERROR: Failed to import psychology_constants: {e}")
    raise

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

# Enhanced system prompt with behavioral economics principles
DEFAULT_SYSTEM_PROMPT = MENU_ENGINEERING_SYSTEM_PROMPT


def get_client():
    """Get the OpenRouter client."""
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not configured")

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )


def _get_mock_response(func_name: str, **kwargs) -> dict:
    """Generate mock response when AI service is unavailable."""
    import random

    if func_name == "enhance_description":
        return {
            "enhanced_description": f"Succulent {kwargs.get('item_name', 'item')} prepared to perfection. A true delight requiring no further introduction.",
            "key_selling_points": [
                "Chef's special recipe",
                "Locally sourced ingredients",
                "Perfect for sharing",
            ],
            "tips": ["Pair with our signature drinks", "Best engaged while warm"],
            "psychology_applied": ["Sensory language", "Social proof"],
        }

    elif func_name == "analyze_menu_structure":
        return {
            "overall_score": 7,
            "section_order_recommendation": ["Starters", "Mains", "Desserts"],
            "items_to_highlight": [
                kwargs.get("menu_sections", [{}])[0]
                .get("items", [{}])[0]
                .get("name", "Item")
            ],
            "items_to_reconsider": [],
            "general_recommendations": [
                "Simplify category names",
                "Use price anchoring",
            ],
            "choice_architecture_notes": ["Good use of white space"],
            "cognitive_load_assessment": "medium",
        }

    elif func_name == "generate_sales_suggestions":
        price = kwargs.get("price", 10)
        return {
            "priority": "medium",
            "suggested_price": round(price * 1.1, 2),
            "immediate_actions": ["Highlight on menu", "Train staff to upsell"],
            "marketing_tips": ["Create a combo deal"],
            "estimated_impact": "15% increase in margin",
            "margin_optimization": "Slight price increase justified by quality",
            "elasticity_assessment": "low price sensitivity",
        }

    elif func_name == "get_customer_recommendations":
        return {
            "top_recommendation": {
                "item": "Chef's Special",
                "reason": "It complements your current selection perfectly.",
                "pitch": "You must try our Chef's Special, it's a customer favorite.",
                "psychology_trigger": "social proof",
            },
            "alternatives": [{"item": "Seasonal Salad", "reason": "Lighter option"}],
            "upsells": [
                {"item": "Premium Side", "pitch": "Add a premium side for just $3"}
            ],
            "compromise_recommendation": {
                "item": "Standard Burger",
                "reason": "A classic choice",
            },
        }

    elif func_name == "generate_owner_report":
        period = kwargs.get("period", "weekly")
        return {
            "executive_summary": f"Performance for this {period} has been steady with notable growth in high-margin categories. Customer satisfaction metrics remain positive.",
            "highlights": [
                "Revenue up 5% vs last period",
                "Star items retention is strong",
                "Waste reduction targets met",
            ],
            "concerns": [
                "Labor costs slightly above target",
                "Puzzle items need visibility boost",
            ],
            "top_recommendations": [
                {
                    "action": "Promote seasonal specials",
                    "impact": "High revenue potential",
                    "effort": "low",
                    "priority_score": 9,
                },
                {
                    "action": "Review inventory levels",
                    "impact": "Cost saving",
                    "effort": "medium",
                    "priority_score": 7,
                },
            ],
            "next_steps": ["Schedule staff training", "Update digital menu board"],
            "trade_offs": ["Higher marketing spend required for growth"],
            "multi_objective_score": {
                "revenue": 8,
                "margin": 7,
                "satisfaction": 9,
                "simplicity": 8,
            },
        }

    return {"error": "Mock response not implemented"}


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
    Enhance a menu item description using behavioral economics principles.

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
        dict with enhanced_description, key_selling_points, tips, psychology_applied
    """

    if not OPENROUTER_API_KEY:
        return _get_mock_response(
            "enhance_description", item_name=item_name, price=price
        )

    # Get category-specific psychological guidance
    category_lower = category.lower() if category else "puzzle"
    category_psychology = CATEGORY_PSYCHOLOGY.get(
        category_lower, CATEGORY_PSYCHOLOGY["puzzle"]
    )

    # Determine price tier for appropriate messaging
    if price < PRICE_PSYCHOLOGY["value_threshold"]:
        price_tier = "value"
        price_guidance = (
            "Frame as generous, satisfying, honest value. Avoid cheapness signals."
        )
    elif price < PRICE_PSYCHOLOGY["premium_threshold"]:
        price_tier = "mid-range"
        price_guidance = "Balance quality signals with accessibility. Convey craftsmanship without pretension."
    else:
        price_tier = "premium"
        price_guidance = "Use premium language: artisanal, signature, hand-crafted. Justify through experience."

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

    prompt = f"""Enhance this menu item description using behavioral economics principles.

Item: {item_name}
Current Description: {current_description if current_description else "None provided"}
Category: {category} ({category_psychology['profile']})
Price: ${price:.2f} ({price_tier} tier)
Cuisine Type: {cuisine_type}

{DESCRIPTION_ENHANCEMENT_CONTEXT}

CATEGORY-SPECIFIC STRATEGY:
{category_psychology['psychology']}
Description Tone: {category_psychology['description_tone']}
{price_guidance}

Standard Guidelines:
- Use sensory words (crispy, tender, aromatic, fresh)
- Highlight premium ingredients
- Keep it concise (2-3 sentences max)
- Match the price point expectation using price-quality heuristic

{f"Additional Requirements:{chr(10)}{requirements_text}" if requirements_text else ""}

Respond ONLY with valid JSON:
{{"enhanced_description": "Your improved description", "key_selling_points": ["point1", "point2"], "tips": ["tip1", "tip2"], "psychology_applied": ["List psychological principles used"]}}"""

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

    if not OPENROUTER_API_KEY:
        return _get_mock_response("analyze_menu_structure", menu_sections=menu_sections)

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

    prompt = f"""Analyze this menu structure using choice architecture and behavioral economics principles.

Menu:
{json.dumps(menu_summary, indent=2)}
{focus_text}{custom_text}

{MENU_ANALYSIS_CONTEXT}

Respond ONLY with valid JSON:
{{"overall_score": 7, "section_order_recommendation": ["Section1", "Section2"], "items_to_highlight": ["item1"], "items_to_reconsider": ["item2"], "general_recommendations": ["rec1", "rec2"], "choice_architecture_notes": ["Golden triangle usage", "Decoy positioning"], "cognitive_load_assessment": "low/medium/high"}}"""

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

    if not OPENROUTER_API_KEY:
        return _get_mock_response(
            "generate_sales_suggestions", item_name=item_name, price=price
        )

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

    # Classify margin quality
    margin_quality = (
        "excellent"
        if margin_pct >= 70
        else (
            "good" if margin_pct >= 50 else "concerning" if margin_pct >= 35 else "poor"
        )
    )

    # Get category psychology
    category_lower = category.lower() if category else "puzzle"
    category_psychology = CATEGORY_PSYCHOLOGY.get(
        category_lower, CATEGORY_PSYCHOLOGY["puzzle"]
    )

    prompt = f"""Generate sales suggestions using mathematical optimization and behavioral economics.

Item: {item_name}
Category: {category} ({category_psychology['profile']})
Price: ${price:.2f}, Cost: ${cost:.2f}, Margin: ${margin:.2f} ({margin_pct:.1f}% - {margin_quality})
Purchases: {purchases}
{f"Section Avg Price: ${section_avg_price:.2f}" if section_avg_price else ""}
{f"Section Avg Sales: {int(section_avg_sales)}" if section_avg_sales else ""}
{strategy_text}{custom_text}

{SALES_SUGGESTIONS_CONTEXT}

CATEGORY STRATEGY:
{category_psychology['strategy']}
{category_psychology['pricing_approach']}

Respond ONLY with valid JSON:
{{"priority": "high", "suggested_price": {price}, "immediate_actions": ["action1", "action2"], "marketing_tips": ["tip1"], "estimated_impact": "Expected outcome", "margin_optimization": "strategy for improving margin", "elasticity_assessment": "low/medium/high price sensitivity"}}"""

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

    if not OPENROUTER_API_KEY:
        return _get_mock_response(
            "get_customer_recommendations", current_items=current_items
        )

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

    prompt = f"""Generate customer recommendations using behavioral economics principles.

Current Order: {current_items if current_items else "Nothing yet"}
{"Budget: $" + f"{budget_remaining:.2f}" if budget_remaining else ""}
{"Preferences: " + ", ".join(preferences) if preferences else ""}
{upsell_text}{custom_text}

Available Items:
{json.dumps(menu_summary, indent=2)}

{CUSTOMER_RECOMMENDATIONS_CONTEXT}

Respond ONLY with valid JSON:
{{"top_recommendation": {{"item": "Item Name", "reason": "Why", "pitch": "Server pitch", "psychology_trigger": "loss aversion/social proof/etc"}}, "alternatives": [{{"item": "Name", "reason": "Why"}}], "upsells": [{{"item": "Add-on", "pitch": "Quick pitch"}}], "compromise_recommendation": {{"item": "Safe middle choice", "reason": "Why this is the balanced option"}}}}"""

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

    if not OPENROUTER_API_KEY:
        return _get_mock_response("generate_owner_report", period=period)

    style_text = ""
    if report_style == "detailed":
        style_text = "\nProvide a detailed, comprehensive analysis with specific numbers and actionable steps."
    else:
        style_text = "\nKeep it brief and executive-focused with clear priorities."

    custom_text = ""
    if custom_instructions:
        custom_text = f"\n\nADDITIONAL REQUIREMENTS: {custom_instructions}"

    prompt = f"""Generate a {period} insights report using multi-objective optimization principles.

Data:
{json.dumps(summary_data, indent=2)}
{style_text}{custom_text}

{OWNER_REPORT_CONTEXT}

Respond ONLY with valid JSON:
{{"executive_summary": "2-3 sentence overview", "highlights": ["highlight1"], "concerns": ["concern1"], "top_recommendations": [{{"action": "What to do", "impact": "Result", "effort": "low", "priority_score": 8}}], "next_steps": ["step1"], "trade_offs": ["Explicit trade-off statement"], "multi_objective_score": {{"revenue": 7, "margin": 6, "satisfaction": 8, "simplicity": 7}}}}"""

    response = chat_completion(prompt)
    return parse_json_response(response)


def is_gemini_available() -> bool:
    """Check if OpenRouter API is configured (kept for compatibility)."""
    return OPENROUTER_API_KEY is not None and len(OPENROUTER_API_KEY) > 0
