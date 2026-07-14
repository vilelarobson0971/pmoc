"""
PMOC - Plano de Manutenção, Operação e Controle
Sistema de gerenciamento de manutenção de aparelhos de ar condicionado
Versão: 2.1
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
from fpdf import FPDF
import tempfile
import os
import requests
import base64
import io
import json
import logging
import traceback

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURAÇÕES
# ============================================================

PAGE_TITLE = "PMOC - Plano de Manutenção, Operação e Controle - AKR Brands"
PAGE_ICON = "❄️"
GITHUB_REPO = "vilelarobson0971/pmoc"
GITHUB_FILE = "pmoc.csv"
CONFIG_FILE = "pmoc_config.json"
MAINTENANCE_INTERVAL_DAYS = 180
LOCATIONS = ["Matriz", "Filial"]
TECHNICIANS = ["Guilherme", "Ismael"]
DEFAULT_SUPERVISOR = "Ismael"
TIMEZONE = 'America/Sao_Paulo'

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
        logger.error(f"Erro ao carregar configurações: {str(e)}")
        return {}

def save_config(config_data):
    """Salva as configurações no arquivo JSON"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar configurações: {str(e)}")
        return False

def load_from_github(token):
    """Carrega dados do GitHub"""
    if not token:
        return None
    
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        
        content = response.json().get("content", "")
        if not content:
            return None
        
        decoded_content = base64.b64decode(content).decode("utf-8")
        if not decoded_content.strip():
            return None
        
        df = pd.read_csv(io.StringIO(decoded_content))
        
        # Garantir colunas necessárias
        required_cols = ['TAG', 'Local', 'Setor', 'Marca', 'Modelo', 'BTU', 
                        'Data Manutenção', 'Técnico Executante', 'Aprovação Supervisor',
                        'Próxima manutenção', 'Observações']
        
        for col in required_cols:
            if col not in df.columns:
                df[col] = ''
        
        return df
        
    except Exception as e:
        logger.error(f"Erro ao carregar do GitHub: {str(e)}")
        return None

def save_to_github(data, token):
    """Salva dados no GitHub"""
    if not token:
        return False
    
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Verifica se o arquivo existe
        response = requests.get(url, headers=headers, timeout=10)
        sha = response.json().get("sha", "") if response.status_code == 200 else ""
        
        # Converte DataFrame para CSV
        csv_data = data.to_csv(index=False)
        encoded_content = base64.b64encode(csv_data.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": f"Atualização PMOC - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": encoded_content,
            "sha": sha if sha else None
        }
        
        response = requests.put(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao salvar no GitHub: {str(e)}")
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
    """Garante que os dados estejam inicializados no session_state"""
    if 'data' not in st.session_state or st.session_state.data is None:
        # Tenta carregar do GitHub
        config_data = load_config()
        token = config_data.get('github_token', '')
        
        if token:
            saved_data = load_from_github(token)
            if saved_data is not None:
                st.session_state.data = saved_data
                return
    
    # Se ainda não tem dados, cria dados iniciais
    if 'data' not in st.session_state or st.session_state.data is None:
        st.session_state.data = create_initial_data()

def save_data():
    """Salva os dados atuais"""
    try:
        if 'data' not in st.session_state or st.session_state.data is None:
            st.error("Não há dados para salvar")
            return False
            
        config_data = load_config()
        token = config_data.get('github_token', '')
        
        if not token:
            st.error("Token de acesso ao GitHub não configurado")
            return False
        
        if save_to_github(st.session_state.data, token):
            return True
        else:
            st.error("Falha ao salvar dados no GitHub.")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao salvar dados: {str(e)}")
        st.error(f"Erro ao salvar: {str(e)}")
        return False

# ============================================================
# GERADOR DE RELATÓRIOS PDF
# ============================================================

def generate_pdf_report(data, title="Relatório de Aparelhos"):
    """Gera relatório PDF dos aparelhos"""
    try:
        if data is None or data.empty:
            st.warning("Não há dados para gerar o relatório")
            return None
        
        pdf = FPDF(orientation='L')
        pdf.add_page()
        
        # Configuração de fonte
        pdf.set_font("Arial", size=9)
        pdf.set_text_color(0, 0, 0)
        
        # Fuso horário
        tz = pytz.timezone(TIMEZONE)
        now = datetime.now(tz)
        
        # Cabeçalho
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, PAGE_TITLE, 0, 1, 'C')
        pdf.ln(5)
        
        # Título do relatório
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, title, 0, 1, 'C')
        pdf.ln(5)
        
        # Data e hora
        pdf.set_font("Arial", 'I', 9)
        pdf.cell(0, 10, f"Gerado em: {now.strftime('%d/%m/%Y %H:%M')}", 0, 1, 'R')
        pdf.ln(8)
        
        # Configuração das colunas
        col_widths = [12, 20, 30, 20, 25, 12, 25, 25, 25, 25, 40]
        headers = ["TAG", "Local", "Setor", "Marca", "Modelo", 
                  "BTU", "Última Manut.", "Próx. Manut.", 
                  "Técnico", "Aprovação", "Observações"]
        
        # Cabeçalho da tabela
        pdf.set_font("Arial", 'B', 8)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 8, header, 1, 0, 'C')
        pdf.ln()
        
        # Conteúdo da tabela
        pdf.set_font("Arial", size=7)
        for _, row in data.iterrows():
            cells = [
                str(row['TAG'])[:10] if pd.notna(row['TAG']) else '',
                str(row['Local'])[:18] if pd.notna(row['Local']) else '',
                str(row['Setor'])[:25] if pd.notna(row['Setor']) else '',
                str(row['Marca'])[:18] if pd.notna(row['Marca']) else '',
                str(row['Modelo'])[:22] if pd.notna(row['Modelo']) else '',
                str(row['BTU'])[:10] if pd.notna(row['BTU']) else '',
                str(row['Data Manutenção'])[:10] if pd.notna(row['Data Manutenção']) and str(row['Data Manutenção']) != '' else 'N/A',
                str(row['Próxima manutenção'])[:10] if pd.notna(row['Próxima manutenção']) and str(row['Próxima manutenção']) != '' else 'N/A',
                str(row['Técnico Executante'])[:22] if pd.notna(row['Técnico Executante']) else '',
                str(row['Aprovação Supervisor'])[:22] if pd.notna(row['Aprovação Supervisor']) else '',
                str(row['Observações'])[:60] if pd.notna(row['Observações']) and str(row['Observações']) != '' else 'Nenhuma'
            ]
            
            for i, cell in enumerate(cells):
                pdf.cell(col_widths[i], 6, cell, 1, 0, 'C' if i in [0, 5, 6, 7] else 'L')
            pdf.ln()
        
        # Estatísticas
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Estatísticas:", 0, 1)
        pdf.set_font("Arial", size=10)
        
        total = len(data)
        pdf.cell(0, 10, f"Total de Aparelhos: {total}", 0, 1)
        
        try:
            with_maintenance = len(data[data['Data Manutenção'].notna() & (data['Data Manutenção'] != '')])
            pdf.cell(0, 10, f"Com manutenção registrada: {with_maintenance}", 0, 1)
            
            overdue_count = 0
            for _, row in data.iterrows():
                next_date = row.get('Próxima manutenção', '')
                if next_date and str(next_date) != '':
                    try:
                        date_obj = datetime.strptime(str(next_date), '%d/%m/%Y')
                        if date_obj < datetime.now():
                            overdue_count += 1
                    except ValueError:
                        pass
            
            pdf.cell(0, 10, f"Manutenções atrasadas: {overdue_count}", 0, 1)
        except Exception as e:
            pdf.cell(0, 10, "Erro ao calcular estatísticas", 0, 1)
        
        # Rodapé
        pdf.ln(15)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 10, "Sistema PMOC - AKR Brands", 0, 0, 'C')
        
        # Gera o arquivo
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(temp_file.name)
        
        return temp_file.name
        
    except Exception as e:
        logger.error(f"Erro ao gerar PDF: {str(e)}")
        logger.error(traceback.format_exc())
        st.error(f"Erro ao gerar PDF: {str(e)}")
        return None

# ============================================================
# PÁGINAS DA APLICAÇÃO
# ============================================================

def show_consultation_page():
    """Página de consulta de aparelhos"""
    try:
        st.header("📊 Consulta de Aparelhos")
        
        # Garantir que os dados existem
        ensure_data_initialized()
        
        if st.session_state.data is None or st.session_state.data.empty:
            st.warning("Nenhum dado disponível. Adicione aparelhos ou carregue do GitHub.")
            return
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            local_filter = st.selectbox("Local", ["Todos"] + list(st.session_state.data['Local'].unique()))
        with col2:
            setor_filter = st.selectbox("Setor", ["Todos"] + list(st.session_state.data['Setor'].unique()))
        with col3:
            marca_filter = st.selectbox("Marca", ["Todos"] + list(st.session_state.data['Marca'].unique()))
        
        # Aplicar filtros
        filtered_data = st.session_state.data.copy()
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
        
        # Gerar relatório
        st.subheader("📄 Gerar Relatório")
        selected_tags = st.multiselect(
            "Selecione os aparelhos para incluir no relatório (deixe vazio para todos)",
            options=filtered_data['TAG'].unique()
        )
        
        if st.button("Gerar Relatório PDF", type="primary"):
            with st.spinner("Gerando relatório PDF..."):
                if selected_tags:
                    report_data = filtered_data[filtered_data['TAG'].isin(selected_tags)]
                    title = f"Relatório de Aparelhos Selecionados ({len(report_data)} itens)"
                else:
                    report_data = filtered_data
                    title = f"Relatório Completo de Aparelhos ({len(report_data)} itens)"
                
                pdf_file = generate_pdf_report(report_data, title)
                
                if pdf_file:
                    try:
                        with open(pdf_file, "rb") as f:
                            pdf_bytes = f.read()
                        
                        st.download_button(
                            label="📥 Baixar Relatório PDF",
                            data=pdf_bytes,
                            file_name=f"relatorio_pmoc_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            mime="application/pdf"
                        )
                    finally:
                        if os.path.exists(pdf_file):
                            os.unlink(pdf_file)
        
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
        
        # Exportar CSV
        st.download_button(
            label="📥 Exportar para CSV",
            data=st.session_state.data.to_csv(index=False).encode('utf-8'),
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
                st.error(f"Erro ao calcular atrasos: {str(e)}")
                st.metric("Manutenções Atrasadas", 0)
                
    except Exception as e:
        st.error(f"Erro ao carregar consulta: {str(e)}")
        logger.error(f"Erro em show_consultation_page: {str(e)}")
        logger.error(traceback.format_exc())

def show_add_device_page():
    """Página para adicionar aparelho"""
    try:
        st.header("➕ Adicionar Novo Aparelho")
        
        ensure_data_initialized()
        
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
                if st.session_state.data is not None and tag in st.session_state.data['TAG'].values:
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
                    
                    if st.session_state.data is None:
                        st.session_state.data = pd.DataFrame([new_row])
                    else:
                        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                    
                    if save_data():
                        st.success(f"✅ Aparelho TAG {tag} adicionado com sucesso!")
                        st.balloons()
                        st.rerun()
                    
    except Exception as e:
        st.error(f"Erro ao adicionar aparelho: {str(e)}")
        logger.error(f"Erro em show_add_device_page: {str(e)}")
        logger.error(traceback.format_exc())

def show_edit_device_page():
    """Página para editar aparelho"""
    try:
        st.header("✏️ Editar Aparelho")
        
        ensure_data_initialized()
        
        if st.session_state.data is None or st.session_state.data.empty:
            st.warning("Não há aparelhos cadastrados para editar")
            return
        
        tag_to_edit = st.selectbox(
            "Selecione a TAG do aparelho a editar",
            st.session_state.data['TAG'].unique()
        )
        
        if tag_to_edit:
            row = st.session_state.data[st.session_state.data['TAG'] == tag_to_edit].iloc[0]
            
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
                        
                        if save_data():
                            st.success(f"✅ Aparelho TAG {tag} atualizado com sucesso!")
                            st.rerun()
                            
    except Exception as e:
        st.error(f"Erro ao editar aparelho: {str(e)}")
        logger.error(f"Erro em show_edit_device_page: {str(e)}")
        logger.error(traceback.format_exc())

def show_remove_device_page():
    """Página para remover aparelho"""
    try:
        st.header("🗑️ Remover Aparelho")
        
        ensure_data_initialized()
        
        if st.session_state.data is None or st.session_state.data.empty:
            st.warning("Não há aparelhos cadastrados para remover")
            return
        
        tag_to_remove = st.selectbox(
            "Selecione a TAG do aparelho a remover",
            st.session_state.data['TAG'].unique()
        )
        
        if tag_to_remove:
            row = st.session_state.data[st.session_state.data['TAG'] == tag_to_remove].iloc[0]
            
            st.warning(f"⚠️ Você está prestes a remover permanentemente o aparelho:")
            st.write(f"**TAG:** {tag_to_remove}")
            st.write(f"**Local:** {row['Local']}")
            st.write(f"**Setor:** {row['Setor']}")
            st.write(f"**Marca/Modelo:** {row['Marca']} {row['Modelo']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Remoção", type="primary"):
                    st.session_state.data = st.session_state.data[st.session_state.data['TAG'] != tag_to_remove]
                    if save_data():
                        st.success(f"✅ Aparelho TAG {tag_to_remove} removido com sucesso!")
                        st.rerun()
            with col2:
                if st.button("❌ Cancelar"):
                    st.rerun()
                    
    except Exception as e:
        st.error(f"Erro ao remover aparelho: {str(e)}")
        logger.error(f"Erro em show_remove_device_page: {str(e)}")
        logger.error(traceback.format_exc())

def show_maintenance_page():
    """Página para registrar manutenção"""
    try:
        st.header("🔧 Registrar Manutenção")
        
        ensure_data_initialized()
        
        if st.session_state.data is None or st.session_state.data.empty:
            st.warning("Não há aparelhos cadastrados para registrar manutenção")
            return
        
        tag_to_maintain = st.selectbox(
            "Selecione a TAG do aparelho para registrar manutenção",
            st.session_state.data['TAG'].unique()
        )
        
        if tag_to_maintain:
            row = st.session_state.data[st.session_state.data['TAG'] == tag_to_maintain].iloc[0]
            
            st.write(f"**Aparelho selecionado:** TAG {tag_to_maintain} - {row['Marca']} {row['Modelo']}")
            st.write(f"**Localização:** {row['Local']} - {row['Setor']}")
            
            with st.form("maintenance_form"):
                maintenance_date = st.date_input(
                    "Data da Manutenção*",
                    format="DD/MM/YYYY"
                )
                
                technician = st.selectbox(
                    "Técnico Executante*",
                    TECHNICIANS,
                    index=0
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
                        
                        if save_data():
                            st.success(f"✅ Manutenção para TAG {tag_to_maintain} registrada com sucesso!")
                            st.info(f"📅 Próxima manutenção: {next_maintenance.strftime('%d/%m/%Y')}")
                            st.balloons()
                            st.rerun()
                            
    except Exception as e:
        st.error(f"Erro ao registrar manutenção: {str(e)}")
        logger.error(f"Erro em show_maintenance_page: {str(e)}")
        logger.error(traceback.format_exc())

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
        logger.error(f"Erro em check_password: {str(e)}")
        return False

def show_configuration_page():
    """Página de configuração"""
    try:
        st.header("⚙️ Configuração")
        
        if not check_password():
            st.stop()
        
        # Carrega configurações
        config_data = load_config()
        
        # Configuração do GitHub
        st.subheader("🔐 Configuração do GitHub")
        
        github_token = st.text_input(
            "Token de Acesso ao GitHub",
            type="password",
            value=config_data.get('github_token', ''),
            help="Obtenha em: GitHub > Settings > Developer Settings > Personal Access Tokens"
        )
        
        if st.button("💾 Salvar Configurações", type="primary"):
            config_data['github_token'] = github_token
            if save_config(config_data):
                st.success("✅ Configurações salvas com sucesso!")
                if github_token:
                    saved_data = load_from_github(github_token)
                    if saved_data is not None:
                        st.session_state.data = saved_data
                        st.success("✅ Dados carregados do GitHub com sucesso!")
        
        # Sincronização
        st.subheader("🔄 Sincronização Manual")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Carregar do GitHub"):
                if github_token:
                    saved_data = load_from_github(github_token)
                    if saved_data is not None:
                        st.session_state.data = saved_data
                        st.success("✅ Dados carregados do GitHub com sucesso!")
                    else:
                        st.error("❌ Falha ao carregar dados do GitHub")
                else:
                    st.error("❌ Token de acesso não configurado!")
        
        with col2:
            if st.button("📤 Salvar no GitHub"):
                if github_token:
                    if save_data():
                        st.success("✅ Dados salvos no GitHub com sucesso!")
                    else:
                        st.error("❌ Falha ao salvar dados no GitHub")
                else:
                    st.error("❌ Token de acesso não configurado!")
        
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
        logger.error(f"Erro em show_configuration_page: {str(e)}")
        logger.error(traceback.format_exc())

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
        st.sidebar.text(f"Versão 2.1 - {datetime.now().year}")
        
    except Exception as e:
        st.error(f"❌ Ocorreu um erro inesperado: {str(e)}")
        st.error("Por favor, contate o suporte técnico.")
        logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
