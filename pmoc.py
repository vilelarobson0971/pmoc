"""
PMOC - Plano de Manutenção, Operação e Controle
Sistema de gerenciamento de manutenção de aparelhos de ar condicionado
Versão: 2.2 - Versão Simplificada
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import base64
import io

# ============================================================
# CONFIGURAÇÕES
# ============================================================

PAGE_TITLE = "PMOC - Plano de Manutenção, Operação e Controle - AKR Brands"
PAGE_ICON = "❄️"
CONFIG_FILE = "pmoc_config.json"
DATA_FILE = "pmoc_data.csv"
MAINTENANCE_INTERVAL_DAYS = 180
LOCATIONS = ["Matriz", "Filial"]
TECHNICIANS = ["Guilherme", "Ismael"]
DEFAULT_SUPERVISOR = "Ismael"

# ============================================================
# FUNÇÕES DE DADOS
# ============================================================

def load_config():
    """Carrega as configurações do arquivo JSON"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        st.error(f"Erro ao carregar configurações: {str(e)}")
        return {}

def save_config(config_data):
    """Salva as configurações no arquivo JSON"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar configurações: {str(e)}")
        return False

def load_data():
    """Carrega dados do arquivo CSV local"""
    try:
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            # Garantir colunas necessárias
            required_cols = ['TAG', 'Local', 'Setor', 'Marca', 'Modelo', 'BTU', 
                           'Data Manutenção', 'Técnico Executante', 'Aprovação Supervisor',
                           'Próxima manutenção', 'Observações']
            for col in required_cols:
                if col not in df.columns:
                    df[col] = ''
            return df
        return None
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

def save_data(df):
    """Salva dados no arquivo CSV local"""
    try:
        df.to_csv(DATA_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados: {str(e)}")
        return False

def create_initial_data():
    """Cria dados iniciais de exemplo"""
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
    df = pd.DataFrame(initial_data)
    df['BTU'] = df['BTU'].astype(str)
    return df

def ensure_data_initialized():
    """Garante que os dados estejam inicializados"""
    if 'data' not in st.session_state or st.session_state.data is None:
        # Tenta carregar do arquivo
        saved_data = load_data()
        if saved_data is not None:
            st.session_state.data = saved_data
        else:
            st.session_state.data = create_initial_data()
            save_data(st.session_state.data)

def get_data():
    """Retorna os dados atuais"""
    ensure_data_initialized()
    return st.session_state.data

def save_current_data():
    """Salva os dados atuais"""
    try:
        if 'data' in st.session_state and st.session_state.data is not None:
            return save_data(st.session_state.data)
        return False
    except Exception as e:
        st.error(f"Erro ao salvar: {str(e)}")
        return False

# ============================================================
# FUNÇÕES DE EXPORTAÇÃO
# ============================================================

def export_to_csv(df):
    """Exporta dados para CSV"""
    try:
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="pmoc_export_{datetime.now().strftime("%Y%m%d")}.csv">Baixar CSV</a>'
        return href
    except Exception as e:
        st.error(f"Erro ao exportar CSV: {str(e)}")
        return None

def export_to_html(df):
    """Exporta dados para HTML (tabela para impressão)"""
    try:
        html = df.to_html(index=False, classes='table table-striped')
        return html
    except Exception as e:
        st.error(f"Erro ao exportar HTML: {str(e)}")
        return None

# ============================================================
# PÁGINAS DA APLICAÇÃO
# ============================================================

def show_consultation_page():
    """Página de consulta de aparelhos"""
    try:
        st.header("📊 Consulta de Aparelhos")
        
        df = get_data()
        
        if df is None or df.empty:
            st.warning("Nenhum dado disponível. Adicione aparelhos ou carregue do arquivo.")
            return
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            local_filter = st.selectbox("Local", ["Todos"] + list(df['Local'].unique()))
        with col2:
            setor_filter = st.selectbox("Setor", ["Todos"] + list(df['Setor'].unique()))
        with col3:
            marca_filter = st.selectbox("Marca", ["Todos"] + list(df['Marca'].unique()))
        
        # Aplicar filtros
        filtered_data = df.copy()
        if local_filter != "Todos":
            filtered_data = filtered_data[filtered_data['Local'] == local_filter]
        if setor_filter != "Todos":
            filtered_data = filtered_data[filtered_data['Setor'] == setor_filter]
        if marca_filter != "Todos":
            filtered_data = filtered_data[filtered_data['Marca'] == marca_filter]
        
        # Calcular próxima manutenção
        display_data = filtered_data.copy()
        
        def calculate_next_maintenance(row):
            if pd.notna(row['Data Manutenção']) and str(row['Data Manutenção']) != '':
                try:
                    maintenance_date = datetime.strptime(str(row['Data Manutenção']), '%d/%m/%Y')
                    next_maintenance = maintenance_date + timedelta(days=MAINTENANCE_INTERVAL_DAYS)
                    return next_maintenance.strftime('%d/%m/%Y')
                except ValueError:
                    return 'data inválida'
            return 'aguardando programação'
        
        display_data['Próxima manutenção (calculada)'] = display_data.apply(calculate_next_maintenance, axis=1)
        
        # Exibir dados
        columns_to_show = [
            "TAG", "Local", "Setor", "Marca", "Modelo", 
            "BTU", "Data Manutenção", "Próxima manutenção (calculada)",
            "Técnico Executante", "Aprovação Supervisor", "Observações"
        ]
        
        st.dataframe(
            display_data[columns_to_show],
            use_container_width=True,
            hide_index=True
        )
        
        # Botões de exportação
        col1, col2 = st.columns(2)
        with col1:
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exportar para CSV",
                data=csv_data,
                file_name=f'pmoc_export_{datetime.now().strftime("%Y%m%d")}.csv',
                mime='text/csv'
            )
        
        # Estatísticas
        st.subheader("📈 Estatísticas")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Aparelhos", len(filtered_data))
        with col2:
            with_maintenance = len(filtered_data[filtered_data['Data Manutenção'] != ''])
            st.metric("Com manutenção registrada", with_maintenance)
        with col3:
            try:
                overdue_count = 0
                for _, row in display_data.iterrows():
                    if row['Próxima manutenção (calculada)'] not in ['aguardando programação', 'data inválida']:
                        try:
                            next_date = datetime.strptime(row['Próxima manutenção (calculada)'], '%d/%m/%Y')
                            if next_date < datetime.now():
                                overdue_count += 1
                        except:
                            pass
                st.metric("Manutenções Atrasadas", overdue_count)
            except Exception as e:
                st.metric("Manutenções Atrasadas", 0)
                
    except Exception as e:
        st.error(f"Erro ao carregar consulta: {str(e)}")

def show_add_device_page():
    """Página para adicionar aparelho"""
    try:
        st.header("➕ Adicionar Novo Aparelho")
        
        df = get_data()
        
        with st.form("add_form"):
            col1, col2 = st.columns(2)
            with col1:
                tag = st.number_input("TAG*", min_value=1, step=1)
                local = st.selectbox("Local*", LOCATIONS)
                setor = st.text_input("Setor*")
                marca = st.text_input("Marca*")
            with col2:
                modelo = st.text_input("Modelo")
                btu = st.number_input("BTU*", min_value=0, step=1000)
            
            st.markdown("(*) Campos obrigatórios")
            submitted = st.form_submit_button("Adicionar Aparelho", type="primary")
            
            if submitted:
                if df is not None and tag in df['TAG'].values:
                    st.error("❌ Já existe um aparelho com esta TAG!")
                elif not setor or not marca:
                    st.error("❌ Preencha todos os campos obrigatórios!")
                else:
                    new_row = {
                        'TAG': tag,
                        'Local': local,
                        'Setor': setor,
                        'Marca': marca,
                        'Modelo': modelo,
                        'BTU': str(btu),
                        'Data Manutenção': '',
                        'Técnico Executante': '',
                        'Aprovação Supervisor': '',
                        'Próxima manutenção': '',
                        'Observações': ''
                    }
                    
                    if df is None:
                        st.session_state.data = pd.DataFrame([new_row])
                    else:
                        st.session_state.data = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    
                    if save_current_data():
                        st.success(f"✅ Aparelho TAG {tag} adicionado com sucesso!")
                        st.balloons()
                        st.rerun()
                    
    except Exception as e:
        st.error(f"Erro ao adicionar aparelho: {str(e)}")

def show_edit_device_page():
    """Página para editar aparelho"""
    try:
        st.header("✏️ Editar Aparelho")
        
        df = get_data()
        
        if df is None or df.empty:
            st.warning("Não há aparelhos cadastrados para editar")
            return
        
        tag_to_edit = st.selectbox(
            "Selecione a TAG do aparelho a editar",
            df['TAG'].unique()
        )
        
        if tag_to_edit:
            row = df[df['TAG'] == tag_to_edit].iloc[0]
            
            with st.form("edit_form"):
                col1, col2 = st.columns(2)
                with col1:
                    tag = st.number_input("TAG*", value=int(row['TAG']), min_value=1, step=1)
                    local = st.selectbox("Local*", LOCATIONS, index=LOCATIONS.index(row['Local']))
                    setor = st.text_input("Setor*", value=row['Setor'])
                    marca = st.text_input("Marca*", value=row['Marca'])
                with col2:
                    modelo = st.text_input("Modelo", value=row['Modelo'])
                    btu_value = int(row['BTU']) if str(row['BTU']).isdigit() else 0
                    btu = st.number_input("BTU*", value=btu_value, min_value=0, step=1000)
                
                st.markdown("(*) Campos obrigatórios")
                submitted = st.form_submit_button("Atualizar Aparelho", type="primary")
                
                if submitted:
                    if not setor or not marca:
                        st.error("❌ Preencha todos os campos obrigatórios!")
                    else:
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_edit, 'TAG'] = tag
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_edit, 'Local'] = local
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_edit, 'Setor'] = setor
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_edit, 'Marca'] = marca
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_edit, 'Modelo'] = modelo
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_edit, 'BTU'] = str(btu)
                        
                        if save_current_data():
                            st.success(f"✅ Aparelho TAG {tag} atualizado com sucesso!")
                            st.rerun()
                            
    except Exception as e:
        st.error(f"Erro ao editar aparelho: {str(e)}")

def show_remove_device_page():
    """Página para remover aparelho"""
    try:
        st.header("🗑️ Remover Aparelho")
        
        df = get_data()
        
        if df is None or df.empty:
            st.warning("Não há aparelhos cadastrados para remover")
            return
        
        tag_to_remove = st.selectbox(
            "Selecione a TAG do aparelho a remover",
            df['TAG'].unique()
        )
        
        if tag_to_remove:
            row = df[df['TAG'] == tag_to_remove].iloc[0]
            
            st.warning(f"⚠️ Você está prestes a remover permanentemente o aparelho:")
            st.write(f"**TAG:** {tag_to_remove}")
            st.write(f"**Local:** {row['Local']}")
            st.write(f"**Setor:** {row['Setor']}")
            st.write(f"**Marca/Modelo:** {row['Marca']} {row['Modelo']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Remoção", type="primary"):
                    st.session_state.data = df[df['TAG'] != tag_to_remove]
                    if save_current_data():
                        st.success(f"✅ Aparelho TAG {tag_to_remove} removido com sucesso!")
                        st.rerun()
            with col2:
                if st.button("❌ Cancelar"):
                    st.rerun()
                    
    except Exception as e:
        st.error(f"Erro ao remover aparelho: {str(e)}")

def show_maintenance_page():
    """Página para registrar manutenção"""
    try:
        st.header("🔧 Registrar Manutenção")
        
        df = get_data()
        
        if df is None or df.empty:
            st.warning("Não há aparelhos cadastrados para registrar manutenção")
            return
        
        tag_to_maintain = st.selectbox(
            "Selecione a TAG do aparelho para registrar manutenção",
            df['TAG'].unique()
        )
        
        if tag_to_maintain:
            row = df[df['TAG'] == tag_to_maintain].iloc[0]
            
            st.write(f"**Aparelho selecionado:** TAG {tag_to_maintain} - {row['Marca']} {row['Modelo']}")
            st.write(f"**Localização:** {row['Local']} - {row['Setor']}")
            
            with st.form("maintenance_form"):
                maintenance_date = st.date_input(
                    "Data da Manutenção*"
                )
                
                technician = st.selectbox(
                    "Técnico Executante*",
                    TECHNICIANS
                )
                
                supervisor = st.text_input("Aprovação Supervisor", value=DEFAULT_SUPERVISOR)
                observations = st.text_area("Observações", value=row['Observações'])
                
                if maintenance_date:
                    next_maintenance = maintenance_date + timedelta(days=MAINTENANCE_INTERVAL_DAYS)
                    st.info(f"📅 Próxima manutenção será agendada para: **{next_maintenance.strftime('%d/%m/%Y')}**")
                
                st.markdown("(*) Campos obrigatórios")
                submitted = st.form_submit_button("Registrar Manutenção", type="primary")
                
                if submitted:
                    if not maintenance_date or not technician:
                        st.error("❌ Preencha todos os campos obrigatórios!")
                    else:
                        next_maintenance = maintenance_date + timedelta(days=MAINTENANCE_INTERVAL_DAYS)
                        
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_maintain, 'Data Manutenção'] = maintenance_date.strftime('%d/%m/%Y')
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_maintain, 'Técnico Executante'] = technician
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_maintain, 'Aprovação Supervisor'] = supervisor
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_maintain, 'Próxima manutenção'] = next_maintenance.strftime('%d/%m/%Y')
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_maintain, 'Observações'] = observations
                        
                        if save_current_data():
                            st.success(f"✅ Manutenção para TAG {tag_to_maintain} registrada com sucesso!")
                            st.info(f"📅 Próxima manutenção: {next_maintenance.strftime('%d/%m/%Y')}")
                            st.balloons()
                            st.rerun()
                            
    except Exception as e:
        st.error(f"Erro ao registrar manutenção: {str(e)}")

def check_password():
    """Verifica a senha de acesso"""
    try:
        if 'password_correct' not in st.session_state:
            st.session_state.password_correct = False
        
        if not st.session_state.password_correct:
            password = st.text_input("🔑 Digite a senha de acesso:", type="password")
            if password == "king@2025":
                st.session_state.password_correct = True
                st.rerun()
            elif password != "":
                st.error("❌ Senha incorreta!")
            return False
        return True
    except Exception as e:
        return False

def show_configuration_page():
    """Página de configuração"""
    try:
        st.header("⚙️ Configuração")
        
        if not check_password():
            st.stop()
        
        # Carrega configurações
        config_data = load_config()
        
        # Configuração
        st.subheader("📁 Configuração de Dados")
        
        # Mostrar status dos dados
        df = get_data()
        if df is not None:
            st.success(f"✅ Dados carregados: {len(df)} aparelhos")
        else:
            st.warning("⚠️ Nenhum dado carregado")
        
        # Botões de gerenciamento
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 Salvar Dados"):
                if save_current_data():
                    st.success("✅ Dados salvos com sucesso!")
        
        with col2:
            if st.button("🔄 Recarregar Dados"):
                saved_data = load_data()
                if saved_data is not None:
                    st.session_state.data = saved_data
                    st.success("✅ Dados recarregados com sucesso!")
                    st.rerun()
                else:
                    st.warning("⚠️ Nenhum dado salvo encontrado")
        
        with col3:
            if st.button("📊 Resetar Dados"):
                if st.checkbox("Confirmar reset dos dados?"):
                    st.session_state.data = create_initial_data()
                    save_current_data()
                    st.success("✅ Dados resetados com sucesso!")
                    st.rerun()
        
        st.markdown("---")
        
        # Menu de configuração
        st.subheader("📋 Gerenciamento de Aparelhos")
        config_option = st.radio(
            "Selecione a operação",
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
            
    except Exception as e:
        st.error(f"Erro na configuração: {str(e)}")

# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def main():
    """Função principal da aplicação"""
    try:
        # Configuração da página
        st.set_page_config(
            page_title=PAGE_TITLE,
            page_icon=PAGE_ICON,
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Inicializar dados
        ensure_data_initialized()
        
        # Título
        st.title(f"{PAGE_ICON} PMOC - Plano de Manutenção, Operação e Controle - AKR Brands")
        st.markdown("Sistema de controle de manutenção preventiva de aparelhos de ar condicionado")
        
        # Menu
        menu = st.sidebar.radio(
            "📋 Menu Principal",
            ["📊 Consulta", "⚙️ Configuração"]
        )
        
        if menu == "📊 Consulta":
            show_consultation_page()
        elif menu == "⚙️ Configuração":
            show_configuration_page()
        
        # Rodapé
        st.sidebar.markdown("---")
        st.sidebar.text("Desenvolvido por Robson Vilela")
        st.sidebar.text(f"Versão 2.2 - {datetime.now().year}")
        
    except Exception as e:
        st.error(f"❌ Ocorreu um erro inesperado: {str(e)}")

if __name__ == "__main__":
    main()
