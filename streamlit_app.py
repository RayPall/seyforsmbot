# streamlit_app.py
# ---------------------------------------------------------------------------
#  ✍️  Vygenerovat příspěvek     (WEBHOOK_POST)
#  ➕  Přidat personu            (WEBHOOK_PERSONA_ADD)
# ---------------------------------------------------------------------------

import requests, streamlit as st

# --------- Make webhooky ------------------------------------------------------
WEBHOOK_POST        = "https://hook.eu2.make.com/6m46qtelfmarmwpq1jqgomm403eg5xkw"
WEBHOOK_PERSONA_ADD = "https://hook.eu2.make.com/9yo8y77db7i6do272joo7ybfoue1qcoc"

DEFAULT_PERSONAS = [
    "Daniel Šturm", "Martin Cígler", "Marek Steiger",
    "Kristína Pastierik", "Lucie Jahnová", "Seyfor"
]

if "person_list" not in st.session_state:
    st.session_state.person_list = DEFAULT_PERSONAS.copy()

def rerun():
    (st.rerun if hasattr(st, "rerun") else st.experimental_rerun)()

# ------------------------------------------------------------------------------
st.set_page_config(page_title="LinkedIn bot", page_icon="📝")
st.title("LinkedIn bot")

tab_post, tab_persona = st.tabs(["✍️ Vygenerovat příspěvek", "➕ Přidat personu"])

# ====================== 1)  Vygenerovat příspěvek =============================
with tab_post:
    st.subheader("Vygenerovat LinkedIn příspěvek")
    with st.form("post_form"):
        topic = st.text_area("Jaké má být téma příspěvku?")
        persona = st.radio(
            "Čím stylem má být příspěvek napsán?",
            st.session_state.person_list
        )
        submitted_post = st.form_submit_button("Odeslat")

    if submitted_post:
        payload = {
            "personName":  persona,
            "postContent": topic
            # e‑mail jsme odstranili
        }

        with st.spinner("Generuji pomocí ChatGPT…"):
            try:
                res = requests.post(WEBHOOK_POST, json=payload, timeout=120)
                res.raise_for_status()
            except Exception as e:
                st.error(f"Chyba při komunikaci s Make: {e}")
                st.stop()

        try:
            post_text = res.json().get("post", "")
        except Exception:
            post_text = res.text

        post_md = post_text.strip().replace("\n", "  \n")
        st.success("Hotovo! Zde je vygenerovaný příspěvek:")
        st.markdown(post_md)

# ====================== 2)  Přidat personu ====================================
with tab_persona:
    st.subheader("Přidat novou personu")

    with st.form("persona_add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            name   = st.text_input("Jméno*")
            role   = st.text_input("Role / pozice*")
            tone   = st.text_area("Tone of Voice*")
        with col2:
            style  = st.text_area("Styl psaní*")
            lang_choices = ("Čeština", "Slovenština", "Angličtina", "Jiný")
            lang   = st.selectbox("Jazyk*", lang_choices)

            custom_lang = st.text_input("Zadejte název jazyka*") if lang == "Jiný" else ""
            sample = st.text_area("Ukázkový příspěvek*")

        submitted_persona_add = st.form_submit_button("Uložit personu")

    if submitted_persona_add:
        if not name.strip():
            st.error("Jméno je povinné.")
            st.stop()
        if lang == "Jiný" and not custom_lang.strip():
            st.error("Prosím zadej název jazyka.")
            st.stop()

        language_value = custom_lang.strip() if lang == "Jiný" else lang

        payload_add = {
            "name":     name.strip(),
            "role":     role.strip(),
            "tone":     tone.strip(),
            "style":    style.strip(),
            "language": language_value,
            "sample":   sample.strip()
        }

        with st.spinner("Ukládám personu…"):
            try:
                requests.post(WEBHOOK_PERSONA_ADD, json=payload_add, timeout=30).raise_for_status()
            except Exception as e:
                st.error(f"Chyba při ukládání: {e}")
                st.stop()

        st.session_state.person_list.append(name.strip())
        st.success("Persona uložena ✔️")
        rerun()
