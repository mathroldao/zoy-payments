import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="Zoy Finance", layout="wide")

# -----------------------------
# CONECTAR GOOGLE SHEETS
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
# FILTRO POR INFLUENCIADOR
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
# FUNÇÕES
# -----------------------------
def moeda(valor):
    try:
        valor = float(valor)
    except:
        valor = 0
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def atualizar_nf(row_index, numero, valor, arquivo_nome):
    worksheet.update(f"L{row_index}:L{row_index}", [[numero]])
    worksheet.update(f"M{row_index}:M{row_index}", [[valor]])
    worksheet.update(f"N{row_index}:N{row_index}", [[arquivo_nome]])
    worksheet.update(f"O{row_index}:O{row_index}", [[datetime.now().strftime("%d/%m/%Y %H:%M")]])
    worksheet.update(f"E{row_index}:E{row_index}", [["NF Enviada"]])

# -----------------------------
# CÁLCULOS
# -----------------------------
total_recebido = sum(float(p["valor"]) for p in pagamentos if p["status"] == "Pago")

valor_estimado = sum(float(p["valor"]) for p in pagamentos if p["status"] in [
    "Aguardando Nota Fiscal",
    "NF Enviada",
    "NF Reprovada"
])

aguardando_pagamento = sum(float(p["valor"]) for p in pagamentos if p["status"] == "Pagamento Programado")

# -----------------------------
# ESTILO
# -----------------------------
st.markdown("""
<style>
.card {
    padding: 22px;
    border-radius: 16px;
    background-color: #f8f9fc;
    border: 1px solid #e6e6e6;
}
.card-title {
    font-size: 14px;
    color: #777;
}
.card-value {
    font-size: 30px;
    font-weight: bold;
}
.box {
    padding: 22px;
    border-radius: 16px;
    border: 1px solid #e6e6e6;
    margin-bottom: 18px;
}
.small {
    color: #777;
    font-size: 14px;
}
.info-box {
    padding: 16px;
    border-radius: 12px;
    background-color: #faf5ff;
    margin-bottom: 14px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# TELA
# -----------------------------
st.title("Carteira")
st.write(f"Olá, **{influenciador_selecionado}**. Gerencie seus recebíveis, acompanhe seu saldo e envie suas notas fiscais.")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Total Recebido</div>
        <div class="card-value">{moeda(total_recebido)}</div>
        <div class="small">Valor total já pago em sua conta.</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Valor Estimado</div>
        <div class="card-value">{moeda(valor_estimado)}</div>
        <div class="small">Valores ainda sem nota ou pendentes de liberação.</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Aguardando Pagamento</div>
        <div class="card-value">{moeda(aguardando_pagamento)}</div>
        <div class="small">Notas validadas ou pagamentos agendados.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.subheader("Extrato")

if len(pagamentos) == 0:
    st.info("Nenhuma ordem de pagamento encontrada para este influenciador.")

for i, pagamento in enumerate(pagamentos):

    status = pagamento["status"]

    if status == "Aguardando Nota Fiscal":
        badge_color = "#fff7ed"
        badge_text = "Aguardando NF"
        mensagem = "Você precisa emitir e enviar sua nota fiscal."
    elif status == "NF Enviada":
        badge_color = "#eff6ff"
        badge_text = "NF Enviada"
        mensagem = "Sua nota está em análise pelo financeiro."
    elif status == "NF Reprovada":
        badge_color = "#fef2f2"
        badge_text = "NF Reprovada"
        mensagem = "Sua nota foi reprovada. Ajuste e envie novamente."
    elif status == "Pagamento Programado":
        badge_color = "#f0fdf4"
        badge_text = "Pagamento Programado"
        mensagem = "Pagamento já está sendo processado."
    elif status == "Pago":
        badge_color = "#ecfdf5"
        badge_text = "Pago"
        mensagem = "Pagamento já foi realizado."
    else:
        badge_color = "#f3f4f6"
        badge_text = status
        mensagem = ""

    st.markdown(f"""
    <div class="box">
        <span style="background:{badge_color}; padding:6px 10px; border-radius:999px; font-weight:600;">
            {badge_text}
        </span>
        <h3>{moeda(pagamento["valor"])}</h3>
        <p><b>Campanha:</b> {pagamento["campanha"]}</p>
        <p><b>Tomador:</b> {pagamento["tomador"]}</p>
        <p class="small">Criado em {pagamento["data_criacao"]}</p>
        <p style="margin-top:10px; font-weight:500;">{mensagem}</p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(f"Ver dados da NF — {pagamento['campanha']}"):

        st.markdown(f"""
        <div class="info-box">
            <p><b>Razão social:</b> {pagamento["tomador"]}</p>
            <p><b>CNPJ:</b> {pagamento["cnpj"]}</p>
            <p><b>Endereço:</b> {pagamento["endereco"]}</p>
            <p><b>Descrição sugerida da NF:</b> {pagamento["descricao_nf"]}</p>
            <p><b>Valor da NF:</b> {moeda(pagamento["valor"])}</p>
            <p><b>Prazo para envio:</b> {pagamento["prazo_nf"]}</p>
        </div>
        """, unsafe_allow_html=True)

        if pagamento["status"] in ["Aguardando Nota Fiscal", "NF Reprovada"]:

            st.markdown("### Enviar Nota Fiscal")

            numero = st.text_input("Número da NF", key=f"numero_{i}")
            valor_nf = st.text_input("Valor da NF", value=moeda(pagamento["valor"]), key=f"valor_{i}")
            arquivo = st.file_uploader("Upload da NF (PDF)", type=["pdf"], key=f"arquivo_{i}")

            if st.button("Enviar NF", key=f"botao_{i}"):

                if not numero:
                    st.error("Preencha o número da NF antes de enviar.")
                elif not arquivo:
                    st.error("Anexe o PDF da NF antes de enviar.")
                else:
                    linha_real = df_filtrado.index[i] + 2

                    atualizar_nf(
                        linha_real,
                        numero,
                        valor_nf,
                        arquivo.name
                    )

                    st.success("NF enviada com sucesso! O status foi atualizado para NF Enviada.")
                    st.rerun()

        else:
            st.info("Esta ordem de pagamento não está disponível para envio de NF neste momento.")
