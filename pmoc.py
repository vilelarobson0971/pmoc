"""
PMOC - Plano de Manutenção, Operação e Controle
Sistema de gerenciamento de manutenção de aparelhos de ar condicionado
Versão: 2.0
"""

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
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import logging
from dataclasses import dataclass, asdict
from enum import Enum

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# CONSTANTES E CONFIGURAÇÕES
# ============================================================

@dataclass
class AppConfig:
    """Configurações da aplicação"""
    page_title: str = "PMOC - Plano de Manutenção, Operação e Controle - AKR Brands"
    page_icon: str = "❄️"
    layout: str = "wide"
    github_repo: str = "vilelarobson0971/pmoc"
    github_file: str = "pmoc.csv"
    config_file: str = "pmoc_config.json"
    maintenance_interval_days: int = 180
    max_btu: int = 60000
    min_btu: int = 0
    timezone: str = 'America/Sao_Paulo'
    
    # Opções fixas
    LOCATIONS: tuple = ("Matriz", "Filial")
    TECHNICIANS: tuple = ("Guilherme", "Ismael")
    DEFAULT_SUPERVISOR: str = "Ismael"

config = AppConfig()

# ============================================================
# CLASSES DE DOMÍNIO
# ============================================================

class MaintenanceStatus(Enum):
    """Status de manutenção do aparelho"""
    UP_TO_DATE = "Em dia"
    DUE_SOON = "Vence em breve"
    OVERDUE = "Atrasado"
    NOT_SCHEDULED = "Não agendado"
    INVALID = "Data inválida"

@dataclass
class Device:
    """Representa um aparelho de ar condicionado"""
    tag: int
    location: str
    sector: str
    brand: str
    model: str
    btu: int
    maintenance_date: Optional[str] = None
    technician: str = ""
    supervisor: str = ""
    next_maintenance: Optional[str] = None
    observations: str = ""
    
    @classmethod
    def from_dataframe_row(cls, row: pd.Series) -> 'Device':
        """Cria instância a partir de uma linha do DataFrame"""
        return cls(
            tag=int(row['TAG']),
            location=str(row['Local']),
            sector=str(row['Setor']),
            brand=str(row['Marca']),
            model=str(row['Modelo']),
            btu=int(row['BTU']) if pd.notna(row['BTU']) and str(row['BTU']).strip() else 0,
            maintenance_date=str(row['Data Manutenção']) if pd.notna(row['Data Manutenção']) and str(row['Data Manutenção']) != '' else None,
            technician=str(row['Técnico Executante']) if pd.notna(row['Técnico Executante']) else "",
            supervisor=str(row['Aprovação Supervisor']) if pd.notna(row['Aprovação Supervisor']) else "",
            next_maintenance=str(row['Próxima manutenção']) if pd.notna(row['Próxima manutenção']) and str(row['Próxima manutenção']) != '' else None,
            observations=str(row['Observações']) if pd.notna(row['Observações']) else ""
        )
    
    def to_dataframe_row(self) -> Dict[str, Any]:
        """Converte para dicionário compatível com DataFrame"""
        return {
            'TAG': self.tag,
            'Local': self.location,
            'Setor': self.sector,
            'Marca': self.brand,
            'Modelo': self.model,
            'BTU': str(self.btu),
            'Data Manutenção': self.maintenance_date or '',
            'Técnico Executante': self.technician,
            'Aprovação Supervisor': self.supervisor,
            'Próxima manutenção': self.next_maintenance or '',
            'Observações': self.observations
        }
    
    def get_maintenance_status(self) -> MaintenanceStatus:
        """Retorna o status da manutenção"""
        if not self.next_maintenance or self.next_maintenance == '':
            return MaintenanceStatus.NOT_SCHEDULED
        
        try:
            next_date = datetime.strptime(self.next_maintenance, '%d/%m/%Y')
            today = datetime.now()
            
            if next_date < today:
                return MaintenanceStatus.OVERDUE
            elif (next_date - today).days <= 30:
                return MaintenanceStatus.DUE_SOON
            else:
                return MaintenanceStatus.UP_TO_DATE
        except ValueError:
            return MaintenanceStatus.INVALID
    
    def calculate_next_maintenance(self) -> Optional[str]:
        """Calcula a próxima data de manutenção"""
        if not self.maintenance_date or self.maintenance_date == '':
            return None
        
        try:
            maintenance_date = datetime.strptime(self.maintenance_date, '%d/%m/%Y')
            next_date = maintenance_date + timedelta(days=config.maintenance_interval_days)
            return next_date.strftime('%d/%m/%Y')
        except ValueError:
            return None
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Valida os dados do aparelho"""
        errors = []
        
        if self.tag <= 0:
            errors.append("TAG deve ser um número positivo")
        
        if self.location not in config.LOCATIONS:
            errors.append(f"Local deve ser um de: {', '.join(config.LOCATIONS)}")
        
        if not self.sector or len(self.sector.strip()) == 0:
            errors.append("Setor é obrigatório")
        
        if not self.brand or len(self.brand.strip()) == 0:
            errors.append("Marca é obrigatória")
        
        if self.btu < config.min_btu or self.btu > config.max_btu:
            errors.append(f"BTU deve estar entre {config.min_btu} e {config.max_btu}")
        
        return len(errors) == 0, errors

# ============================================================
# GERENCIADOR DE DADOS
# ============================================================

class DataManager:
    """Gerencia o carregamento e salvamento de dados"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.DataManager")
    
    def load_config(self) -> Dict[str, str]:
        """Carrega configurações do arquivo"""
        try:
            if os.path.exists(config.config_file):
                with open(config.config_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Erro ao carregar configurações: {str(e)}")
            return {}
    
    def save_config(self, config_data: Dict[str, str]) -> bool:
        """Salva configurações no arquivo"""
        try:
            with open(config.config_file, 'w') as f:
                json.dump(config_data, f)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar configurações: {str(e)}")
            return False
    
    def load_from_github(self, token: str) -> Optional[pd.DataFrame]:
        """Carrega dados do GitHub"""
        if not token:
            self.logger.warning("Token não fornecido")
            return None
            
        try:
            url = f"https://api.github.com/repos/{config.github_repo}/contents/{config.github_file}"
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
            
            self.logger.info(f"Dados carregados do GitHub: {len(df)} registros")
            return df
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro de rede ao carregar do GitHub: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados do GitHub: {str(e)}")
            return None
    
    def save_to_github(self, data: pd.DataFrame, token: str) -> bool:
        """Salva dados no GitHub"""
        if not token:
            self.logger.warning("Token não fornecido")
            return False
            
        try:
            url = f"https://api.github.com/repos/{config.github_repo}/contents/{config.github_file}"
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Verifica se o arquivo existe para obter SHA
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
            
            self.logger.info("Dados salvos no GitHub com sucesso")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro de rede ao salvar no GitHub: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados no GitHub: {str(e)}")
            return False

# ============================================================
# GERENCIADOR DE ESTADO
# ============================================================

class StateManager:
    """Gerencia o estado da aplicação"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.logger = logging.getLogger(f"{__name__}.StateManager")
    
    def initialize(self) -> pd.DataFrame:
        """Inicializa os dados da aplicação"""
        if 'data' not in st.session_state:
            self.logger.info("Inicializando dados...")
            config_data = self.data_manager.load_config()
            token = config_data.get('github_token', '')
            
            # Tenta carregar do GitHub
            if token:
                saved_data = self.data_manager.load_from_github(token)
                if saved_data is not None:
                    st.session_state.data = self._ensure_columns(saved_data)
                    self.logger.info("Dados carregados do GitHub")
                    return st.session_state.data
            
            # Dados iniciais
            st.session_state.data = self._create_initial_data()
            self.logger.info("Dados iniciais criados")
        
        return st.session_state.data
    
    def _ensure_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Garante que todas as colunas necessárias existem"""
        required_cols = ['TAG', 'Local', 'Setor', 'Marca', 'Modelo', 'BTU', 
                        'Data Manutenção', 'Técnico Executante', 'Aprovação Supervisor',
                        'Próxima manutenção', 'Observações']
        
        for col in required_cols:
            if col not in df.columns:
                df[col] = ''
        
        # Converte BTU para string
        if 'BTU' in df.columns:
            df['BTU'] = df['BTU'].astype(str)
        
        return df
    
    def _create_initial_data(self) -> pd.DataFrame:
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
    
    def save(self) -> bool:
        """Salva os dados atuais"""
        try:
            config_data = self.data_manager.load_config()
            token = config_data.get('github_token', '')
            
            if not token:
                st.error("Token de acesso ao GitHub não configurado")
                return False
            
            if self.data_manager.save_to_github(st.session_state.data, token):
                st.success("Dados salvos no GitHub com sucesso!")
                return True
            else:
                st.error("Falha ao salvar dados no GitHub.")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados: {str(e)}")
            st.error(f"Erro ao salvar: {str(e)}")
            return False

# ============================================================
# GERADOR DE RELATÓRIOS
# ============================================================

class ReportGenerator:
    """Gera relatórios em PDF"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ReportGenerator")
        self.tz = pytz.timezone(config.timezone)
    
    def generate_pdf(self, data: pd.DataFrame, title: str = "Relatório de Aparelhos") -> Optional[str]:
        """Gera relatório PDF dos aparelhos"""
        if data.empty:
            st.warning("Não há dados para gerar o relatório")
            return None
            
        try:
            pdf = FPDF(orientation='L')
            pdf.add_page()
            
            # Cabeçalho
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, config.page_title, 0, 1, 'C')
            pdf.ln(5)
            
            # Título do relatório
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, title, 0, 1, 'C')
            pdf.ln(5)
            
            # Data e hora
            now = datetime.now(self.tz)
            pdf.set_font("Arial", 'I', 9)
            pdf.cell(0, 10, f"Gerado em: {now.strftime('%d/%m/%Y %H:%M:%S')}", 0, 1, 'R')
            pdf.ln(8)
            
            # Configuração da tabela
            col_widths = [12, 20, 30, 20, 25, 12, 25, 25, 25, 25, 40]
            headers = ["TAG", "Local", "Setor", "Marca", "Modelo", 
                      "BTU", "Última Manut.", "Próx. Manut.", 
                      "Técnico", "Aprovação", "Observações"]
            
            # Cabeçalho da tabela
            pdf.set_font("Arial", 'B', 8)
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 8, header, 1, 0, 'C')
            pdf.ln()
            
            # Conteúdo
            pdf.set_font("Arial", size=7)
            for _, row in data.iterrows():
                # Processar dados
                cells = [
                    self._safe_str(row.get('TAG', ''))[:10],
                    self._safe_str(row.get('Local', ''))[:18],
                    self._safe_str(row.get('Setor', ''))[:25],
                    self._safe_str(row.get('Marca', ''))[:18],
                    self._safe_str(row.get('Modelo', ''))[:22],
                    self._safe_str(row.get('BTU', ''))[:10],
                    self._safe_str(row.get('Data Manutenção', ''), 'N/A')[:10],
                    self._safe_str(row.get('Próxima manutenção', ''), 'N/A')[:10],
                    self._safe_str(row.get('Técnico Executante', ''))[:22],
                    self._safe_str(row.get('Aprovação Supervisor', ''))[:22],
                    self._safe_str(row.get('Observações', ''), 'Nenhuma')[:60]
                ]
                
                for i, cell in enumerate(cells):
                    align = 'C' if i in [0, 5, 6, 7] else 'L'
                    pdf.cell(col_widths[i], 6, cell, 1, 0, align)
                pdf.ln()
            
            # Estatísticas
            self._add_statistics(pdf, data)
            
            # Rodapé
            pdf.ln(15)
            pdf.set_font("Arial", 'I', 8)
            pdf.cell(0, 10, "Sistema PMOC - AKR Brands", 0, 0, 'C')
            
            # Salvar
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            pdf.output(temp_file.name)
            
            self.logger.info(f"PDF gerado: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar PDF: {str(e)}")
            st.error(f"Erro ao gerar PDF: {str(e)}")
            return None
    
    def _safe_str(self, value: Any, default: str = '') -> str:
        """Converte valor para string com segurança"""
        if pd.isna(value) or value is None:
            return default
        return str(value)
    
    def _add_statistics(self, pdf: FPDF, data: pd.DataFrame) -> None:
        """Adiciona estatísticas ao relatório"""
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Estatísticas:", 0, 1)
        pdf.set_font("Arial", size=10)
        
        total = len(data)
        pdf.cell(0, 10, f"Total de Aparelhos: {total}", 0, 1)
        
        # Calcula estatísticas
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
            self.logger.warning(f"Erro ao calcular estatísticas: {str(e)}")
            pdf.cell(0, 10, "Erro ao calcular estatísticas", 0, 1)

# ============================================================
# COMPONENTES UI
# ============================================================

class UIComponents:
    """Componentes reutilizáveis da interface"""
    
    @staticmethod
    def show_device_details(device: Device) -> None:
        """Exibe detalhes de um aparelho"""
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Local:** {device.location}")
            st.write(f"**Setor:** {device.sector}")
        with col2:
            st.write(f"**Marca:** {device.brand}")
            st.write(f"**Modelo:** {device.model}")
        with col3:
            st.write(f"**BTU:** {device.btu}")
            status = device.get_maintenance_status()
            status_icons = {
                MaintenanceStatus.UP_TO_DATE: "✅",
                MaintenanceStatus.DUE_SOON: "⚠️",
                MaintenanceStatus.OVERDUE: "❌",
                MaintenanceStatus.NOT_SCHEDULED: "⏳",
                MaintenanceStatus.INVALID: "❓"
            }
            status_colors = {
                MaintenanceStatus.UP_TO_DATE: "green",
                MaintenanceStatus.DUE_SOON: "orange",
                MaintenanceStatus.OVERDUE: "red",
                MaintenanceStatus.NOT_SCHEDULED: "gray",
                MaintenanceStatus.INVALID: "red"
            }
            st.write(f"**Status:** {status_icons.get(status, '')} {status.value}")

# ============================================================
# PÁGINAS DA APLICAÇÃO
# ============================================================

def save_data() -> bool:
    """Função de conveniência para salvar dados"""
    state_manager = StateManager()
    return state_manager.save()

def show_consultation_page():
    """Página de consulta de aparelhos"""
    st.header("📊 Consulta de Aparelhos")
    
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
    
    # Preparar dados para exibição
    display_data = filtered_data.copy()
    
    def calculate_next_maintenance(row):
        if pd.notna(row['Data Manutenção']) and str(row['Data Manutenção']) != '':
            try:
                maintenance_date = datetime.strptime(str(row['Data Manutenção']), '%d/%m/%Y')
                next_maintenance = maintenance_date + timedelta(days=config.maintenance_interval_days)
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
        report_data = filtered_data[filtered_data['TAG'].isin(selected_tags)] if selected_tags else filtered_data
        title = f"Relatório de Aparelhos Selecionados ({len(report_data)} itens)" if selected_tags else f"Relatório Completo de Aparelhos ({len(report_data)} itens)"
        
        report_gen = ReportGenerator()
        pdf_file = report_gen.generate_pdf(report_data, title)
        
        if pdf_file:
            with open(pdf_file, "rb") as f:
                pdf_bytes = f.read()
            
            st.download_button(
                label="📥 Baixar Relatório PDF",
                data=pdf_bytes,
                file_name=f"relatorio_pmoc_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )
            
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
        hide_index=True,
        column_config={
            "TAG": "TAG",
            "Local": "Local",
            "Setor": "Setor",
            "Marca": "Marca",
            "Modelo": "Modelo",
            "BTU": "BTU",
            "Data Manutenção": st.column_config.TextColumn(
                "Data Manutenção",
                help="Data da última manutenção"
            ),
            "Próxima manutenção (calculada)": st.column_config.Column(
                "Próxima Manutenção",
                help=f"Calculada automaticamente como Data Manutenção + {config.maintenance_interval_days} dias"
            ),
            "Técnico Executante": "Técnico",
            "Aprovação Supervisor": "Aprovação",
            "Observações": "Observações"
        }
    )
    
    # Exportar CSV
    col1, col2 = st.columns(2)
    with col1:
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

def show_add_device_page():
    """Página para adicionar aparelho"""
    st.header("➕ Adicionar Novo Aparelho")
    
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            tag = st.number_input("TAG*", min_value=1, step=1)
            local = st.selectbox("Local*", config.LOCATIONS)
            setor = st.text_input("Setor*")
            marca = st.text_input("Marca*")
        with col2:
            modelo = st.text_input("Modelo")
            btu = st.number_input("BTU*", min_value=config.min_btu, max_value=config.max_btu, step=1000)
        
        st.markdown("(*) Campos obrigatórios")
        submitted = st.form_submit_button("Adicionar Aparelho", type="primary")
        
        if submitted:
            # Validações
            if tag in st.session_state.data['TAG'].values:
                st.error("❌ Já existe um aparelho com esta TAG!")
                return
            
            if not setor or not marca:
                st.error("❌ Preencha todos os campos obrigatórios!")
                return
            
            # Criar novo aparelho
            device = Device(
                tag=tag,
                location=local,
                sector=setor,
                brand=marca,
                model=modelo,
                btu=btu
            )
            
            is_valid, errors = device.validate()
            if not is_valid:
                for error in errors:
                    st.error(f"❌ {error}")
                return
            
            # Adicionar ao DataFrame
            new_row = device.to_dataframe_row()
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
            
            if save_data():
                st.success(f"✅ Aparelho TAG {tag} adicionado com sucesso!")
                st.balloons()
                st.rerun()

def show_edit_device_page():
    """Página para editar aparelho"""
    st.header("✏️ Editar Aparelho")
    
    if st.session_state.data.empty:
        st.warning("Não há aparelhos cadastrados para editar")
        return
    
    tag_to_edit = st.selectbox(
        "Selecione a TAG do aparelho a editar",
        st.session_state.data['TAG'].unique()
    )
    
    if tag_to_edit:
        row = st.session_state.data[st.session_state.data['TAG'] == tag_to_edit].iloc[0]
        device = Device.from_dataframe_row(row)
        
        UIComponents.show_device_details(device)
        
        st.markdown("---")
        
        with st.form("edit_form"):
            col1, col2 = st.columns(2)
            with col1:
                tag = st.number_input("TAG*", value=device.tag, min_value=1, step=1)
                local = st.selectbox("Local*", config.LOCATIONS, index=config.LOCATIONS.index(device.location))
                setor = st.text_input("Setor*", value=device.sector)
                marca = st.text_input("Marca*", value=device.brand)
            with col2:
                modelo = st.text_input("Modelo", value=device.model)
                btu = st.number_input("BTU*", value=device.btu, min_value=config.min_btu, max_value=config.max_btu, step=1000)
            
            st.markdown("(*) Campos obrigatórios")
            submitted = st.form_submit_button("Atualizar Aparelho", type="primary")
            
            if submitted:
                if not setor or not marca:
                    st.error("❌ Preencha todos os campos obrigatórios!")
                    return
                
                # Atualizar
                st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_edit, 'TAG'] = tag
                st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_edit, 'Local'] = local
                st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_edit, 'Setor'] = setor
                st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_edit, 'Marca'] = marca
                st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_edit, 'Modelo'] = modelo
                st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_edit, 'BTU'] = str(btu)
                
                if save_data():
                    st.success(f"✅ Aparelho TAG {tag} atualizado com sucesso!")
                    st.rerun()

def show_remove_device_page():
    """Página para remover aparelho"""
    st.header("🗑️ Remover Aparelho")
    
    if st.session_state.data.empty:
        st.warning("Não há aparelhos cadastrados para remover")
        return
    
    tag_to_remove = st.selectbox(
        "Selecione a TAG do aparelho a remover",
        st.session_state.data['TAG'].unique()
    )
    
    if tag_to_remove:
        row = st.session_state.data[st.session_state.data['TAG'] == tag_to_remove].iloc[0]
        device = Device.from_dataframe_row(row)
        
        st.warning("⚠️ Você está prestes a remover permanentemente este aparelho:")
        UIComponents.show_device_details(device)
        
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

def show_maintenance_page():
    """Página para registrar manutenção"""
    st.header("🔧 Registrar Manutenção")
    
    if st.session_state.data.empty:
        st.warning("Não há aparelhos cadastrados para registrar manutenção")
        return
    
    tag_to_maintain = st.selectbox(
        "Selecione a TAG do aparelho para registrar manutenção",
        st.session_state.data['TAG'].unique()
    )
    
    if tag_to_maintain:
        row = st.session_state.data[st.session_state.data['TAG'] == tag_to_maintain].iloc[0]
        device = Device.from_dataframe_row(row)
        
        st.markdown("**Aparelho selecionado:**")
        UIComponents.show_device_details(device)
        
        st.markdown("---")
        
        with st.form("maintenance_form"):
            maintenance_date = st.date_input(
                "Data da Manutenção*",
                format="DD/MM/YYYY"
            )
            
            technician = st.selectbox(
                "Técnico Executante*",
                config.TECHNICIANS,
                index=config.TECHNICIANS.index(device.technician) if device.technician in config.TECHNICIANS else 0
            )
            
            supervisor = st.text_input("Aprovação Supervisor", value=config.DEFAULT_SUPERVISOR)
            observations = st.text_area("Observações", value=device.observations)
            
            if maintenance_date:
                next_maintenance = maintenance_date + timedelta(days=config.maintenance_interval_days)
                st.info(f"📅 Próxima manutenção será agendada para: **{next_maintenance.strftime('%d/%m/%Y')}**")
            
            st.markdown("(*) Campos obrigatórios")
            submitted = st.form_submit_button("Registrar Manutenção", type="primary")
            
            if submitted:
                if not maintenance_date or not technician:
                    st.error("❌ Preencha todos os campos obrigatórios!")
                    return
                
                # Atualizar
                next_maintenance = maintenance_date + timedelta(days=config.maintenance_interval_days)
                
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

def show_configuration_page():
    """Página de configuração"""
    st.header("⚙️ Configuração")
    
    # Verificar senha
    if 'password_correct' not in st.session_state:
        st.session_state.password_correct = False
    
    if not st.session_state.password_correct:
        password = st.text_input("🔑 Digite a senha de acesso:", type="password")
        if password == "king@2025":
            st.session_state.password_correct = True
            st.success("✅ Acesso concedido!")
            st.rerun()
        elif password != "":
            st.error("❌ Senha incorreta!")
        st.stop()
    
    # Carrega configurações existentes
    data_manager = DataManager()
    config_data = data_manager.load_config()
    
    # Configuração do GitHub
    st.subheader("🔐 Configuração do GitHub")
    
    github_token = st.text_input(
        "Token de Acesso ao GitHub",
        type="password",
        value=config_data.get('github_token', ''),
        help="Obtenha em: GitHub > Settings > Developer Settings > Personal Access Tokens (classic)"
    )
    
    if st.button("💾 Salvar Configurações", type="primary"):
        config_data['github_token'] = github_token
        if data_manager.save_config(config_data):
            st.success("✅ Configurações salvas com sucesso!")
            
            # Tenta carregar dados do GitHub
            if github_token:
                saved_data = data_manager.load_from_github(github_token)
                if saved_data is not None:
                    state_manager = StateManager()
                    st.session_state.data = state_manager._ensure_columns(saved_data)
                    st.success("✅ Dados carregados do GitHub com sucesso!")
    
    # Sincronização
    st.subheader("🔄 Sincronização Manual")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Carregar do GitHub"):
            if github_token:
                data_manager = DataManager()
                saved_data = data_manager.load_from_github(github_token)
                if saved_data is not None:
                    state_manager = StateManager()
                    st.session_state.data = state_manager._ensure_columns(saved_data)
                    st.success("✅ Dados carregados do GitHub com sucesso!")
                else:
                    st.error("❌ Falha ao carregar dados do GitHub")
            else:
                st.error("❌ Token de acesso não configurado!")
    
    with col2:
        if st.button("📤 Salvar no GitHub"):
            if github_token:
                data_manager = DataManager()
                if data_manager.save_to_github(st.session_state.data, github_token):
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

# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def main():
    """Função principal da aplicação"""
    try:
        # Configuração da página
        st.set_page_config(
            page_title=config.page_title,
            page_icon=config.page_icon,
            layout=config.layout
        )
        
        # Inicializar dados
        state_manager = StateManager()
        state_manager.initialize()
        
        # Título
        st.title(f"{config.page_icon} PMOC - Plano de Manutenção, Operação e Controle - AKR Brands")
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
        st.sidebar.text(f"Versão 2.0 - {datetime.now().year}")
        st.sidebar.info(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
        st.error(f"❌ Ocorreu um erro inesperado: {str(e)}")
        st.error("Por favor, contate o suporte técnico.")

if __name__ == "__main__":
    main()
