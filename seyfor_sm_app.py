# streamlit_app.py
import base64, pathlib, requests, streamlit as st

# ---------- konfigurace -------------------------------------------------------
WEBHOOK_POST = "https://hook.eu2.make.com/6m46qtelfmarmwpq1jqgomm403eg5xkw"
PROMPT_FILE  = pathlib.Path("prompt.txt")

DEFAULT_PROMPT = """... (výchozí text promptu z předchozí verze) ...""".strip()

# ---------- práce s promptem --------------------------------------------------
def load_prompt() -> str:
    return PROMPT_FILE.read_text("utf-8").strip() if PROMPT_FILE.exists() else DEFAULT_PROMPT

def save_prompt(txt: str):
    PROMPT_FILE.write_text(txt.strip(), encoding="utf-8")

# ---------- session -----------------------------------------------------------
if "gpt_prompt" not in st.session_state:
    st.session_state.gpt_prompt = load_prompt()

def rerun():
    (st.rerun if hasattr(st, "rerun") else st.experimental_rerun)()

# ---------- helper ------------------------------------------------------------
def files_to_base64(files):
    return [
        {"filename": f.name,
         "data": base64.b64encode(f.read()).decode("utf-8")}
        for f in files
    ]

# ---------- ui ----------------------------------------------------------------
st.set_page_config("LinkedIn bot", "📝")
st.title("LinkedIn bot")

tab_post, tab_prompt = st.tabs(["✍️ Vytvořit příspěvek", "🛠 Prompt pro GPT"])

# ----------------------- vytváření příspěvku ----------------------------------
with tab_post:
    with st.form("post_form"):
        topic = st.text_area("Téma / obsah příspěvku*", height=200)
        networks = st.multiselect(
            "Vyber sociální sítě", ["Facebook", "Instagram", "Threads"]
        )
        imgs = st.file_uploader(
            "Přilož obrázky (JPEG/PNG)", type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )
        send = st.form_submit_button("Odeslat do Make")

    if send:
        if not topic.strip():
            st.error("Téma příspěvku je povinné."); st.stop()

        payload = {
            "postContent":   topic.strip(),
            "gptPrompt":     st.session_state.gpt_prompt,
            "socialNetworks": networks,
            "images": files_to_base64(imgs) if imgs else []
        }

        with st.spinner("Odesílám na Make…"):
            try:
                r = requests.post(WEBHOOK_POST, json=payload, timeout=120)
                r.raise_for_status()
            except Exception as e:
                st.error(f"Chyba při komunikaci s Make: {e}")
                st.stop()

        # robustní načtení odpovědi
        try:
            resp = r.json()
            post = resp.get("post", str(resp)) if isinstance(resp, dict) else str(resp)
        except ValueError:
            post = r.text or "⚠️ Odpověď nebyla ve formátu JSON."

        st.success("Hotovo! Generovaný příspěvek:")
        st.markdown(post.strip().replace("\n", "  \n"))

# --------------------------- panel promptu ------------------------------------
with tab_prompt:
    st.subheader("Prompt pro GPT (uloženo v prompt.txt)")
    new_txt = st.text_area("Uprav prompt:", st.session_state.gpt_prompt, height=300)
    if st.button("Uložit prompt"):
        st.session_state.gpt_prompt = new_txt.strip() or DEFAULT_PROMPT
        save_prompt(st.session_state.gpt_prompt)
        st.success("Prompt uložen."); rerun()
