import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
from fpdf import FPDF
import tempfile
import os

# Set page config
st.set_page_config(
    page_title="PMOC - Plano de Manutenção, Operação e Controle",
    page_icon="❄️",
    layout="wide"
)

# Initialize session state for data
if 'data' not in st.session_state:
    # Load initial data from the provided Excel
    initial_data = {
        'TAG': list(range(1, 42)),  # Tags from 1 to 41
        'Local': ['Matriz']*20 + ['Filial']*13 + ['Matriz']*8,
        'Setor': [
            'Recepção', 'CPD', 'CPD', 'RH', 'Marketing', 'Marketing', 'Inteligência de mercado',
            'Antigo Show Room', 'Diretoria - Rafael', 'Controladoria', 'Diretoria - Jair',
            'Sala reunião térreo', 'Financeiro', 'Diretoria', 'Sala reunião principal',
            'Sala reunião principal', 'Expedição - Recepção', 'Expedição - Sala Welder',
            'Corte - Risco', 'Estoque - Sala Umberto', 'Laboratório - Sala ADM',
            'Laboratório - Sala ADM', 'Gerência', 'Modelagem', 'Inteligência do Produto',
            'Estilo', 'Show Room', 'T.I.', 'PCP', 'PCP', 'Compras', 'Refeitório', 'Refeitório',
            'Refeitório', 'Sala de Reunião', 'Estúdio', 'Estúdio', 'Refeitório', 'Refeitório',
            'Sala Expedição Kids', 'Ecommerce'
        ],
        'Marca': [
            'Springer', 'Philco', 'Elgin', 'Springer', 'TCL', 'TCL', 'TCL', 'Springer',
            'Springer', 'Springer', 'COMFEE', 'COMFEE', 'Springer', 'Springer', 'Springer',
            'Springer', 'Philco', 'Agratto', 'COMFEE', 'GREE', 'GREE', 'GREE', 'GREE', 'GREE',
            'GREE', 'GREE', 'GREE', 'Consul', 'Electrolux', 'GREE', 'Philco', 'GREE', 'GREE',
            'GREE', 'GREE', 'Philco', 'Springer', 'Agratto', 'Agratto', '', ''
        ],
        'Modelo': [
            '42MACA12S5', 'Eco Inverter', 'HWFL18B2IA', '42MACB18S5', 'TAC18CSA1', 'TAC18CSA1',
            'TAC18CSA1', '42MACB18S5', '42AFFCL12', '42MACB18S5', '42AFCE12X5', '42AFCD18F5',
            '42MACB18S5', '42TFCA', '42MACB18S5', '42MACB18S5', 'Eco Inverter', 'ACST12FR4-02',
            '42AFCD12F5', 'GWC12QC-D3NNB4D/I', 'GWC18AAD-D3NNA1D/I', 'GWC18AAD-D3NNA1D/I',
            'GWC12AAC-D3NNB4D/I', 'GWC12AAC-D3NNB4D/I', 'GWC24QE-D3NNB4D/I', 'GWC24QE-D3NNB4D/I',
            'GWC24QE-D3NNB4D/I', '', 'VI18F', 'GWC12QC-D3NNB4D/I', 'Eco Inverter',
            'GWC24QE-D3NNB4D/I', 'GWC24QE-D3NNB4D/I', 'GWC24QE-D3NNB4D/I', 'GWC24QE-D3NNB4D/I',
            '', '', 'LCS24F-02', 'LCS24F-02', '', ''
        ],
        'BTU': [
            12000, 12000, 18000, 18000, 18000, 18000, 18000, 18000, 12000, 18000, 12000, 18000,
            18000, 12000, 18000, 18000, 18000, 12000, 12000, 12000, 18000, 18000, 12000, 12000,
            24000, 24000, 24000, 12000, 18000, 12000, 12000, 24000, 24000, 24000, 24000, 24000,
            24000, 24000, 24000, 0, 12000
        ],
        'Data Manutenção': ['']*41,
        'Técnico Executante': ['']*41,
        'Aprovação Supervisor': ['']*41,
        'Próxima manutenção': ['']*41
    }
    st.session_state.data = pd.DataFrame(initial_data)
    st.session_state.data['BTU'] = st.session_state.data['BTU'].astype(str)

# Function to save data
def save_data():
    st.session_state.data.to_csv('pmoc_data.csv', index=False)
    st.success("Dados salvos com sucesso!")

# Try to load saved data
try:
    saved_data = pd.read_csv('pmoc_data.csv')
    st.session_state.data = saved_data
except:
    pass

# Function to generate PDF report in landscape format
def generate_pdf_report(data, title="Relatório de Aparelhos"):
    pdf = FPDF(orientation='L')  # Landscape orientation
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # Header with company name
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt="PMOC - Plano de Manutenção, Operação e Controle - AKR Brands", ln=1, align='C')
    pdf.ln(5)
    
    # Report title
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt=title, ln=1, align='C')
    pdf.ln(5)
    
    # Date and time
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, txt=f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1, align='R')
    pdf.ln(10)
    
    # Table header
    pdf.set_font("Arial", 'B', 10)
    col_widths = [12, 20, 40, 25, 35, 12, 20, 20, 25, 25]  # Adjusted widths for landscape
    headers = ["TAG", "Local", "Setor", "Marca", "Modelo", "BTU", "Última Manut.", 
               "Próxima Manut.", "Técnico", "Aprovação"]
    
    # Header row
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, txt=header, border=1, align='C')
    pdf.ln()
    
    # Table content
    pdf.set_font("Arial", size=8)
    for _, row in data.iterrows():
        # Handle NaN/None values
        tag = str(row['TAG']) if pd.notna(row['TAG']) else ''
        local = str(row['Local']) if pd.notna(row['Local']) else ''
        setor = str(row['Setor']) if pd.notna(row['Setor']) else ''
        marca = str(row['Marca']) if pd.notna(row['Marca']) else ''
        modelo = str(row['Modelo']) if pd.notna(row['Modelo']) else ''
        btu = str(row['BTU']) if pd.notna(row['BTU']) else ''
        data_manut = str(row['Data Manutenção']) if pd.notna(row['Data Manutenção']) else ''
        prox_manut = str(row['Próxima manutenção']) if pd.notna(row['Próxima manutenção']) else ''
        tecnico = str(row['Técnico Executante']) if pd.notna(row['Técnico Executante']) else ''
        aprovacao = str(row['Aprovação Supervisor']) if pd.notna(row['Aprovação Supervisor']) else ''
        
        pdf.cell(col_widths[0], 8, txt=tag, border=1, align='C')
        pdf.cell(col_widths[1], 8, txt=local, border=1)
        pdf.cell(col_widths[2], 8, txt=setor, border=1)
        pdf.cell(col_widths[3], 8, txt=marca, border=1)
        pdf.cell(col_widths[4], 8, txt=modelo, border=1)
        pdf.cell(col_widths[5], 8, txt=btu, border=1, align='C')
        pdf.cell(col_widths[6], 8, txt=data_manut, border=1, align='C')
        pdf.cell(col_widths[7], 8, txt=prox_manut, border=1, align='C')
        pdf.cell(col_widths[8], 8, txt=tecnico, border=1)
        pdf.cell(col_widths[9], 8, txt=aprovacao, border=1)
        pdf.ln()
    
    # Statistics section
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Estatísticas:", ln=1)
    pdf.set_font("Arial", size=10)
    
    total = len(data)
    pdf.cell(0, 10, txt=f"Total de Aparelhos: {total}", ln=1)
    
    try:
        next_maintenance = len(data[data['Próxima manutenção'] != ''])
        pdf.cell(0, 10, txt=f"Com próxima manutenção agendada: {next_maintenance}", ln=1)
        
        overdue = data[
            (data['Próxima manutenção'] != '') & 
            (pd.to_datetime(data['Próxima manutenção'], errors='coerce', dayfirst=True) < datetime.now())
        ]
        pdf.cell(0, 10, txt=f"Manutenções atrasadas: {len(overdue)}", ln=1)
    except Exception as e:
        pdf.cell(0, 10, txt=f"Erro ao calcular estatísticas: {str(e)}", ln=1)
    
    # Footer
    pdf.ln(15)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, txt="Sistema PMOC - AKR Brands", ln=1, align='C')
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    return temp_file.name

def main():
    try:
        st.title("❄️ PMOC - Plano de Manutenção, Operação e Controle - AKR Brands")
        st.markdown("Controle de manutenção preventiva de aparelhos de ar condicionado")
        
        # Navigation
        menu = st.sidebar.selectbox("Menu", ["Consulta", "Adicionar Aparelho", "Editar Aparelho", "Remover Aparelho", "Realizar Manutenção"])
        
        if menu == "Consulta":
            st.header("Consulta de Aparelhos")
            
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                local_filter = st.selectbox("Local", ["Todos"] + list(st.session_state.data['Local'].unique()))
            with col2:
                setor_filter = st.selectbox("Setor", ["Todos"] + list(st.session_state.data['Setor'].unique()))
            with col3:
                marca_filter = st.selectbox("Marca", ["Todos"] + list(st.session_state.data['Marca'].unique()))
            
            # Apply filters
            filtered_data = st.session_state.data.copy()
            if local_filter != "Todos":
                filtered_data = filtered_data[filtered_data['Local'] == local_filter]
            if setor_filter != "Todos":
                filtered_data = filtered_data[filtered_data['Setor'] == setor_filter]
            if marca_filter != "Todos":
                filtered_data = filtered_data[filtered_data['Marca'] == marca_filter]
            
            # PDF Report Section
            st.subheader("Gerar Relatório em PDF")
            selected_tags = st.multiselect(
                "Selecione os aparelhos para incluir no relatório (deixe vazio para todos)",
                options=filtered_data['TAG'].unique()
            )
            
            if st.button("Gerar Relatório PDF"):
                try:
                    if selected_tags:
                        report_data = filtered_data[filtered_data['TAG'].isin(selected_tags)]
                        title = f"Relatório de Aparelhos Selecionados ({len(report_data)} itens)"
                    else:
                        report_data = filtered_data
                        title = f"Relatório Completo de Aparelhos ({len(report_data)} itens)"
                    
                    pdf_file = generate_pdf_report(report_data, title)
                    
                    with open(pdf_file, "rb") as f:
                        pdf_bytes = f.read()
                    
                    st.download_button(
                        label="Baixar Relatório PDF",
                        data=pdf_bytes,
                        file_name=f"relatorio_pmoc_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf"
                    )
                    
                    # Clean up
                    os.unlink(pdf_file)
                except Exception as e:
                    st.error(f"Erro ao gerar relatório PDF: {str(e)}")
            
            # Show data
            st.dataframe(
                filtered_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "TAG": "TAG",
                    "Local": "Local",
                    "Setor": "Setor",
                    "Marca": "Marca",
                    "Modelo": "Modelo",
                    "BTU": "BTU",
                    "Data Manutenção": st.column_config.DateColumn(
                        "Data Manutenção",
                        format="DD/MM/YYYY"
                    ),
                    "Técnico Executante": "Técnico",
                    "Aprovação Supervisor": "Aprovação",
                    "Próxima manutenção": st.column_config.DateColumn(
                        "Próxima Manutenção",
                        format="DD/MM/YYYY"
                    )
                }
            )
            
            # Export button
            st.download_button(
                label="Exportar para CSV",
                data=st.session_state.data.to_csv(index=False).encode('utf-8'),
                file_name='pmoc_export.csv',
                mime='text/csv'
            )
            
            # Statistics
            st.subheader("Estatísticas")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Aparelhos", len(filtered_data))
            with col2:
                st.metric("Próximas Manutenções", len(filtered_data[filtered_data['Próxima manutenção'] != '']))
            with col3:
                try:
                    overdue = filtered_data[
                        (filtered_data['Próxima manutenção'] != '') & 
                        (pd.to_datetime(filtered_data['Próxima manutenção'], errors='coerce', dayfirst=True) < datetime.now())
                    ]
                    st.metric("Manutenções Atrasadas", len(overdue), delta=f"-{len(overdue)}" if len(overdue) > 0 else None)
                except:
                    st.metric("Manutenções Atrasadas", 0)
        
        elif menu == "Adicionar Aparelho":
            # [Restante do código para outras opções de menu...]
            pass
        
        # [Demais opções do menu (Adicionar, Editar, Remover, Manutenção) permanecem iguais...]

    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {str(e)}")

if __name__ == "__main__":
    main()
