import streamlit as st

st.set_page_config(page_title="Zoy Finance", layout="wide")

st.title("Carteira")

# --- RESUMO ---
col1, col2, col3 = st.columns(3)

col1.metric("Total Recebido", "R$ 0,00")
col2.metric("Valor Estimado", "R$ 6.000,00")
col3.metric("Aguardando Pagamento", "R$ 0,00")

st.markdown("---")

# --- EXTRATO ---
st.subheader("Extrato")

op = {
    "valor": "R$ 6.000,00",
    "status": "Aguardando Nota Fiscal",
    "tomador": "IEST TECNOLOGIA LTDA",
    "cnpj": "32.008.487/0001-45",
    "campanha": "TCL | Bienal de Arquitetura",
    "data": "20/04/2026"
}

with st.container():
    st.markdown(f"### {op['valor']}")
    st.write(f"**Status:** {op['status']}")
    st.write(f"**Tomador:** {op['tomador']} ({op['cnpj']})")
    st.write(f"**Campanha:** {op['campanha']}")
    st.write(f"Criado em {op['data']}")

    st.markdown("### Enviar Nota Fiscal")

    numero = st.text_input("Número da NF")
    valor_nf = st.text_input("Valor da NF")
    arquivo = st.file_uploader("Upload da NF (PDF)", type=["pdf"])

    if st.button("Enviar NF"):
        st.success("Nota enviada com sucesso!")
