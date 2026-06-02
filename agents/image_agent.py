import base64
import io
from pathlib import Path
from uuid import uuid4

from openai import OpenAI

from agents.config import get_openai_api_key
from agents.prompt_agent import ReferenceImage

MODEL = "gpt-image-1-mini"
EDIT_MODEL = "gpt-image-1.5"
INPUT_FIDELITY = "high"
QUALITY = "medium"
SIZE = "1024x1024"


class ImageAgent:
    """Generates images from prompts using GPT Image models."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = MODEL,
        output_dir: Path | None = None,
    ) -> None:
        self.client = OpenAI(api_key=api_key or get_openai_api_key())
        self.model = model
        self.quality = QUALITY
        self.size = SIZE
        self.output_dir = output_dir or Path(__file__).resolve().parent.parent / "assets" / "generated"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, prompt: str, reference: ReferenceImage | None = None) -> Path:
        if reference:
            ext = reference.mime_type.split("/")[-1]
            if ext == "jpeg":
                ext = "jpg"
            image_file = (f"reference.{ext}", io.BytesIO(reference.data), reference.mime_type)
            response = self.client.images.edit(
                model=EDIT_MODEL,
                image=image_file,
                prompt=prompt,
                size=self.size,
                quality=self.quality,
                input_fidelity=INPUT_FIDELITY,
            )
        else:
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size=self.size,
                quality=self.quality,
            )

        return self._save_response(response)

    def _save_response(self, response) -> Path:
        if not response.data:
            raise RuntimeError("OpenAI returned no image data.")

        image_data = response.data[0]
        if image_data.b64_json:
            image_bytes = base64.b64decode(image_data.b64_json)
        elif image_data.url:
            import urllib.request

            with urllib.request.urlopen(image_data.url) as resp:
                image_bytes = resp.read()
        else:
            raise RuntimeError("OpenAI returned no image content.")

        output_path = self.output_dir / f"{uuid4().hex}.png"
        output_path.write_bytes(image_bytes)
        return output_path
