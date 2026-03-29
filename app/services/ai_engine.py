from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

# Cap stored history turns included in the prompt (each turn = user + model pair segments).
_MAX_HISTORY_MESSAGES = 40


class GeminiInterpreter:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set!")
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-flash-lite"

    def _normalize_chart_data(self, chart_data):
        """Support legacy rows where chart_data was a flat list of points."""
        if chart_data is None:
            return {"points": [], "aspects": []}
        if isinstance(chart_data, list):
            return {"points": chart_data, "aspects": []}
        points = chart_data.get("points") or []
        aspects = chart_data.get("aspects") or []
        return {"points": points, "aspects": aspects}

    def _prepare_data_text(self, chart_data):
        """Structured sections so the model can scan planets, aspects, and houses reliably."""
        data = self._normalize_chart_data(chart_data)
        points = data["points"]
        aspects = data["aspects"]

        planets_lines = []
        house_lines = []
        for p in points:
            name = p.get("name", "?")
            line = f"- {name}: {p.get('sign', '?')} at {p.get('degree_in_sign', '?')}° (ecliptic {p.get('total_degree', '?')}°)"
            if "House" in name:
                house_lines.append(line)
            else:
                planets_lines.append(line)

        aspects_lines = [
            f"- {a.get('p1', '?')} {a.get('aspect', '?')} {a.get('p2', '?')} (orb {a.get('orb', '?')}°)"
            for a in aspects
        ]

        planets_text = "\n".join(planets_lines) or "(none)"
        aspects_text = "\n".join(aspects_lines) or "(none)"
        houses_text = "\n".join(house_lines) or "(none)"
        return planets_text, aspects_text, houses_text

    def generate_standard_report(self, chart_data: dict, profile_name: str) -> str:
        planets, aspects, houses = self._prepare_data_text(chart_data)

        prompt = f"""
            You are an elite Psychological Astrologer.
            Write a structured birth chart analysis for: {profile_name}.
            Avoid listing: "Don't just list planets. Instead, tell a story about how their energies merge."
            Target Audience: "Write for an intelligent adult seeking deep psychological insight."
            Formatting: "Use bold text for key psychological archetypes but never for planet names."
            
            FORMAT YOUR RESPONSE EXACTLY LIKE THIS (use markdown):

            ## Core Identity
            [Sun, Moon, Ascendant synthesis — 2-3 paragraphs]

            ## Mind & Communication
            [Mercury, 3rd house — 1-2 paragraphs]

            ## Love & Relationships
            [Venus, 7th house — 1-2 paragraphs]

            ## Drive & Ambition
            [Mars, 1st/10th house — 1-2 paragraphs]

            ## Life Challenges & Growth
            [Saturn, South/North Node aspects — 1-2 paragraphs]

            ## Key Aspects
            [Most significant aspects and their meaning — 1-2 paragraphs]

            STRICT RULES:
            - NO raw data, NO JSON, NO degree numbers in the text
            - Synthesize everything into flowing narrative
            - Professional, analytical tone
            - English only

            RAW DATA (for your reference only, do not copy into output):
            --- PLANETS ---
            {planets}
            --- ASPECTS ---
            {aspects}
            --- HOUSES ---
            {houses}
            """
        try:
            response = self.client.models.generate_content(model=self.model_id, contents=prompt)
            return response.text
        except Exception as e:
            print(f"Gemini Error: {str(e)}")
            raise

    def _format_history_for_prompt(self, history: list | None) -> str:
        if not history:
            return ""
        lines = []
        for item in history[-_MAX_HISTORY_MESSAGES:]:
            role = item.get("role") or "user"
            parts = item.get("parts")
            if isinstance(parts, list) and parts:
                text = parts[0]
            else:
                text = item.get("content") or ""
            if not str(text).strip():
                continue
            who = "User" if role == "user" else "Assistant"
            lines.append(f"{who}: {text}")
        return "\n".join(lines)

    def answer_question(
        self,
        chart_data: dict,
        report: str,
        question: str,
        history: list | None = None,
    ) -> str:
        """
        Answer using one generate_content call so behavior is predictable across SDK versions.
        Prior turns are passed as plain text (truncated) to stay within context limits.
        """
        planets, aspects, houses = self._prepare_data_text(chart_data)
        history_block = self._format_history_for_prompt(history)

        prior = ""
        if history_block:
            prior = f"""
PRIOR CONVERSATION (most recent last; use for continuity only):
{history_block}
"""

        prompt = f"""
You are a professional astrologer. You previously wrote this report:
---
{report}
---
{prior}
Based on the raw chart data below, answer this specific user question:
"{question}"

STRICT GUIDELINES:
1. BE SPECIFIC: Reference planet positions, house cusps, and aspects from the data when relevant.
2. CONTEXT: Use the prior conversation only to resolve follow-ups; ground answers in the chart.
3. TONE: Analytical and professional.
4. LANGUAGE: Answer in English.

RAW DATA:
--- PLANETS & ANGLES ---
{planets}
--- ASPECTS ---
{aspects}
--- HOUSE CUSPS ---
{houses}
"""
        try:
            response = self.client.models.generate_content(model=self.model_id, contents=prompt)
            return response.text
        except Exception as e:
            print(f"Gemini Error: {str(e)}")
            raise
