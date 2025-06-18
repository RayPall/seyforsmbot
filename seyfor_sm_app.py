# streamlit_app.py
import base64, pathlib, requests, streamlit as st

# ---------- CESTA K SOUBORU S PROMPTEM ----------------------------------------
PROMPT_FILE   = pathlib.Path("prompt.txt")

# ---------- DEFAULT PROMPT ----------------------------------------------------
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

# ---------- FUNKCE PRO PRÁCI S PROMPTEM --------------------------------------
def load_prompt() -> str:
    if PROMPT_FILE.exists():
        return PROMPT_FILE.read_text(encoding="utf-8").strip()
    return DEFAULT_PROMPT

def save_prompt(text: str):
    PROMPT_FILE.write_text(text.strip(), encoding="utf-8")

# ---------- SESSION STATE -----------------------------------------------------
if "gpt_prompt" not in st.session_state:
    st.session_state.gpt_prompt = load_prompt()

# ---------- OSTATNÍ KONSTANTY -------------------------------------------------
WEBHOOK_POST    = "https://hook.eu2.make.com/6m46qtelfmarmwpq1jqgomm403eg5xkw"
DEFAULT_PERSONA = "DefaultPersona"

# ---------- HELPER ------------------------------------------------------------
def files_to_base64(files):
    out = []
    for f in files:
        out.append(
            {"filename": f.name,
             "data": base64.b64encode(f.read()).decode("utf-8")}
        )
    return out

def rerun():   # kompatibilita verzí Streamlit
    (st.rerun if hasattr(st, "rerun") else st.experimental_rerun)()

# ---------- UI ----------------------------------------------------------------
st.set_page_config(page_title="LinkedIn bot", page_icon="📝")
st.title("LinkedIn bot")

tab_post, tab_prompt = st.tabs(["✍️ Vytvořit příspěvek", "🛠 Prompt pro GPT"])

# ====================== 1)  Vytvořit příspěvek ================================
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
        submitted = st.form_submit_button("Odeslat do Make")

    if submitted:
        if not topic.strip():
            st.error("Téma příspěvku je povinné."); st.stop()

        payload = {
            "personaName":  DEFAULT_PERSONA,
            "postContent":  topic.strip(),
            "socialNetworks": networks,
            "gptPrompt":    st.session_state.gpt_prompt,
            "images": files_to_base64(imgs) if imgs else []
        }

        with st.spinner("Odesílám na Make…"):
            try:
                r = requests.post(WEBHOOK_POST, json=payload, timeout=120)
                r.raise_for_status()
            except Exception as e:
                st.error(f"Chyba při komunikaci s Make: {e}"); st.stop()

        post = r.json().get("post", r.text)
        st.success("Hotovo! Generovaný příspěvek:")
        st.markdown(post.strip().replace("\n", "  \n"))

# ====================== 2)  Prompt pro GPT ====================================
with tab_prompt:
    st.subheader("Prompt pro GPT (trvale uložen v souboru)")

    prompt_text = st.text_area(
        "Uprav prompt dle libosti:",
        value=st.session_state.gpt_prompt,
        height=300
    )
    if st.button("Uložit prompt"):
        st.session_state.gpt_prompt = prompt_text.strip() or DEFAULT_PROMPT
        save_prompt(st.session_state.gpt_prompt)
        st.success("Prompt uložen a příště se načte ze souboru.")
        rerun()
