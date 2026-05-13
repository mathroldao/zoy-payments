import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Zoy Finance", layout="wide")

# LINK DA PLANILHA
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSnOO6m8TRBKpN4vMJ8hWwy9Jh7J1m3vOYmy60_XU_WgGoXpMrjxVIr8S2Z50d9BLY_t3wqfdp3S-f5/pub?output=csv"

df = pd.read_csv(url)
df = df.fillna("")
df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)

# FILTRO
influenciadores = sorted(df["influenciador"].dropna().unique())

st.sidebar.title("Acesso")
influenciador_selecionado = st.sidebar.selectbox(
    "Selecione o influenciador",
    influenciadores
)

df_filtrado = df[df["influenciador"] == influenciador_selecionado]
pagamentos = df_filtrado.to_dict(orient="records")

# MOEDA
def moeda(valor):
    try:
        valor = float(valor)
    except:
        valor = 0
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# CÁLCULOS
total_recebido = sum(float(p["valor"]) for p in pagamentos if p["status"] == "Pago")

valor_estimado = sum(float(p["valor"]) for p in pagamentos if p["status"] in [
    "Aguardando Nota Fiscal",
    "NF Enviada",
    "NF Reprovada"
])

aguardando_pagamento = sum(float(p["valor"]) for p in pagamentos if p["status"] == "Pagamento Programado")

# ESTILO
st.markdown("""
<style>
.card { padding: 22px; border-radius: 16px; background-color: #f8f9fc; border: 1px solid #e6e6e6; }
.card-title { font-size: 14px; color: #777; }
.card-value { font-size: 30px; font-weight: bold; }
.box { padding: 22px; border-radius: 16px; border: 1px solid #e6e6e6; margin-bottom: 18px; }
.small { color: #777; font-size: 14px; }
.info-box { padding: 16px; border-radius: 12px; background-color: #faf5ff; margin-bottom: 14px; }
</style>
""", unsafe_allow_html=True)

# TÍTULO
st.title("Carteira")
st.write(f"Olá, **{influenciador_selecionado}**.")

# CARDS
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"<div class='card'><div class='card-title'>Total Recebido</div><div class='card-value'>{moeda(total_recebido)}</div></div>", unsafe_allow_html=True)

with col2:
    st.markdown(f"<div class='card'><div class='card-title'>Valor Estimado</div><div class='card-value'>{moeda(valor_estimado)}</div></div>", unsafe_allow_html=True)

with col3:
    st.markdown(f"<div class='card'><div class='card-title'>Aguardando Pagamento</div><div class='card-value'>{moeda(aguardando_pagamento)}</div></div>", unsafe_allow_html=True)

st.markdown("---")
st.subheader("Extrato")

for i, pagamento in enumerate(pagamentos):

    st.markdown(f"""
    <div class="box">
        <h3>{moeda(pagamento["valor"])}</h3>
        <p><b>Campanha:</b> {pagamento["campanha"]}</p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Ver dados da NF"):

        if pagamento["status"] in ["Aguardando Nota Fiscal", "NF Reprovada"]:

            numero = st.text_input("Número da NF", key=f"numero_{i}")
            valor_nf = st.text_input("Valor da NF", value=moeda(pagamento["valor"]), key=f"valor_{i}")
            arquivo = st.file_uploader("Upload da NF (PDF)", type=["pdf"], key=f"arquivo_{i}")

            if st.button("Enviar NF", key=f"botao_{i}"):

                assunto = f"Envio de NF - {pagamento['campanha']}"
                
                corpo = f"""
Olá,

Segue minha nota fiscal referente à campanha:

Influenciador: {influenciador_selecionado}
Campanha: {pagamento['campanha']}
Valor: {moeda(pagamento['valor'])}
Número da NF: {numero}

Obrigado.
"""

                mailto_link = f"mailto:financeiro@zoy.com?subject={urllib.parse.quote(assunto)}&body={urllib.parse.quote(corpo)}"

                st.markdown(f"[📧 Clique aqui para enviar o e-mail]({mailto_link})")

        else:
            st.info("NF já enviada ou não disponível.")
