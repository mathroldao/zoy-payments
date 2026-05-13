import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import io

st.set_page_config(page_title="Zoy Finance", layout="wide")

SPREADSHEET_ID = "1R6TCMWI-cExcAg431-EOjY0DAP6VNJynFUHJpNcMCGU"
WORKSHEET_NAME = "pagamentos"
DRIVE_FOLDER_ID = "1YIOoOAMcjJq43MdiMjukVtW-AlCIQ8Jm"

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)
drive_service = build("drive", "v3", credentials=creds)

sheet = client.open_by_key(SPREADSHEET_ID)
worksheet = sheet.worksheet(WORKSHEET_NAME)

data = worksheet.get_all_records()
df = pd.DataFrame(data).fillna("")
df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)

def moeda(valor):
    try:
        valor = float(valor)
    except:
        valor = 0
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def upload_pdf_drive(arquivo, campanha, influenciador):
    file_name = f"NF - {influenciador} - {campanha} - {arquivo.name}"

    file_metadata = {
        "name": file_name,
        "parents": [DRIVE_FOLDER_ID]
    }

    media = MediaIoBaseUpload(
        io.BytesIO(arquivo.getvalue()),
        mimetype="application/pdf",
        resumable=False
    )

    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink",
        supportsAllDrives=True
    ).execute()

    return uploaded_file.get("webViewLink")

def atualizar_nf(row_index, numero, valor, link_arquivo):
    worksheet.update(f"L{row_index}:L{row_index}", [[numero]])
    worksheet.update(f"M{row_index}:M{row_index}", [[valor]])
    worksheet.update(f"N{row_index}:N{row_index}", [[link_arquivo]])
    worksheet.update(f"O{row_index}:O{row_index}", [[datetime.now().strftime("%d/%m/%Y %H:%M")]])
    worksheet.update(f"E{row_index}:E{row_index}", [["NF Enviada"]])

def atualizar_status(row_index, novo_status):
    worksheet.update(f"E{row_index}:E{row_index}", [[novo_status]])

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
.login-box {
    max-width: 420px;
    margin: auto;
    padding-top: 80px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# LOGIN
# -----------------------------
if "logado" not in st.session_state:
    st.session_state.logado = False

if "tipo_usuario" not in st.session_state:
    st.session_state.tipo_usuario = ""

if "influenciador_logado" not in st.session_state:
    st.session_state.influenciador_logado = ""

if not st.session_state.logado:

    st.markdown("<div class='login-box'>", unsafe_allow_html=True)

    st.title("Portal Financeiro Zoy")
    st.write("Acesse sua carteira ou painel financeiro.")

    email_digitado = st.text_input("E-mail")
    senha_digitada = st.text_input("Senha", type="password")

    if st.button("Entrar"):

        admin_email = st.secrets["admin"]["email"]
        admin_senha = st.secrets["admin"]["senha"]

        if email_digitado.strip().lower() == admin_email.strip().lower() and senha_digitada.strip() == admin_senha.strip():
            st.session_state.logado = True
            st.session_state.tipo_usuario = "admin"
            st.rerun()

        else:
            usuario = df[
                (df["email"].astype(str).str.strip().str.lower() == email_digitado.strip().lower()) &
                (df["senha"].astype(str).str.strip() == senha_digitada.strip())
            ]

            if len(usuario) > 0:
                st.session_state.logado = True
                st.session_state.tipo_usuario = "influenciador"
                st.session_state.influenciador_logado = usuario.iloc[0]["influenciador"]
                st.rerun()
            else:
                st.error("E-mail ou senha inválidos.")

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.title("Acesso")

    if st.session_state.tipo_usuario == "admin":
        st.write("Logado como:")
        st.write("**Financeiro Zoy**")
    else:
        st.write("Logado como:")
        st.write(f"**{st.session_state.influenciador_logado}**")

    if st.button("Sair"):
        st.session_state.logado = False
        st.session_state.tipo_usuario = ""
        st.session_state.influenciador_logado = ""
        st.rerun()

# -----------------------------
# PAINEL ADMIN
# -----------------------------
if st.session_state.tipo_usuario == "admin":

    st.title("Painel Financeiro Zoy")
    st.write("Acompanhe as ordens de pagamento, notas fiscais enviadas e status de pagamento.")

    total_op = df["valor"].sum()
    total_nf_enviada = df[df["status"] == "NF Enviada"]["valor"].sum()
    total_programado = df[df["status"] == "Pagamento Programado"]["valor"].sum()
    total_pago = df[df["status"] == "Pago"]["valor"].sum()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">Total em OPs</div>
            <div class="card-value">{moeda(total_op)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">NF Enviada</div>
            <div class="card-value">{moeda(total_nf_enviada)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">Pagamento Programado</div>
            <div class="card-value">{moeda(total_programado)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">Pago</div>
            <div class="card-value">{moeda(total_pago)}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    status_filtro = st.selectbox(
        "Filtrar por status",
        ["Todos", "Aguardando Nota Fiscal", "NF Enviada", "NF Reprovada", "Pagamento Programado", "Pago"]
    )

    if status_filtro != "Todos":
        df_admin = df[df["status"] == status_filtro]
    else:
        df_admin = df

    st.subheader("Ordens de Pagamento")

    for index, row in df_admin.iterrows():

        linha_real = index + 2

        st.markdown(f"""
        <div class="box">
            <h3>{moeda(row["valor"])}</h3>
            <p><b>Influenciador:</b> {row["influenciador"]}</p>
            <p><b>Campanha:</b> {row["campanha"]}</p>
            <p><b>Status:</b> {row["status"]}</p>
            <p><b>Número NF:</b> {row.get("numero_nf", "")}</p>
            <p><b>Data envio NF:</b> {row.get("data_envio_nf", "")}</p>
        </div>
        """, unsafe_allow_html=True)

        if row.get("arquivo_nf", ""):
            st.markdown(f"[Abrir NF enviada]({row['arquivo_nf']})")

        col_a, col_b, col_c, col_d = st.columns(4)

        with col_a:
            if st.button("Aprovar NF", key=f"aprovar_{index}"):
                atualizar_status(linha_real, "Pagamento Programado")
                st.success("NF aprovada. Status alterado para Pagamento Programado.")
                st.rerun()

        with col_b:
            if st.button("Reprovar NF", key=f"reprovar_{index}"):
                atualizar_status(linha_real, "NF Reprovada")
                st.warning("NF reprovada. Influenciador poderá reenviar.")
                st.rerun()

        with col_c:
            if st.button("Marcar como Pago", key=f"pago_{index}"):
                atualizar_status(linha_real, "Pago")
                st.success("Pagamento marcado como Pago.")
                st.rerun()

        with col_d:
            if st.button("Voltar para Aguardando NF", key=f"aguardando_{index}"):
                atualizar_status(linha_real, "Aguardando Nota Fiscal")
                st.info("Status alterado para Aguardando Nota Fiscal.")
                st.rerun()

    st.stop()

# -----------------------------
# PORTAL INFLUENCIADOR
# -----------------------------
influenciador_selecionado = st.session_state.influenciador_logado

df_filtrado = df[df["influenciador"] == influenciador_selecionado]
pagamentos = df_filtrado.to_dict(orient="records")

total_recebido = sum(float(p["valor"]) for p in pagamentos if p["status"] == "Pago")

valor_estimado = sum(float(p["valor"]) for p in pagamentos if p["status"] in [
    "Aguardando Nota Fiscal",
    "NF Enviada",
    "NF Reprovada"
])

aguardando_pagamento = sum(float(p["valor"]) for p in pagamentos if p["status"] == "Pagamento Programado")

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

        if status in ["Aguardando Nota Fiscal", "NF Reprovada"]:

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
                    try:
                        linha_real = df_filtrado.index[i] + 2

                        link_arquivo = upload_pdf_drive(
                            arquivo,
                            pagamento["campanha"],
                            influenciador_selecionado
                        )

                        atualizar_nf(
                            linha_real,
                            numero,
                            valor_nf,
                            link_arquivo
                        )

                        st.success("NF enviada com sucesso! O arquivo foi salvo no Drive e o status foi atualizado.")
                        st.rerun()

                    except Exception as e:
                        st.error("Erro ao enviar a NF.")
                        st.write(str(e))

        else:
            st.info("Esta ordem de pagamento não está disponível para envio de NF neste momento.")
