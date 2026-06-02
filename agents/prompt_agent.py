import base64
from dataclasses import dataclass

from openai import OpenAI

from agents.config import get_openai_api_key

MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """You are an expert prompt writer for AI image generation models.
Given product context (industry, product type, brand styling, scene), write a single
detailed image generation prompt suitable for models like DALL-E, Stable Diffusion, or Midjourney.

Requirements:
- One cohesive paragraph, no bullet points
- Include lighting, composition, mood, and visual style
- Reflect the brand styling and scene naturally
- Commercial product photography quality
- Do not include meta commentary, only the prompt itself"""

REFERENCE_SYSTEM_PROMPT = """You are an expert prompt writer for AI image generation models.
A reference product image will be provided. Write a single detailed image generation prompt
for an image-editing model that will use that reference.

Requirements:
- Preserve the core product identity, shape, and packaging from the reference image
- Apply the requested brand styling, scene, lighting, and mood from the text context
- One cohesive paragraph, no bullet points
- Commercial product photography quality
- Do not include meta commentary, only the prompt itself"""


@dataclass
class ProductContext:
    industry: str
    product_type: str
    brand_styling: str
    scene: str


@dataclass
class ReferenceImage:
    data: bytes
    mime_type: str


class PromptAgent:
    """Generates image prompts from product context using GPT-4o-mini."""

    def __init__(self, api_key: str | None = None, model: str = MODEL) -> None:
        self.client = OpenAI(api_key=api_key or get_openai_api_key())
        self.model = model

    def generate(self, context: ProductContext, reference: ReferenceImage | None = None) -> str:
        user_text = (
            f"Industry: {context.industry or 'not specified'}\n"
            f"Product type: {context.product_type or 'not specified'}\n"
            f"Brand styling: {context.brand_styling or 'not specified'}\n"
            f"Scene: {context.scene or 'not specified'}"
        )

        if reference:
            system_prompt = REFERENCE_SYSTEM_PROMPT
            user_content: str | list = [
                {"type": "text", "text": user_text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{reference.mime_type};base64,{base64.b64encode(reference.data).decode()}",
                    },
                },
            ]
        else:
            system_prompt = SYSTEM_PROMPT
            user_content = user_text

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.7,
        )

        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("OpenAI returned an empty prompt.")
        return content.strip()
