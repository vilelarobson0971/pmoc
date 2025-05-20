import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
from fpdf import FPDF
import tempfile
import os
import numpy as np
import requests
import base64
import io
import time

# Configuração inicial da página
def setup_page():
    st.set_page_config(
        page_title="PMOC - Plano de Manutenção, Operação e Controle - AKR Brands",
        page_icon="❄️",
        layout="wide"
    )

# Funções para sincronização com GitHub
def get_github_file_url(repo, file_path):
    return f"https://api.github.com/repos/{repo}/contents/{file_path}"

def load_from_github(repo, file_path, token=None):
    try:
        url = get_github_file_url(repo, file_path)
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        } if token else {}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 404:
            return None
            
        response.raise_for_status()
        
        content = response.json().get("content", "")
        if not content:
            return None
            
        decoded_content = base64.b64decode(content).decode("utf-8")
        
        if not decoded_content.strip():
            return None
            
        return pd.read_csv(io.StringIO(decoded_content))
    except Exception as e:
        st.error(f"Erro ao carregar dados do GitHub: {str(e)}")
        return None

def save_to_github(repo, file_path, data, token=None):
    try:
        url = get_github_file_url(repo, file_path)
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        } if token else {}
        
        # Verifica se o arquivo já existe para obter o SHA
        response = requests.get(url, headers=headers)
        sha = response.json().get("sha", "") if response.status_code == 200 else ""
        
        # Converte DataFrame para CSV
        csv_data = data.to_csv(index=False)
        encoded_content = base64.b64encode(csv_data.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": f"Atualização PMOC - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": encoded_content,
            "sha": sha if sha else None
        }
        
        response = requests.put(url, json=payload, headers=headers)
        response.raise_for_status()
        
        # Verifica se a atualização foi bem-sucedida
        if response.status_code == 200 or response.status_code == 201:
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao salvar dados no GitHub: {str(e)}")
        return False

# Inicialização dos dados
def init_data():
    if 'data' not in st.session_state:
        initial_data = {
            'TAG': list(range(1, 42)),
            'Local': ['Matriz']*20 + ['Filial']*13 + ['Matriz']*8,
            'Setor': ['Recepção', 'CPD', 'CPD', 'RH', 'Marketing', 'Marketing', 'Inteligência de mercado',
                     'Antigo Show Room', 'Diretoria - Rafael', 'Controladoria', 'Diretoria - Jair',
                     'Sala reunião térreo', 'Financeiro', 'Diretoria', 'Sala reunião principal',
                     'Sala reunião principal', 'Expedição - Recepção', 'Expedição - Sala Welder',
                     'Corte - Risco', 'Estoque - Sala Umberto', 'Laboratório - Sala ADM',
                     'Laboratório - Sala ADM', 'Gerência', 'Modelagem', 'Inteligência do Produto',
                     'Estilo', 'Show Room', 'T.I.', 'PCP', 'PCP', 'Compras', 'Refeitório', 'Refeitório',
                     'Refeitório', 'Sala de Reunião', 'Estúdio', 'Estúdio', 'Refeitório', 'Refeitório',
                     'Sala Expedição Kids', 'Ecommerce'],
            'Marca': ['Springer', 'Philco', 'Elgin', 'Springer', 'TCL', 'TCL', 'TCL', 'Springer',
                     'Springer', 'Springer', 'COMFEE', 'COMFEE', 'Springer', 'Springer', 'Springer',
                     'Springer', 'Philco', 'Agratto', 'COMFEE', 'GREE', 'GREE', 'GREE', 'GREE', 'GREE',
                     'GREE', 'GREE', 'GREE', 'Consul', 'Electrolux', 'GREE', 'Philco', 'GREE', 'GREE',
                     'GREE', 'GREE', 'Philco', 'Springer', 'Agratto', 'Agratto', '', ''],
            'Modelo': ['42MACA12S5', 'Eco Inverter', 'HWFL18B2IA', '42MACB18S5', 'TAC18CSA1', 'TAC18CSA1',
                      'TAC18CSA1', '42MACB18S5', '42AFFCL12', '42MACB18S5', '42AFCE12X5', '42AFCD18F5',
                      '42MACB18S5', '42TFCA', '42MACB18S5', '42MACB18S5', 'Eco Inverter', 'ACST12FR4-02',
                      '42AFCD12F5', 'GWC12QC-D3NNB4D/I', 'GWC18AAD-D3NNA1D/I', 'GWC18AAD-D3NNA1D/I',
                      'GWC12AAC-D3NNB4D/I', 'GWC12AAC-D3NNB4D/I', 'GWC24QE-D3NNB4D/I', 'GWC24QE-D3NNB4D/I',
                      'GWC24QE-D3NNB4D/I', '', 'VI18F', 'GWC12QC-D3NNB4D/I', 'Eco Inverter',
                      'GWC24QE-D3NNB4D/I', 'GWC24QE-D3NNB4D/I', 'GWC24QE-D3NNB4D/I', 'GWC24QE-D3NNB4D/I',
                      '', '', 'LCS24F-02', 'LCS24F-02', '', ''],
            'BTU': [12000, 12000, 18000, 18000, 18000, 18000, 18000, 18000, 12000, 18000, 12000, 18000,
                   18000, 12000, 18000, 18000, 18000, 12000, 12000, 12000, 18000, 18000, 12000, 12000,
                   24000, 24000, 24000, 12000, 18000, 12000, 12000, 24000, 24000, 24000, 24000, 24000,
                   24000, 24000, 24000, 0, 12000],
            'Data Manutenção': ['']*41,
            'Técnico Executante': ['']*41,
            'Aprovação Supervisor': ['']*41,
            'Próxima manutenção': ['']*41,
            'Observações': ['']*41
        }
        st.session_state.data = pd.DataFrame(initial_data)
        st.session_state.data['BTU'] = st.session_state.data['BTU'].astype(str)

# Função para salvar dados com feedback melhorado
def save_data():
    try:
        repo = "vilelarobson0971/pmoc"
        file_path = "pmoc.csv"
        
        if 'github_token' not in st.session_state or not st.session_state.github_token:
            st.error("🔑 Token de acesso ao GitHub não configurado!")
            return False
        
        with st.spinner("⏳ Salvando dados no GitHub..."):
            time.sleep(1)  # Simula um delay para visualização
            if save_to_github(repo, file_path, st.session_state.data, st.session_state.github_token):
                st.toast("✅ Dados salvos no GitHub com sucesso!", icon="✅")
                return True
            else:
                st.error("❌ Falha ao salvar dados no GitHub!")
                return False
    except Exception as e:
        st.error(f"⚠️ Erro ao salvar dados: {str(e)}")
        return False

# Carregar dados com tratamento melhorado
def load_data():
    try:
        repo = "vilelarobson0971/pmoc"
        file_path = "pmoc.csv"
        
        if 'github_token' not in st.session_state or not st.session_state.github_token:
            st.warning("🔑 Token não configurado. Usando dados locais.")
            return
        
        with st.spinner("⏳ Carregando dados do GitHub..."):
            time.sleep(1)  # Simula um delay para visualização
            saved_data = load_from_github(repo, file_path, st.session_state.github_token)
            
            if saved_data is not None:
                if 'Observações' not in saved_data.columns:
                    saved_data['Observações'] = ''
                st.session_state.data = saved_data
                st.toast("✅ Dados carregados do GitHub com sucesso!", icon="✅")
            else:
                st.warning("📂 Arquivo não encontrado no GitHub. Usando dados locais.")
    except Exception as e:
        st.error(f"⚠️ Erro ao carregar dados: {str(e)}")

# [...] (O resto do script permanece igual, incluindo as funções generate_pdf_report, show_consultation_page, etc.)

# Página de Configuração com melhor feedback
def show_configuration_page():
    st.header("⚙️ Configuração")
    
    if not check_password():
        st.stop()
    
    # Configuração do Token do GitHub
    st.subheader("🔑 Configuração do GitHub")
    if 'github_token' not in st.session_state:
        st.session_state.github_token = ""
    
    github_token = st.text_input(
        "Token de Acesso ao GitHub (obrigatório para sincronização)",
        type="password",
        value=st.session_state.github_token,
        help="Obtenha seu token em: GitHub > Settings > Developer Settings > Personal Access Tokens"
    )
    
    if st.button("💾 Salvar Token"):
        st.session_state.github_token = github_token
        st.toast("✅ Token salvo com sucesso!", icon="✅")
    
    # Sincronização manual
    st.subheader("🔄 Sincronização Manual")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⬇️ Carregar Dados do GitHub", help="Busca os dados mais recentes do repositório"):
            if st.session_state.github_token:
                load_data()
            else:
                st.error("❌ Token não configurado!")
    
    with col2:
        if st.button("⬆️ Salvar Dados no GitHub", help="Envia os dados locais para o repositório"):
            if st.session_state.github_token:
                save_data()
            else:
                st.error("❌ Token não configurado!")
    
    # Menu de configuração
    config_option = st.sidebar.radio(
        "Opções de Configuração",
        ["Adicionar Aparelho", "Editar Aparelho", "Remover Aparelho", "Realizar Manutenção"]
    )
    
    if config_option == "Adicionar Aparelho":
        show_add_device_page()
    elif config_option == "Editar Aparelho":
        show_edit_device_page()
    elif config_option == "Remover Aparelho":
        show_remove_device_page()
    elif config_option == "Realizar Manutenção":
        show_maintenance_page()

# Função principal
def main():
    try:
        setup_page()
        init_data()
        load_data()
        
        st.title("❄️ PMOC - Plano de Manutenção, Operação e Controle - AKR Brands")
        st.markdown("Controle de manutenção preventiva de aparelhos de ar condicionado")
        
        menu = st.sidebar.radio(
            "Menu Principal",
            ["Consulta", "Configuração"]
        )
        
        if menu == "Consulta":
            show_consultation_page()
        elif menu == "Configuração":
            show_configuration_page()
            
    except Exception as e:
        st.error(f"⚠️ Ocorreu um erro inesperado: {str(e)}")

if __name__ == "__main__":
    main()
