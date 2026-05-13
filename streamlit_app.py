import streamlit as st

st.set_page_config(page_title="Zoy Finance", layout="wide")

# --- ESTILO ---
st.markdown("""
<style>
.card {
    padding: 20px;
    border-radius: 12px;
    background-color: #f8f9fc;
    border: 1px solid #e6e6e6;
}
.card-title {
    font-size: 14px;
    color: #777;
}
.card-value {
    font-size: 28px;
    font-weight: bold;
}
.box {
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #e6e6e6;
}
</style>
""", unsafe_allow_html=True)

st.title("Carteira")

# --- RESUMO ---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="card">
        <div class="card-title">Total Recebido</div>
        <div class="card-value">R$ 0,00</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card">
        <div class="card-title">Valor Estimado</div>
        <div class="card-value">R$ 6.000,00</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="card">
        <div class="card-title">Aguardando Pagamento</div>
        <div class="card-value">R$ 0,00</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- EXTRATO ---
st.subheader("Extrato")

st.markdown("""
<div class="box">
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
