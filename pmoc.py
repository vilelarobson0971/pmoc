"""
PMOC - Versão Mínima para Teste
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ============================================================
# CONFIGURAÇÕES BÁSICAS
# ============================================================

st.set_page_config(
    page_title="PMOC - Teste",
    page_icon="❄️",
    layout="wide"
)

# ============================================================
# DADOS INICIAIS
# ============================================================

def get_initial_data():
    """Retorna dados iniciais"""
    data = {
        'TAG': [1, 2, 3],
        'Local': ['Matriz', 'Filial', 'Matriz'],
        'Setor': ['Recepção', 'CPD', 'RH'],
        'Marca': ['Springer', 'Philco', 'Elgin'],
        'Modelo': ['42MACA12S5', 'Eco Inverter', 'HWFL18B2IA'],
        'BTU': ['12000', '12000', '18000'],
        'Data Manutenção': ['', '', ''],
        'Técnico Executante': ['', '', ''],
        'Aprovação Supervisor': ['', '', ''],
        'Próxima manutenção': ['', '', ''],
        'Observações': ['', '', '']
    }
    return pd.DataFrame(data)

# ============================================================
# INICIALIZAÇÃO
# ============================================================

if 'data' not in st.session_state:
    st.session_state.data = get_initial_data()

# ============================================================
# INTERFACE
# ============================================================

st.title("❄️ PMOC - Teste de Funcionamento")

st.success("✅ Aplicação iniciou com sucesso!")

# Mostrar dados
st.subheader("📊 Dados Carregados")
st.dataframe(st.session_state.data, use_container_width=True)

# Menu simples
menu = st.sidebar.radio(
    "Menu",
    ["Início", "Configuração"]
)

if menu == "Configuração":
    st.header("⚙️ Configuração")
    st.write("Página de configuração")
    
    # Botão para recarregar
    if st.button("Recarregar Dados"):
        st.session_state.data = get_initial_data()
        st.success("Dados recarregados!")
        st.rerun()
    
    # Botão para adicionar
    with st.form("add_form"):
        tag = st.number_input("TAG", min_value=1, step=1)
        local = st.text_input("Local", "Matriz")
        setor = st.text_input("Setor", "Teste")
        marca = st.text_input("Marca", "Teste")
        
        if st.form_submit_button("Adicionar"):
            new_row = {
                'TAG': tag,
                'Local': local,
                'Setor': setor,
                'Marca': marca,
                'Modelo': '',
                'BTU': '0',
                'Data Manutenção': '',
                'Técnico Executante': '',
                'Aprovação Supervisor': '',
                'Próxima manutenção': '',
                'Observações': ''
            }
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Adicionado TAG {tag}!")
            st.rerun()

# Rodapé
st.sidebar.markdown("---")
st.sidebar.text("Versão Teste")

st.info("💡 Se esta página carregou, o Streamlit está funcionando corretamente.")
