import base64
import pathlib
import requests
import streamlit as st

# ---------------------- konfigurace -------------------------------------------
WEBHOOK_POST = "https://hook.eu2.make.com/99h47b3gribi1wuywxa5wuu4vp9q27mr"
PROMPT_FILE  = pathlib.Path("prompt.txt")

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

# ------------------- práce s promptem -----------------------------------------
def load_prompt() -> str:
    if PROMPT_FILE.exists():
        txt = PROMPT_FILE.read_text("utf-8").strip()
        return txt or DEFAULT_PROMPT          # fallback na default
    return DEFAULT_PROMPT

def save_prompt(text: str):
    PROMPT_FILE.write_text(text.strip() or DEFAULT_PROMPT, encoding="utf-8")

# ------------------- Streamlit session ----------------------------------------
if "gpt_prompt" not in st.session_state:
    st.session_state.gpt_prompt = load_prompt()

rerun = st.rerun if hasattr(st, "rerun") else st.experimental_rerun

# ------------------- pomocná funkce -------------------------------------------
def files_to_base64(files):
    return [
        {"filename": f.name,
         "data": base64.b64encode(f.read()).decode("utf-8")}
        for f in files
    ]

# ------------------- UI -------------------------------------------------------
st.set_page_config(page_title="LinkedIn bot", page_icon="📝")
st.title("LinkedIn bot")

tab_post, tab_prompt = st.tabs(["✍️ Vytvořit příspěvek", "🛠 Prompt pro GPT"])

# ============ 1) formulář pro příspěvek =======================================
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
            "gptPrompt":     st.session_state.gpt_prompt or DEFAULT_PROMPT,
            "socialNetworks": networks,
            "images":        files_to_base64(imgs) if imgs else []
        }

        with st.spinner("Odesílám na Make…"):
            try:
                resp = requests.post(WEBHOOK_POST, json=payload, timeout=120)
                resp.raise_for_status()
            except Exception as e:
                st.error(f"Chyba při komunikaci s Make: {e}"); st.stop()

        # robustní načtení odpovědi (JSON i plain text)
        try:
            data = resp.json()
            post = data["post"] if isinstance(data, dict) else str(data)
        except ValueError:
            post = resp.text or "⚠️ Odpověď nebyla ve formátu JSON."

        st.success("Hotovo! Generovaný příspěvek:")
        st.markdown(post.strip().replace("\n", "  \n"))

# ============ 2) panel pro úpravu promptu =====================================
with tab_prompt:
    st.subheader("Prompt pro GPT (uloženo v prompt.txt)")
    new_prompt = st.text_area(
        "Uprav prompt dle libosti:", st.session_state.gpt_prompt, height=300
    )
    if st.button("Uložit prompt"):
        st.session_state.gpt_prompt = new_prompt.strip() or DEFAULT_PROMPT
        save_prompt(st.session_state.gpt_prompt)
        st.success("Prompt uložen.")
        rerun()
