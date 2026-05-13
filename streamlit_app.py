import streamlit as st

st.set_page_config(page_title="Zoy Finance", layout="wide")

# --- DADOS FAKE POR ENQUANTO ---
pagamentos = [
    {
        "valor": 6000,
        "status": "Aguardando Nota Fiscal",
        "tomador": "IEST TECNOLOGIA LTDA",
        "cnpj": "32.008.487/0001-45",
        "campanha": "TCL | Bienal de Arquitetura",
        "data": "20/04/2026"
    },
    {
        "valor": 2500,
        "status": "NF Enviada",
        "tomador": "ZOY COMUNICACAO LTDA",
        "cnpj": "00.000.000/0001-00",
        "campanha": "Sallve | Verão",
        "data": "25/04/2026"
    },
    {
        "valor": 1200,
        "status": "Pagamento Programado",
        "tomador": "CLIENTE EXEMPLO LTDA",
        "cnpj": "11.111.111/0001-11",
        "campanha": "Kibon | Palito Premiado",
        "data": "30/04/2026"
    }
]

def moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

total_recebido = sum(p["valor"] for p in pagamentos if p["status"] == "Pago")
valor_estimado = sum(p["valor"] for p in pagamentos if p["status"] in ["Aguardando Nota Fiscal", "NF Enviada"])
aguardando_pagamento = sum(p["valor"] for p in pagamentos if p["status"] == "Pagamento Programado")

# --- ESTILO ---
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
.badge {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    background-color: #f3e8ff;
    color: #6b21a8;
    font-weight: 600;
    font-size: 13px;
}
.small {
    color: #777;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

st.title("Carteira")
st.write("Gerencie seus recebíveis, acompanhe seu saldo e envie suas notas fiscais.")

# --- RESUMO ---
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

# --- EXTRATO ---
st.subheader("Extrato")

for pagamento in pagamentos:
    st.markdown(f"""
    <div class="box">
        <span class="badge">{pagamento["status"]}</span>
        <h3>{moeda(pagamento["valor"])}</h3>
        <p><b>Tomador:</b> {pagamento["tomador"]} ({pagamento["cnpj"]})</p>
        <p><b>Campanha:</b> {pagamento["campanha"]}</p>
        <p class="small">Criado em {pagamento["data"]}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("### Enviar Nota Fiscal")

campanhas = [p["campanha"] for p in pagamentos if p["status"] == "Aguardando Nota Fiscal"]
campanha_selecionada = st.selectbox("Selecione a campanha", campanhas)

numero = st.text_input("Número da NF")
valor_nf = st.text_input("Valor da NF")
arquivo = st.file_uploader("Upload da NF (PDF)", type=["pdf"])

if st.button("Enviar NF"):
    st.success(f"Nota da campanha {campanha_selecionada} enviada com sucesso!")
