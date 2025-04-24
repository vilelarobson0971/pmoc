import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
from fpdf import FPDF
import tempfile
import os

# Configuração da página
def setup_page():
    st.set_page_config(
        page_title="PMOC - Plano de Manutenção, Operação e Controle - AKR Brands",
        page_icon="❄️",
        layout="wide"
    )

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
            'Próxima manutenção': ['']*41
        }
        st.session_state.data = pd.DataFrame(initial_data)
        st.session_state.data['BTU'] = st.session_state.data['BTU'].astype(str)

# Função principal
def main():
    try:
        setup_page()
        init_data()
        
        st.title("❄️ PMOC - Plano de Manutenção, Operação e Controle - AKR Brands")
        st.markdown("Controle de manutenção preventiva de aparelhos de ar condicionado")
        
        menu = st.sidebar.selectbox("Menu", ["Consulta", "Adicionar Aparelho", "Editar Aparelho", "Remover Aparelho", "Realizar Manutenção"])
        
        if menu == "Consulta":
            show_consultation_page()
        elif menu == "Adicionar Aparelho":
            show_add_device_page()
        elif menu == "Editar Aparelho":
            show_edit_device_page()
        elif menu == "Remover Aparelho":
            show_remove_device_page()
        elif menu == "Realizar Manutenção":
            show_maintenance_page()
            
    except Exception as e:
        st.error(f"Erro ao carregar a aplicação: {str(e)}")

# Páginas específicas (implemente essas funções conforme necessário)
def show_consultation_page():
    st.header("Consulta de Aparelhos")
    # Adicione aqui o conteúdo da página de consulta

def show_add_device_page():
    st.header("Adicionar Novo Aparelho")
    # Adicione aqui o conteúdo da página de adição

def show_edit_device_page():
    st.header("Editar Aparelho Existente")
    # Adicione aqui o conteúdo da página de edição

def show_remove_device_page():
    st.header("Remover Aparelho")
    # Adicione aqui o conteúdo da página de remoção

def show_maintenance_page():
    st.header("Registrar Manutenção")
    # Adicione aqui o conteúdo da página de manutenção

if __name__ == "__main__":
    main()
