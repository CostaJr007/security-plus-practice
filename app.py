import streamlit as st
import json
import os

# --- SETUP ---
st.set_page_config(page_title="Simulado Security+", layout="wide")

st.markdown("""
<style>
    /* Estilo robusto para explicação */
    .exp-container {
        margin-top: 20px;
        padding: 20px;
        background-color: #f0f7fb;
        border-left: 5px solid #007bff;
        border-radius: 5px;
        color: #333;
    }
    .exp-title {
        font-weight: bold;
        color: #0056b3;
        margin-bottom: 10px;
        font-size: 1.1em;
    }
</style>
""", unsafe_allow_html=True)


# --- CARREGAR DADOS ---
@st.cache_data
def get_data():
    if os.path.exists('questions_db_final.json'):
        with open('questions_db_final.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


questions = get_data()

if not questions:
    st.error("❌ Execute o script 'extractor_cross.py' primeiro!")
    st.stop()

# --- SESSÃO ---
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'answers' not in st.session_state: st.session_state.answers = {}  # {id: {'escolha': 'A', 'acertou': True}}
if 'filter' not in st.session_state: st.session_state.filter = False


# --- LÓGICA DE FILTRO ---
def get_qs():
    if st.session_state.filter:
        ids = [k for k, v in st.session_state.answers.items() if not v['acertou']]
        return [q for q in questions if q['id'] in ids]
    return questions


lista_atual = get_qs()

# Proteção de índice
if st.session_state.idx >= len(lista_atual): st.session_state.idx = 0

# --- SIDEBAR ---
with st.sidebar:
    st.title("📊 Painel")
    answered = len(st.session_state.answers)
    correct = sum(1 for v in st.session_state.answers.values() if v['acertou'])
    wrong = answered - correct

    c1, c2 = st.columns(2)
    c1.metric("Acertos", correct)
    c2.metric("Erros", wrong)

    st.divider()

    # Análise de Tópicos
    st.caption("Desempenho por Domínio:")
    topic_data = {}
    for qid, data in st.session_state.answers.items():
        # Achar tópico original
        orig = next((x for x in questions if x['id'] == qid), None)
        if orig:
            t = orig.get('topic', 'Geral')
            if t not in topic_data: topic_data[t] = {'tot': 0, 'ok': 0}
            topic_data[t]['tot'] += 1
            if data['acertou']: topic_data[t]['ok'] += 1

    for t, vals in topic_data.items():
        perc = int((vals['ok'] / vals['tot']) * 100)
        st.text(f"{t[:25]}..")
        st.progress(perc / 100)

    st.divider()
    if wrong > 0:
        txt = "Sair da Revisão" if st.session_state.filter else "Revisar Erros"
        if st.button(txt):
            st.session_state.filter = not st.session_state.filter
            st.session_state.idx = 0
            st.rerun()

    if st.button("Resetar"):
        st.session_state.answers = {}
        st.rerun()

# --- TELA ---
if not lista_atual:
    st.success("Lista vazia ou finalizada!")
    st.stop()

q_data = lista_atual[st.session_state.idx]
qid = str(q_data['id'])

st.progress((st.session_state.idx + 1) / len(lista_atual))
st.caption(f"Questão {st.session_state.idx + 1}/{len(lista_atual)} | ID: {qid} | Tema: {q_data.get('topic')}")
st.markdown(f"### {q_data['question']}")

opts = [f"{k}) {v}" for k, v in q_data['options'].items()]
res = st.session_state.answers.get(qid)

# --- LÓGICA DE EXIBIÇÃO ---
if not res:
    # PERGUNTA
    val = st.radio("Alternativas:", opts, index=None, key=qid)
    if st.button("Confirmar", type="primary"):
        if val:
            letra = val.split(")")[0]
            ok = (letra == q_data['answer'])
            st.session_state.answers[qid] = {'escolha': val, 'acertou': ok}
            st.rerun()
        else:
            st.warning("Escolha uma opção!")
else:
    # RESPOSTA + EXPLICAÇÃO
    u_val = res['escolha']
    try:
        idx = opts.index(u_val)
    except:
        idx = 0
    st.radio("Sua escolha:", opts, index=idx, disabled=True)

    # Feedback
    correta = q_data['answer']
    if res['acertou']:
        st.success(f"✅ Correto! Resposta: {correta}")
    else:
        st.error(f"❌ Errado. Você marcou {u_val.split(')')[0]}, a certa é {correta}")

    # --- BLOCO DA EXPLICAÇÃO ---
    st.markdown(f"""
    <div class="exp-container">
        <div class="exp-title">📖 Explicação Detalhada</div>
        {q_data['explanation']}
    </div>
    """, unsafe_allow_html=True)
    # ---------------------------

st.markdown("---")
c1, c2, c3 = st.columns([1, 2, 1])
with c1:
    if st.session_state.idx > 0:
        st.button("Anterior", on_click=lambda: st.session_state.update(idx=st.session_state.idx - 1))
with c3:
    if st.session_state.idx < len(lista_atual) - 1:
        st.button("Próxima", on_click=lambda: st.session_state.update(idx=st.session_state.idx + 1))