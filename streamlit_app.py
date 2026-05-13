import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="Zoy Finance", layout="wide")

# -----------------------------
# CONECTAR GOOGLE SHEETS (WRITE)
# -----------------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

sheet = client.open_by_key("1R6TCMWI-cExcAg431-EOjY0DAP6VNJynFUHJpNcMCGU")
worksheet = sheet.worksheet("pagamentos")

data = worksheet.get_all_records()
df = pd.DataFrame(data)

df = df.fillna("")
df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)

# -----------------------------
# FILTRO
# -----------------------------
influenciadores = sorted(df["influenciador"].dropna().unique())

st.sidebar.title("Acesso")
influenciador_selecionado = st.sidebar.selectbox(
    "Selecione o influenciador",
    influenciadores
)

df_filtrado = df[df["influenciador"] == influenciador_selecionado]
pagamentos = df_filtrado.to_dict(orient="records")

# -----------------------------
# FUNÇÃO ATUALIZAR PLANILHA
# -----------------------------
def atualizar_nf(row_index, numero, valor, arquivo_nome):

    worksheet.update(f"L{row_index}", numero)
    worksheet.update(f"M{row_index}", valor)
    worksheet.update(f"N{row_index}", arquivo_nome)
    worksheet.update(f"O{row_index}", datetime.now().strftime("%d/%m/%Y %H:%M"))

    worksheet.update(f"E{row_index}", "NF Enviada")

# -----------------------------
# UI
# -----------------------------
st.title("Carteira")
st.write(f"Olá, **{influenciador_selecionado}**.")

for i, pagamento in enumerate(pagamentos):

    st.markdown(f"### {pagamento['campanha']}")
    st.write(f"Valor: R$ {pagamento['valor']}")

    if pagamento["status"] in ["Aguardando Nota Fiscal", "NF Reprovada"]:

        numero = st.text_input("Número da NF", key=f"numero_{i}")
        valor_nf = st.text_input("Valor da NF", key=f"valor_{i}")
        arquivo = st.file_uploader("Arquivo PDF", key=f"arquivo_{i}")

        if st.button("Enviar NF", key=f"btn_{i}"):

            linha_real = df_filtrado.index[i] + 2

            atualizar_nf(
                linha_real,
                numero,
                valor_nf,
                arquivo.name if arquivo else ""
            )

            st.success("NF enviada e atualizada na planilha!")
            st.rerun()
