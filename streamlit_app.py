import streamlit as st
import pandas as pd
import gspread
import resend
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import io
import os

st.set_page_config(page_title="Zoy Finance", layout="wide")

SPREADSHEET_ID = "1R6TCMWI-cExcAg431-EOjY0DAP6VNJynFUHJpNcMCGU"
WORKSHEET_NAME = "pagamentos"
DRIVE_FOLDER_ID = "1YIOoOAMcjJq43MdiMjukVtW-AlCIQ8Jm"
PORTAL_URL = "https://zoy-payments.streamlit.app"

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

if len(df) > 0:
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)

resend.api_key = st.secrets["resend"]["api_key"]
FROM_EMAIL = st.secrets["resend"]["from_email"]


def moeda(valor):
    try:
        valor = float(valor)
    except:
        valor = 0
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def status_config(status):
    config = {
        "Aguardando Nota Fiscal": ("Aguardando NF", "#FFF7ED", "#C2410C", "Você precisa emitir e enviar sua nota fiscal."),
        "NF Enviada": ("NF Enviada", "#EFF6FF", "#1D4ED8", "Sua nota está em análise pelo financeiro."),
        "NF Reprovada": ("NF Reprovada", "#FEF2F2", "#B91C1C", "Sua nota foi reprovada. Ajuste e envie novamente."),
        "Pagamento Programado": ("Pagamento Programado", "#F5F3FF", "#6D28D9", "Pagamento já está sendo processado."),
        "Pago": ("Pago", "#ECFDF5", "#047857", "Pagamento já foi realizado.")
    }
    return config.get(status, (status, "#F3F4F6", "#374151", ""))


def enviar_email_nova_op(destinatario, influenciador, campanha, valor, prazo_nf, data_pagamento, email_acesso, senha_acesso, novo_influenciador):
    if novo_influenciador:
        assunto = "Seu acesso ao Portal Financeiro Zoy foi criado"
        html = f"""
        <p>Olá, {influenciador}.</p>
        <p>Seu acesso ao Portal Financeiro Zoy foi criado e você possui uma nova ordem de pagamento disponível para emissão de nota fiscal.</p>
        <p>
            <b>Campanha:</b> {campanha}<br>
            <b>Valor:</b> {moeda(valor)}<br>
            <b>Prazo para envio da NF:</b> {prazo_nf}<br>
            <b>Data prevista de pagamento:</b> {data_pagamento}
        </p>
        <p>
            <b>Dados de acesso:</b><br>
            E-mail: {email_acesso}<br>
            Senha: {senha_acesso}
        </p>
        <p>Acesse o portal:<br><a href="{PORTAL_URL}">{PORTAL_URL}</a></p>
        <p>Atenciosamente,<br>Equipe Zoy</p>
        """
    else:
        assunto = "Nova ordem de pagamento disponível no Portal Financeiro Zoy"
        html = f"""
        <p>Olá, {influenciador}.</p>
        <p>Você possui uma nova ordem de pagamento disponível no Portal Financeiro Zoy para emissão de nota fiscal.</p>
        <p>
            <b>Campanha:</b> {campanha}<br>
            <b>Valor:</b> {moeda(valor)}<br>
            <b>Prazo para envio da NF:</b> {prazo_nf}<br>
            <b>Data prevista de pagamento:</b> {data_pagamento}
        </p>
        <p>Acesse o portal:<br><a href="{PORTAL_URL}">{PORTAL_URL}</a></p>
        <p>Atenciosamente,<br>Equipe Zoy</p>
        """

    resend.Emails.send({
        "from": FROM_EMAIL,
        "to": [destinatario],
        "subject": assunto,
        "html": html,
    })


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


def editar_op(row_index, dados):
    worksheet.update(f"B{row_index}:D{row_index}", [[
        dados["influenciador"],
        dados["campanha"],
        dados["valor"]
    ]])

    worksheet.update(f"F{row_index}:K{row_index}", [[
        dados["tomador"],
        dados["cnpj"],
        dados["endereco"],
        dados["descricao_nf"],
        dados["data_criacao"],
        dados["prazo_nf"]
    ]])

    worksheet.update(f"P{row_index}:R{row_index}", [[
        dados["data_pagamento"],
        dados["email"],
        dados["senha"]
    ]])


def excluir_op(row_index):
    worksheet.delete_rows(row_index)


def criar_op(nova_linha):
    worksheet.append_row(nova_linha, value_input_option="USER_ENTERED")


def proximo_id():
    if len(df) == 0:
        return 1
    try:
        return int(pd.to_numeric(df["id"], errors="coerce").max()) + 1
    except:
        return len(df) + 1


def mostrar_logo(width=110):
    if os.path.exists("zoy_logo.png"):
        st.image("zoy_logo.png", width=width)
    else:
        st.markdown("<div class='logo-text'>ZOY</div>", unsafe_allow_html=True)


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #F7F7FA;
}

.block-container {
    padding-top: 2.5rem;
    padding-bottom: 4rem;
    max-width: 1240px;
}

.logo-text {
    font-size: 34px;
    font-weight: 900;
    letter-spacing: -2px;
    color: #111111;
    margin-bottom: 8px;
}

.hero-title {
    font-size: 42px;
    font-weight: 800;
    letter-spacing: -1.5px;
    color: #111111;
    margin-bottom: 4px;
}

.hero-subtitle {
    font-size: 16px;
    color: #6B7280;
    margin-bottom: 28px;
}

.card {
    padding: 24px;
    border-radius: 22px;
    background: #FFFFFF;
    border: 1px solid #ECECF1;
    box-shadow: 0 10px 30px rgba(17, 17, 17, 0.04);
}

.card-title {
    font-size: 13px;
    color: #6B7280;
    font-weight: 600;
    margin-bottom: 10px;
}

.card-value {
    font-size: 30px;
    font-weight: 800;
    letter-spacing: -1px;
    color: #111111;
}

.card-caption {
    font-size: 13px;
    color: #9CA3AF;
    margin-top: 10px;
}

.op-card {
    padding: 24px;
    border-radius: 24px;
    background: #FFFFFF;
    border: 1px solid #ECECF1;
    box-shadow: 0 12px 35px rgba(17, 17, 17, 0.045);
    margin-bottom: 18px;
}

.op-value {
    font-size: 28px;
    font-weight: 800;
    color: #111111;
    margin-top: 14px;
    margin-bottom: 12px;
}

.op-line {
    color: #374151;
    font-size: 14px;
    margin: 6px 0;
}

.small {
    color: #8B8B96;
    font-size: 13px;
}

.info-box {
    padding: 18px;
    border-radius: 18px;
    background: #FAF7FF;
    border: 1px solid #EDE5FF;
    margin-bottom: 14px;
}

.login-shell {
    min-height: 78vh;
    display: flex;
    align-items: center;
    justify-content: center;
}

.login-card {
    width: 100%;
    max-width: 460px;
    background: #FFFFFF;
    border: 1px solid #ECECF1;
    border-radius: 28px;
    padding: 38px;
    box-shadow: 0 24px 70px rgba(17, 17, 17, 0.08);
}

.login-title {
    font-size: 30px;
    font-weight: 800;
    letter-spacing: -1px;
    color: #111111;
    margin-top: 18px;
    margin-bottom: 8px;
}

.login-subtitle {
    color: #6B7280;
    font-size: 15px;
    margin-bottom: 22px;
}

.section-title {
    font-size: 26px;
    font-weight: 800;
    color: #111111;
    letter-spacing: -0.7px;
    margin-top: 24px;
    margin-bottom: 14px;
}

.badge {
    display: inline-block;
    padding: 7px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
}

hr {
    margin: 30px 0 !important;
}

.stButton > button {
    border-radius: 14px;
    border: 1px solid #111111;
    background: #111111;
    color: #FFFFFF;
    font-weight: 700;
    padding: 0.65rem 1rem;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background: #7C3AED;
    border-color: #7C3AED;
    color: #FFFFFF;
}

[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #ECECF1;
}

input, textarea {
    border-radius: 14px !important;
}

div[data-testid="stExpander"] {
    border: 1px solid #ECECF1;
    border-radius: 18px;
    background: #FFFFFF;
    box-shadow: 0 8px 25px rgba(17, 17, 17, 0.025);
}
</style>
""", unsafe_allow_html=True)


if "logado" not in st.session_state:
    st.session_state.logado = False

if "tipo_usuario" not in st.session_state:
    st.session_state.tipo_usuario = ""

if "influenciador_logado" not in st.session_state:
    st.session_state.influenciador_logado = ""


if not st.session_state.logado:
    st.markdown("<div class='login-shell'><div class='login-card'>", unsafe_allow_html=True)
    mostrar_logo(115)

    st.markdown("""
        <div class="login-title">Portal Financeiro</div>
        <div class="login-subtitle">Acesse sua carteira, ordens de pagamento e notas fiscais em um só lugar.</div>
    """, unsafe_allow_html=True)

    email_digitado = st.text_input("E-mail")
    senha_digitada = st.text_input("Senha", type="password")

  if st.button("Entrar", use_container_width=True):
    admins = st.secrets["admins"]

    admin_encontrado = False

    for admin in admins:
        if (
            email_digitado.strip().lower() == admin["email"].strip().lower()
            and senha_digitada.strip() == admin["senha"].strip()
        ):
            admin_encontrado = True
            break

    if admin_encontrado:
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
    st.markdown("</div></div>", unsafe_allow_html=True)
    st.stop()


with st.sidebar:
    mostrar_logo(92)
    st.markdown("---")

    if st.session_state.tipo_usuario == "admin":
        st.markdown("**Financeiro Zoy**")
        st.caption("Painel administrativo")
    else:
        st.markdown(f"**{st.session_state.influenciador_logado}**")
        st.caption("Carteira do influenciador")

    st.markdown("---")

    if st.button("Sair", use_container_width=True):
        st.session_state.logado = False
        st.session_state.tipo_usuario = ""
        st.session_state.influenciador_logado = ""
        st.rerun()


if st.session_state.tipo_usuario == "admin":
    st.markdown('<div class="hero-title">Painel Financeiro Zoy</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Crie, edite, exclua e acompanhe ordens de pagamento, notas fiscais e status financeiros.</div>', unsafe_allow_html=True)

    with st.expander("+ Nova Ordem de Pagamento", expanded=False):
        tipo_influenciador = st.radio(
            "Influenciador",
            ["Selecionar existente", "Cadastrar novo influenciador"],
            horizontal=True
        )

        influenciadores_existentes = sorted(df["influenciador"].dropna().unique()) if len(df) > 0 else []

        if tipo_influenciador == "Selecionar existente":
            influenciador_op = st.selectbox("Selecione o influenciador", influenciadores_existentes)
            dados_usuario = df[df["influenciador"] == influenciador_op].head(1)

            if len(dados_usuario) > 0:
                email_op = dados_usuario.iloc[0]["email"]
                senha_op = dados_usuario.iloc[0]["senha"]
            else:
                email_op = ""
                senha_op = ""
        else:
            influenciador_op = st.text_input("Nome/@ do influenciador")
            email_op = st.text_input("E-mail de acesso")
            senha_op = st.text_input("Senha de acesso")

        st.markdown("### Dados da campanha")
        campanha_op = st.text_input("Campanha")
        valor_op = st.number_input("Valor da OP", min_value=0.0, step=100.0)
        prazo_nf_op = st.text_input("Prazo para envio da NF", placeholder="Ex: 30/05/2026")
        data_pagamento_op = st.text_input("Data prevista de pagamento", placeholder="Ex: 30/06/2026")

        st.markdown("### Dados para emissão da NF")
        tomador_op = st.text_input("Tomador / Razão Social")
        cnpj_op = st.text_input("CNPJ")
        endereco_op = st.text_input("Endereço")
        descricao_nf_op = st.text_area(
            "Descrição sugerida da NF",
            value="Serviço de divulgação publicitária em campanha de marketing de influência."
        )

        if st.button("Criar OP", use_container_width=True):
            if not influenciador_op or not campanha_op or valor_op <= 0 or not tomador_op or not cnpj_op:
                st.error("Preencha os campos obrigatórios: influenciador, campanha, valor, tomador e CNPJ.")
            elif tipo_influenciador == "Cadastrar novo influenciador" and (not email_op or not senha_op):
                st.error("Para novo influenciador, preencha e-mail e senha.")
            elif not email_op:
                st.error("Este influenciador não possui e-mail cadastrado.")
            else:
                nova_linha = [
                    proximo_id(),
                    influenciador_op,
                    campanha_op,
                    valor_op,
                    "Aguardando Nota Fiscal",
                    tomador_op,
                    cnpj_op,
                    endereco_op,
                    descricao_nf_op,
                    datetime.now().strftime("%d/%m/%Y"),
                    prazo_nf_op,
                    "",
                    "",
                    "",
                    "",
                    data_pagamento_op,
                    email_op,
                    senha_op
                ]

                criar_op(nova_linha)

                try:
                    enviar_email_nova_op(
                        destinatario=email_op,
                        influenciador=influenciador_op,
                        campanha=campanha_op,
                        valor=valor_op,
                        prazo_nf=prazo_nf_op,
                        data_pagamento=data_pagamento_op,
                        email_acesso=email_op,
                        senha_acesso=senha_op,
                        novo_influenciador=(tipo_influenciador == "Cadastrar novo influenciador")
                    )
                    st.success("OP criada com sucesso! O influenciador foi notificado por e-mail.")
                except Exception as e:
                    st.warning("OP criada com sucesso, mas o e-mail não foi enviado.")
                    st.write(str(e))

                st.rerun()

    st.markdown("---")

    total_op = df["valor"].sum()
    total_nf_enviada = df[df["status"] == "NF Enviada"]["valor"].sum()
    total_programado = df[df["status"] == "Pagamento Programado"]["valor"].sum()
    total_pago = df[df["status"] == "Pago"]["valor"].sum()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"<div class='card'><div class='card-title'>Total em OPs</div><div class='card-value'>{moeda(total_op)}</div><div class='card-caption'>Base total lançada</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card'><div class='card-title'>NF Enviada</div><div class='card-value'>{moeda(total_nf_enviada)}</div><div class='card-caption'>Aguardando análise</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='card'><div class='card-title'>Pagamento Programado</div><div class='card-value'>{moeda(total_programado)}</div><div class='card-caption'>Em processamento</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='card'><div class='card-title'>Pago</div><div class='card-value'>{moeda(total_pago)}</div><div class='card-caption'>Concluído</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    col_filtro1, col_filtro2 = st.columns([1, 2])

    with col_filtro1:
        status_filtro = st.selectbox(
            "Filtrar por status",
            ["Todos", "Aguardando Nota Fiscal", "NF Enviada", "NF Reprovada", "Pagamento Programado", "Pago"]
        )

    with col_filtro2:
        busca = st.text_input("Buscar por influenciador ou campanha")

    if status_filtro != "Todos":
        df_admin = df[df["status"] == status_filtro]
    else:
        df_admin = df.copy()

    if busca:
        busca_lower = busca.lower()
        df_admin = df_admin[
            df_admin["influenciador"].astype(str).str.lower().str.contains(busca_lower, na=False) |
            df_admin["campanha"].astype(str).str.lower().str.contains(busca_lower, na=False)
        ]

    st.markdown('<div class="section-title">Ordens de Pagamento</div>', unsafe_allow_html=True)

    for index, row in df_admin.iterrows():
        linha_real = index + 2
        badge_text, badge_bg, badge_color, _ = status_config(row["status"])

        valor_formatado = moeda(row["valor"])
        influenciador = row["influenciador"]
        campanha = row["campanha"]
        data_pagamento = row.get("data_pagamento", "")
        numero_nf = row.get("numero_nf", "")
        data_envio_nf = row.get("data_envio_nf", "")

        admin_card_html = f"""
        <div class="op-card">
            <span class="badge" style="background:{badge_bg}; color:{badge_color};">{badge_text}</span>
            <div class="op-value">{valor_formatado}</div>
            <div class="op-line"><b>Influenciador:</b> {influenciador}</div>
            <div class="op-line"><b>Campanha:</b> {campanha}</div>
            <div class="op-line"><b>Pagamento previsto:</b> {data_pagamento}</div>
            <div class="op-line"><b>Número NF:</b> {numero_nf}</div>
            <div class="small">Data envio NF: {data_envio_nf}</div>
        </div>
        """

        st.markdown(admin_card_html, unsafe_allow_html=True)

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

        with st.expander(f"Editar OP — {row['campanha']}"):
            edit_influ = st.text_input("Influenciador", value=str(row["influenciador"]), key=f"edit_influ_{index}")
            edit_campanha = st.text_input("Campanha", value=str(row["campanha"]), key=f"edit_campanha_{index}")
            edit_valor = st.number_input("Valor", value=float(row["valor"]), min_value=0.0, step=100.0, key=f"edit_valor_{index}")
            edit_tomador = st.text_input("Tomador", value=str(row["tomador"]), key=f"edit_tomador_{index}")
            edit_cnpj = st.text_input("CNPJ", value=str(row["cnpj"]), key=f"edit_cnpj_{index}")
            edit_endereco = st.text_input("Endereço", value=str(row["endereco"]), key=f"edit_endereco_{index}")
            edit_descricao = st.text_area("Descrição NF", value=str(row["descricao_nf"]), key=f"edit_desc_{index}")
            edit_data = st.text_input("Data de criação", value=str(row["data_criacao"]), key=f"edit_data_{index}")
            edit_prazo = st.text_input("Prazo NF", value=str(row["prazo_nf"]), key=f"edit_prazo_{index}")
            edit_data_pagamento = st.text_input("Data prevista de pagamento", value=str(row.get("data_pagamento", "")), key=f"edit_data_pagamento_{index}")
            edit_email = st.text_input("E-mail", value=str(row["email"]), key=f"edit_email_{index}")
            edit_senha = st.text_input("Senha", value=str(row["senha"]), key=f"edit_senha_{index}")

            if st.button("Salvar alterações", key=f"salvar_edit_{index}"):
                editar_op(linha_real, {
                    "influenciador": edit_influ,
                    "campanha": edit_campanha,
                    "valor": edit_valor,
                    "tomador": edit_tomador,
                    "cnpj": edit_cnpj,
                    "endereco": edit_endereco,
                    "descricao_nf": edit_descricao,
                    "data_criacao": edit_data,
                    "prazo_nf": edit_prazo,
                    "data_pagamento": edit_data_pagamento,
                    "email": edit_email,
                    "senha": edit_senha
                })
                st.success("OP editada com sucesso.")
                st.rerun()

        with st.expander(f"Excluir OP — {row['campanha']}"):
            st.warning("Atenção: essa ação apaga a OP da planilha e não pode ser desfeita.")
            confirmar = st.checkbox("Confirmo que desejo excluir esta OP", key=f"confirmar_excluir_{index}")

            if st.button("Excluir definitivamente", key=f"excluir_{index}"):
                if confirmar:
                    excluir_op(linha_real)
                    st.success("OP excluída com sucesso.")
                    st.rerun()
                else:
                    st.error("Marque a confirmação antes de excluir.")

    st.stop()


influenciador_selecionado = st.session_state.influenciador_logado

df_filtrado = df[df["influenciador"] == influenciador_selecionado]
pagamentos = df_filtrado.to_dict(orient="records")

total_recebido = sum(float(p["valor"]) for p in pagamentos if p["status"] == "Pago")
valor_estimado = sum(float(p["valor"]) for p in pagamentos if p["status"] in ["Aguardando Nota Fiscal", "NF Enviada", "NF Reprovada"])
aguardando_pagamento = sum(float(p["valor"]) for p in pagamentos if p["status"] == "Pagamento Programado")

st.markdown('<div class="hero-title">Carteira</div>', unsafe_allow_html=True)
st.markdown(f'<div class="hero-subtitle">Olá, <b>{influenciador_selecionado}</b>. Gerencie seus recebíveis, acompanhe seu saldo e envie suas notas fiscais.</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"<div class='card'><div class='card-title'>Total Recebido</div><div class='card-value'>{moeda(total_recebido)}</div><div class='card-caption'>Valor total já pago em sua conta.</div></div>", unsafe_allow_html=True)

with col2:
    st.markdown(f"<div class='card'><div class='card-title'>Valor Estimado</div><div class='card-value'>{moeda(valor_estimado)}</div><div class='card-caption'>Valores ainda sem nota ou pendentes de liberação.</div></div>", unsafe_allow_html=True)

with col3:
    st.markdown(f"<div class='card'><div class='card-title'>Aguardando Pagamento</div><div class='card-value'>{moeda(aguardando_pagamento)}</div><div class='card-caption'>Notas validadas ou pagamentos agendados.</div></div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div class="section-title">Extrato</div>', unsafe_allow_html=True)

if len(pagamentos) == 0:
    st.info("Nenhuma ordem de pagamento encontrada para este influenciador.")

for i, pagamento in enumerate(pagamentos):
    badge_text, badge_bg, badge_color, mensagem = status_config(pagamento["status"])

    texto_pagamento = ""
    data_pagamento = pagamento.get("data_pagamento", "")

    if data_pagamento:
        if pagamento["status"] == "Pago":
            texto_pagamento = f"<div class='op-line'><b>Pagamento realizado em:</b> {data_pagamento}</div>"
        else:
            texto_pagamento = f"<div class='op-line'><b>Pagamento previsto:</b> {data_pagamento}</div>"

    valor_formatado = moeda(pagamento["valor"])
    campanha = pagamento["campanha"]
    tomador = pagamento["tomador"]
    data_criacao = pagamento["data_criacao"]

    card_html = f"""
    <div class="op-card">
        <span class="badge" style="background:{badge_bg}; color:{badge_color};">{badge_text}</span>
        <div class="op-value">{valor_formatado}</div>
        <div class="op-line"><b>Campanha:</b> {campanha}</div>
        <div class="op-line"><b>Tomador:</b> {tomador}</div>
        {texto_pagamento}
        <div class="small">Criado em {data_criacao}</div>
        <div class="op-line" style="margin-top:12px;"><b>{mensagem}</b></div>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)

    with st.expander(f"Ver dados da NF — {pagamento['campanha']}"):
        st.markdown(f"""
        <div class="info-box">
            <p><b>Razão social:</b> {pagamento["tomador"]}</p>
            <p><b>CNPJ:</b> {pagamento["cnpj"]}</p>
            <p><b>Endereço:</b> {pagamento["endereco"]}</p>
            <p><b>Descrição sugerida da NF:</b> {pagamento["descricao_nf"]}</p>
            <p><b>Valor da NF:</b> {moeda(pagamento["valor"])}</p>
            <p><b>Prazo para envio:</b> {pagamento["prazo_nf"]}</p>
            <p><b>Data prevista de pagamento:</b> {pagamento.get("data_pagamento", "")}</p>
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
