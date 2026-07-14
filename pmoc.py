import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
from fpdf import FPDF
import json

# Configuração da página do Streamlit
st.set_page_config(page_title="PMOC - Controle de Splits", layout="wide")
st.title("🔧 Sistema PMOC - Cadastro e Manutenção de Splits")

# 1. CONEXÃO COM O GOOGLE SHEETS via Streamlit Secrets
@st.cache_resource
def conectar_google_sheets():
    # Carrega o JSON de credenciais guardado nas Secrets do Streamlit
    creds_dict = json.loads(st.secrets["g_sheets_credentials"])
    scope = [
        "https://googleapis.com",
        "https://googleapis.com"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    
    # Abre a planilha pelo ID fornecido nas Secrets
    sheet = client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
    return sheet

try:
    sheet = conectar_google_sheets()
except Exception as e:
    st.error(f"Erro ao conectar ao Google Sheets. Verifique as credenciais. Erro: {e}")
    st.stop()

# Função auxiliar para ler dados da planilha
def carregar_dados():
    records = sheet.get_all_records()
    if not records:
        return pd.DataFrame(columns=[
            "TAG", "Local", "Setor", "Marca", "Modelo", "BTU", 
            "Data Manutenção", "Técnico Executante", "Aprovação Supervisor", 
            "Próxima manutenção", "Observações"
        ])
    return pd.DataFrame(records)

df = carregar_dados()

# 2. ABAS DA INTERFACE
aba_cadastro, aba_manutencao, aba_relatorio = st.tabs([
    "🆕 Cadastrar Novo Aparelho", 
    "🛠️ Registrar Manutenção", 
    "📄 Gerar Relatório PDF"
])

# ==========================================
# ABA 1: CADASTRO DE NOVO APARELHO
# ==========================================
with aba_cadastro:
    st.header("Cadastrar Novo Ar-Condicionado Split")
    
    # Define a próxima TAG sequencial automaticamente
    if not df.empty:
        proxima_tag = int(df["TAG"].max()) + 1
    else:
        proxima_tag = 1
        
    st.info(f"O próximo aparelho será registrado com a **TAG: {proxima_tag}**")
    
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            local = st.text_input("Local (ex: Bloco A)")
            setor = st.text_input("Setor (ex: Diretoria)")
            marca = st.text_input("Marca")
        with col2:
            modelo = st.text_input("Modelo / Número de Série")
            btu = st.selectbox("Capacidade (BTUs)", ["9000", "12000", "18000", "24000", "30000", "36000", "60000"])
            obs = st.text_area("Observações Iniciais", value="-")
            
        botao_cadastrar = st.form_submit_button("Salvar no Banco de Dados")
        
        if botao_cadastrar:
            if local and setor and marca:
                # Novo cadastro inicia sem manutenção realizada
                nova_linha = [
                    proxima_tag, local, setor, marca, modelo, btu,
                    "-", "-", "-", "-", obs
                ]
                sheet.append_row(nova_linha)
                st.success(f"Aparelho TAG {proxima_tag} cadastrado com sucesso!")
                st.rerun()
            else:
                st.warning("Por favor, preencha os campos obrigatórios (Local, Setor e Marca).")

# ==========================================
# ABA 2: REGISTRAR MANUTENÇÃO (REGRA 180 DIAS)
# ==========================================
with aba_manutencao:
    st.header("Atualizar Histórico de Manutenção")
    
    if df.empty:
        st.info("Nenhum aparelho cadastrado ainda.")
    else:
        # Seleção do aparelho por TAG
        lista_tags = df["TAG"].tolist()
        tag_selecionada = st.selectbox("Selecione a TAG do aparelho que recebeu manutenção:", lista_tags)
        
        # Puxa os dados atuais do aparelho escolhido
        dados_aparelho = df[df["TAG"] == tag_selecionada].iloc[0]
        st.write(f"**Aparelho:** {dados_aparelho['Marca']} {dados_aparelho['BTU']} BTU | **Local:** {dados_aparelho['Local']} - {dados_aparelho['Setor']}")
        
        with st.form("form_manutencao"):
            col1, col2 = st.columns(2)
            with col1:
                data_manut = st.date_input("Data da Manutenção Atual", datetime.today())
                tecnico = st.text_input("Nome do Técnico Executante")
            with col2:
                supervisor = st.text_input("Nome do Supervisor (Aprovação)")
                novas_obs = st.text_area("Observações da Manutenção", value=str(dados_aparelho['Observações']))
                
            botao_atualizar = st.form_submit_button("Gravar Manutenção")
            
            if botao_atualizar:
                if tecnico and supervisor:
                    # Cálculo automático da próxima manutenção (+180 dias)
                    data_proxima = data_manut + timedelta(days=180)
                    
                    data_manut_str = data_manut.strftime("%d/%m/%Y")
                    data_proxima_str = data_proxima.strftime("%d/%m/%Y")
                    
                    # Localiza a linha correta no Google Sheets (gspread usa índice 1 e o cabeçalho é a linha 1)
                    idx_linha = df[df["TAG"] == tag_selecionada].index[0] + 2
                    
                    # Atualiza os campos específicos da manutenção na planilha
                    sheet.update_cell(idx_linha, 7, data_manut_str)     # Data Manutenção
                    sheet.update_cell(idx_linha, 8, tecnico)            # Técnico
                    sheet.update_cell(idx_linha, 9, supervisor)         # Supervisor
                    sheet.update_cell(idx_linha, 10, data_proxima_str)  # Próxima manutenção
                    sheet.update_cell(idx_linha, 11, novas_obs)         # Observações
                    
                    st.success(f"Manutenção registrada! Próxima revisão agendada para: {data_proxima_str}")
                    st.rerun()
                else:
                    st.warning("Preencha o nome do técnico e do supervisor para validar a manutenção.")

# ==========================================
# ABA 3: EMISSÃO DE RELATÓRIO PDF PARA AUDITORIA
# ==========================================
with aba_relatorio:
    st.header("Gerar Relatório de Auditoria PMOC")
    
    if df.empty:
        st.info("Sem dados disponíveis.")
    else:
        st.dataframe(df, use_container_width=True)
        
        # Filtro opcional para o PDF
        opcao_pdf = st.radio("Escolha o escopo do PDF:", ["Apenas uma TAG específica", "Todos os aparelhos"])
        
        aparelhos_relatorio = []
        if opcao_pdf == "Apenas uma TAG específica":
            tag_pdf = st.selectbox("Selecione a TAG para o relatório:", df["TAG"].tolist(), key="pdf_tag")
            aparelhos_relatorio = df[df["TAG"] == tag_pdf].to_dict(orient="records")
        else:
            aparelhos_relatorio = df.to_dict(orient="records")
            
        if st.button("Gerar e Baixar PDF"):
            # Criação do PDF com FPDF2
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            
            # Cabeçalho do Relatório
            pdf.cell(0, 10, "PLANO DE MANUTENÇÃO, OPERAÇÃO E CONTROLE (PMOC)", ln=True, align="C")
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 8, f"Gerado em: {datetime.today().strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")
            pdf.ln(10)
            
            # Dados dos Aparelhos
            for ap in aparelhos_relatorio:
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(0, 8, f"Equipamento TAG: {ap['TAG']}", ln=True, fill=False)
                pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
                pdf.set_font("Helvetica", "", 10)
                
                pdf.cell(95, 7, f"Local: {ap['Local']}", ln=False)
                pdf.cell(95, 7, f"Setor: {ap['Setor']}", ln=True)
                pdf.cell(95, 7, f"Marca/Modelo: {ap['Marca']} / {ap['Modelo']}", ln=False)
                pdf.cell(95, 7, f"Capacidade: {ap['BTU']} BTUs", ln=True)
                pdf.cell(95, 7, f"Última Manutenção: {ap['Data Manutenção']}", ln=False)
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(95, 7, f"PRÓXIMA MANUTENÇÃO: {ap['Próxima manutenção']}", ln=True)
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 7, f"Obs: {ap['Observações']}", ln=True)
                pdf.ln(5)
                
                # Campos de Assinatura para cada/último aparelho mostrado
                pdf.ln(10)
                pdf.cell(95, 5, "_________________________________________", ln=False, align="C")
                pdf.cell(95, 5, "_________________________________________", ln=True, align="C")
                pdf.cell(95, 5, f"Técnico Executante: {ap['Técnico Executante']}", ln=False, align="C")
                pdf.cell(95, 5, f"Supervisor Responsável: {ap['Aprovação Supervisor']}", ln=True, align="C")
                pdf.ln(15)
            
            # Saída do PDF para download no Streamlit
            pdf_bytes = pdf.output(dest='S')
            st.download_button(
                label="📥 Baixar Relatório PMOC em PDF",
                data=pdf_bytes,
                file_name=f"relatorio_pmoc_{datetime.today().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
