# streamlit_app.py
# ---------------------------------------------------------------------------
#  ✍️  Vytvořit příspěvek   (WEBHOOK_POST)     – výběr sítí + obrázky
#  🛠  Prompt pro GPT       – trvale uložen v prompt.txt
# ---------------------------------------------------------------------------

import base64, pathlib, requests, streamlit as st

# ---------- Konfigurace -------------------------------------------------------
WEBHOOK_POST = "https://hook.eu2.make.com/6m46qtelfmarmwpq1jqgomm403eg5xkw"
DEFAULT_PERSONA = "DefaultPersona"
PROMPT_FILE = pathlib.Path("prompt.txt")

DEFAULT_PROMPT = """
Napiš příspěvek na sociální sítě společnosti **Seyfor** podle následujících instrukcí:

**TONE OF VOICE**
• Odborný a důvěryhodný – uveď alespoň 2 konkrétní čísla či fakta  
• Vstřícný a vděčný – poděkuj partnerům, kolegům nebo účastníkům  
• Motivační a zapojující – obsahuje jasné CTA a lidskou výzvu  
• Profesně přátelský – korporátní, ale neformálně lidský; používej emoji 🎉 🏃‍♀️ 💜

**STYL PSANÍ**
1. Úvodní věta s emoji a hlavním sdělením  
2. 2-3 krátké odstavce nebo odrážky (✅ / 👉 / •) s konkrétními fakty  
3. Závěrečná výzva k akci + poděkování  
• Jazyk: **čeština**  
• V každém odstavci max. 2 věty  
• Na závěr 3-5 relevantních hashtagů (#jsmeseyfor …)

**DOPLŇKOVÁ PRAVIDLA**
• Nepiš datum ani místo, pokud není zadáno ve vstupu  
• U metrik vždy použij číslici (30 let, 4 města, 2 týmy)  
• Emoji zakomponuj organicky, nepřekládej jimi slova  
• Rozsah do ≈ 120 slov  

**VÝSTUP**  
Vrátíš pouze text příspěvku – bez uvozovek a bez formátování kódu.
""".strip()

# ---------- Práce s promptem --------------------------------------------------
def load_prompt() -> str:
    return PROMPT_FILE.read_text(encoding="utf-8").strip() if PROMPT_FILE.exists() else DEFAULT_PROMPT

def save_prompt(txt: str):
    PROMPT_FILE.write_text(txt.strip(), encoding="utf-8")

# ---------- Session state -----------------------------------------------------
if "gpt_prompt" not in st.session_state:
    st.session_state.gpt_prompt = load_prompt()

def rerun():
    (st.rerun if hasattr(st, "rerun") else st.experimental_rerun)()

# ---------- Pomocná funkce ----------------------------------------------------
def files_to_base64(files):
    return [
        {"filename": f.name, "data": base64.b64encode(f.read()).decode("utf-8")}
        for f in files
    ]

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
            "personaName": DEFAULT_PERSONA,
            "postContent": topic.strip(),
            "socialNetworks": networks,
            "gptPrompt": st.session_state.gpt_prompt,
            "images": files_to_base64(imgs) if imgs else []
        }

        with st.spinner("Odesílám na Make…"):
            try:
                r = requests.post(WEBHOOK_POST, json=payload, timeout=120)
                r.raise_for_status()
            except Exception as e:
                st.error(f"Chyba při komunikaci s Make: {e}"); st.stop()

        # ---------- Robustní načtení odpovědi ----------
        try:
            resp = r.json()
            post = resp.get("post", str(resp)) if isinstance(resp, dict) else str(resp)
        except ValueError:
            post = r.text or "⚠️ Odpověď nebyla ve formátu JSON."

        st.success("Hotovo! Generovaný příspěvek:")
        st.markdown(post.strip().replace("\n", "  \n"))

# ====================== 2)  Prompt pro GPT ====================================
with tab_prompt:
    st.subheader("Prompt pro GPT (trvale uložen v prompt.txt)")
    edited = st.text_area(
        "Uprav prompt dle libosti:",
        value=st.session_state.gpt_prompt,
        height=300
    )
    if st.button("Uložit prompt"):
        st.session_state.gpt_prompt = edited.strip() or DEFAULT_PROMPT
        save_prompt(st.session_state.gpt_prompt)
        st.success("Prompt uložen."); rerun()
