import streamlit as st

st.set_page_config(page_title="Zoy Finance", layout="wide")

st.title("Carteira")

# --- RESUMO ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Recebido", "R$ 0,00")

with col2:
    st.metric("Valor Estimado", "R$ 6.000,00")

with col3:
    st.metric("Aguardando Pagamento", "R$ 0,00")

st.markdown("---")

# --- EXTRATO ---
st.subheader("Extrato")

with st.container():
    st.markdown("""
    <div style='padding:20px; border-radius:12px; border:1px solid #eee'>
    <h3>R$ 6.000,00</h3>
    <p><b>Status:</b> Aguardando Nota Fiscal</p>
    <p><b>Tomador:</b> IEST TECNOLOGIA LTDA (32.008.487/0001-45)</p>
    <p><b>Campanha:</b> TCL | Bienal de Arquitetura</p>
    <p>Criado em 20/04/2026</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("### Enviar Nota Fiscal")

numero = st.text_input("Número da NF")
valor_nf = st.text_input("Valor da NF")
arquivo = st.file_uploader("Upload da NF (PDF)", type=["pdf"])

if st.button("Enviar NF"):
    st.success("Nota enviada com sucesso!")
