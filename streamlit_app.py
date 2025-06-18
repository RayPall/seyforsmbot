# streamlit_app.py
# ---------------------------------------------------------------------------
#  ✍️  Vytvořit příspěvek   (WEBHOOK_POST)     – výběr sítí + obrázky
#  🛠  Prompt pro GPT       (panel v záložce)  – text, který se připojí do payloadu
# ---------------------------------------------------------------------------

import base64, io, json, requests, streamlit as st

# ---------- KONSTANTY ---------------------------------------------------------
WEBHOOK_POST = "https://hook.eu2.make.com/6m46qtelfmarmwpq1jqgomm403eg5xkw"
DEFAULT_PERSONA = "DefaultPersona"          # interně použitá persona
DEFAULT_PROMPT  = "Napiš kreativní a poutavý příspěvek pro sociální sítě."

# ---------- SESSION STATE -----------------------------------------------------
if "gpt_prompt" not in st.session_state:
    st.session_state.gpt_prompt = DEFAULT_PROMPT

# ---------- HELPER ------------------------------------------------------------
def files_to_base64(files):
    """Vrátí list dictů: [{'filename': .., 'data': ..}, ...]"""
    out = []
    for f in files:
        b = f.read()
        out.append({
            "filename": f.name,
            "data": base64.b64encode(b).decode("utf-8")
        })
    return out

# ---------- UI ----------------------------------------------------------------
st.set_page_config(page_title="LinkedIn bot", page_icon="📝")
st.title("LinkedIn bot")

tab_post, tab_prompt = st.tabs(["✍️ Vytvořit příspěvek", "🛠 Prompt pro GPT"])

# ====================== 1)  Vytvořit příspěvek ================================
with tab_post:
    st.subheader("Vytvořit příspěvek")

    with st.form("post_form"):
        topic = st.text_area("Téma / obsah příspěvku*", height=200)

        networks = st.multiselect(
            "Vyber sociální sítě",
            ["Facebook", "Instagram", "Threads"],
            placeholder="Vyber jednu či více sítí…"
        )

        uploaded_imgs = st.file_uploader(
            "Přilož obrázky (JPEG/PNG, více souborů lze vybrat najednou)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )

        submitted = st.form_submit_button("Odeslat do Make")

    if submitted:
        if not topic.strip():
            st.error("Téma příspěvku je povinné.")
            st.stop()
        if not networks:
            st.warning("Nezvolil jsi žádnou sociální síť – pokračuji, ale možná to nechceš.")

        payload = {
            "personaName":  DEFAULT_PERSONA,
            "postContent":  topic.strip(),
            "socialNetworks": networks,          # list[str]
            "gptPrompt":   st.session_state.gpt_prompt,
            "images": files_to_base64(uploaded_imgs) if uploaded_imgs else []
        }

        with st.spinner("Odesílám na Make…"):
            try:
                r = requests.post(WEBHOOK_POST, json=payload, timeout=120)
                r.raise_for_status()
            except Exception as e:
                st.error(f"Chyba při komunikaci s Make: {e}")
                st.stop()

        try:
            result = r.json().get("post", "")
        except Exception:
            result = r.text

        st.success("Hotovo! Generovaný příspěvek:")
        st.markdown(result.strip().replace("\n", "  \n"))

# ====================== 2)  Prompt pro GPT ====================================
with tab_prompt:
    st.subheader("Prompt pro GPT (součást payloadu)")

    new_prompt = st.text_area(
        "Uprav prompt dle libosti:",
        value=st.session_state.gpt_prompt,
        height=180
    )
    if st.button("Uložit prompt"):
        st.session_state.gpt_prompt = new_prompt.strip() or DEFAULT_PROMPT
        st.success("Prompt uložen.")
