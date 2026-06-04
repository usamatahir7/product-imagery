from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from agents.image_agent import MODEL as IMAGE_MODEL, ImageAgent
from agents.prompt_agent import MODEL as PROMPT_MODEL, ProductContext, PromptAgent, ReferenceImage
from data.industry_products import INDUSTRIES, INDUSTRY_PRODUCTS
from utils.prompt_logger import log_prompt_to_sheet

ROOT = Path(__file__).resolve().parent
DEFAULT_PROMPT_PATH = ROOT / "assets" / "default_ui" / "default_prompt.txt"
DEFAULT_REFERENCE_PATH = ROOT / "assets" / "default_ui" / "default_reference.webp"
DEFAULT_OUTPUT_PATH = ROOT / "assets" / "default_ui" / "default_output.jpg"

DEFAULT_INDUSTRY = "FDA Food Packaging"
DEFAULT_PRODUCT = "Dairy"
DEFAULT_BRAND_STYLING = "Stand up pouch"
DEFAULT_SCENE = "grocery store shelf"

st.set_page_config(
    page_title="Brand Image Generator",
    page_icon="🎨",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; }
    div[data-testid="stTextInput"] label p,
    div[data-testid="stSelectbox"] label p {
        font-weight: 600;
        color: #334155;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_default_prompt() -> str:
    return DEFAULT_PROMPT_PATH.read_text(encoding="utf-8")


def load_default_reference() -> ReferenceImage:
    return ReferenceImage(
        data=DEFAULT_REFERENCE_PATH.read_bytes(),
        mime_type="image/webp",
    )


def load_defaults() -> tuple[str, ReferenceImage, str]:
    return (
        load_default_prompt(),
        load_default_reference(),
        str(DEFAULT_OUTPUT_PATH),
    )


def init_results_state() -> None:
    if "display_prompt" not in st.session_state:
        prompt, reference, output = load_defaults()
        st.session_state.display_prompt = prompt
        st.session_state.display_reference = reference
        st.session_state.display_output = output
    if "editable_prompt" not in st.session_state:
        st.session_state.editable_prompt = st.session_state.display_prompt


def init_form_state() -> None:
    if "industry" not in st.session_state:
        st.session_state.industry = DEFAULT_INDUSTRY
    if "product_type" not in st.session_state:
        st.session_state.product_type = DEFAULT_PRODUCT
    if "brand_styling" not in st.session_state:
        st.session_state.brand_styling = DEFAULT_BRAND_STYLING
    if "scene" not in st.session_state:
        st.session_state.scene = DEFAULT_SCENE
    if "default_reference_cleared" not in st.session_state:
        st.session_state.default_reference_cleared = False


def to_reference_image(uploaded_file) -> ReferenceImage | None:
    if uploaded_file is None:
        return None
    mime_type = uploaded_file.type or "image/png"
    return ReferenceImage(data=uploaded_file.getvalue(), mime_type=mime_type)


def resolve_reference(uploaded_file) -> ReferenceImage | None:
    if uploaded_file is not None:
        return to_reference_image(uploaded_file)
    if st.session_state.get("default_reference_cleared"):
        return None
    return load_default_reference()


def render_results(reference_upload) -> None:
    reference = st.session_state.get("display_reference")

    st.divider()
    st.subheader("Results")

    result_col1, result_col2 = st.columns([1, 1])

    with result_col1:
        st.markdown(f"**Prompt** · edit and regenerate image below")
        st.text_area(
            "prompt_output",
            height=220,
            label_visibility="collapsed",
            key="editable_prompt",
            help="Edit this prompt, then click Generate Image to create a new image.",
        )

        if st.button(
            "Generate Image from Prompt",
            type="secondary",
            use_container_width=True,
            key="regenerate_image_btn",
        ):
            prompt = st.session_state.editable_prompt.strip()
            if not prompt:
                st.error("Prompt cannot be empty.")
            else:
                image_ref = resolve_reference(reference_upload)
                try:
                    with st.spinner(
                        f"Generating image with {IMAGE_MODEL}"
                        + (" (using reference)" if image_ref else "")
                        + "..."
                    ):
                        image_path = ImageAgent().generate(prompt, reference=image_ref)
                    st.session_state.display_prompt = prompt
                    st.session_state.display_output = str(image_path)
                    if image_ref:
                        st.session_state.display_reference = image_ref
                    st.rerun()
                except Exception as exc:
                    st.error(f"Image generation failed: {exc}")

        if reference:
            st.markdown("**Reference Image**")
            st.image(reference.data, width=280)

    with result_col2:
        st.markdown(f"**Generated Image** · `{IMAGE_MODEL}`")
        st.image(st.session_state.display_output, use_container_width=True)


init_results_state()
init_form_state()

st.title("Brand Image Generator")
st.caption(
    f"Configure your pouch packaging context, generate a prompt with **{PROMPT_MODEL}**, "
    f"then an image with **{IMAGE_MODEL}**. Optionally upload a reference image."
)

st.subheader("Product Context")
col1, col2 = st.columns(2)

with col1:
    industry = st.selectbox("Industry", INDUSTRIES, key="industry")
    products = INDUSTRY_PRODUCTS[industry]
    if st.session_state.product_type not in products:
        st.session_state.product_type = products[0]
    product_type = st.selectbox("Product", products, key="product_type")

with col2:
    brand_styling = st.text_input(
        "Brand Styling",
        placeholder="e.g. Stand up pouch, CareFoil material, matte finish, zipper resealable",
        key="brand_styling",
    )
    scene = st.text_input(
        "Scene",
        placeholder="e.g. grocery store shelf, kitchen counter, peg hook in retail aisle",
        key="scene",
    )

reference_upload = st.file_uploader(
    "Reference image (optional)",
    type=["png", "jpg", "jpeg", "webp"],
    help="Upload a pouch or product photo to replace the default reference.",
    key="reference_upload",
)

if reference_upload is None and not st.session_state.default_reference_cleared:
    name_col, clear_col = st.columns([11, 1])
    with name_col:
        st.markdown(
            '<p style="margin:0;padding:0.35rem 0;font-size:0.875rem;color:#31333F;">'
            "default_reference.webp</p>",
            unsafe_allow_html=True,
        )
    with clear_col:
        if st.button("✕", key="clear_default_reference", help="Remove default reference"):
            st.session_state.default_reference_cleared = True
            st.rerun()

submitted = st.button("Generate Prompt & Image", type="primary", use_container_width=True)

if submitted:
    context = ProductContext(
        industry=industry,
        product_type=product_type,
        brand_styling=brand_styling.strip(),
        scene=scene.strip(),
    )
    reference = resolve_reference(reference_upload)

    try:
        with st.spinner(f"Generating prompt with {PROMPT_MODEL}..."):
            prompt = PromptAgent().generate(context, reference=reference)

        logged = log_prompt_to_sheet(
            prompt=prompt,
            industry=industry,
            product=product_type,
            brand_styling=brand_styling.strip(),
            scene=scene.strip(),
            action="generate_prompt_and_image",
            has_reference=reference is not None,
        )
        if not logged and os.environ.get("DEBUG_SHEET_LOGGING", "").strip().lower() in {"1", "true", "yes"}:
            st.warning("Prompt logging to Google Sheets failed. Run scripts/test_sheet_logging.py to debug.")

        st.session_state.display_prompt = prompt
        st.session_state.editable_prompt = prompt
        st.session_state.display_reference = reference

        with st.spinner(
            f"Generating image with {IMAGE_MODEL}"
            + (" (using reference)" if reference else "")
            + "..."
        ):
            image_path = ImageAgent().generate(prompt, reference=reference)
        st.session_state.display_output = str(image_path)
    except Exception as exc:
        st.error(f"Generation failed: {exc}")

render_results(reference_upload)
