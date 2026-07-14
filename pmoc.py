"""
PMOC - Plano de Manutenção, Operação e Controle
Versão: 3.1 - Corrigida
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import base64

# ============================================================
# CONFIGURAÇÕES
# ============================================================

PAGE_TITLE = "PMOC - Plano de Manutenção, Operação e Controle"
PAGE_ICON = "❄️"
MAINTENANCE_INTERVAL_DAYS = 180
LOCATIONS = ["Matriz", "Filial"]
TECHNICIANS = ["Guilherme", "Ismael"]
DEFAULT_SUPERVISOR = "Ismael"

# ============================================================
# FUNÇÕES DE DADOS
# ============================================================

def get_initial_data():
    """Cria dados iniciais de exemplo"""
    data = {
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
    df = pd.DataFrame(data)
    df['BTU'] = df['BTU'].astype(str)
    return df

# ============================================================
# INICIALIZAÇÃO
# ============================================================

def init_session_state():
    """Inicializa o estado da sessão"""
    if 'data' not in st.session_state:
        st.session_state.data = get_initial_data()
    
    if 'password_correct' not in st.session_state:
        st.session_state.password_correct = False

# ============================================================
# FUNÇÃO PARA GERAR RELATÓRIO HTML (SUBSTITUI O PDF)
# ============================================================

def generate_html_report(data, title="Relatório de Aparelhos"):
    """Gera um relatório em HTML que pode ser impresso como PDF"""
    try:
        if data is None or data.empty:
            return None
        
        # Calcular próxima manutenção para exibição
        display_data = data.copy()
        
        def calc_next(row):
            if pd.notna(row['Data Manutenção']) and str(row['Data Manutenção']) != '':
                try:
                    dt = datetime.strptime(str(row['Data Manutenção']), '%d/%m/%Y')
                    return (dt + timedelta(days=MAINTENANCE_INTERVAL_DAYS)).strftime('%d/%m/%Y')
                except:
                    return 'Data inválida'
            return 'Não agendado'
        
        display_data['Próxima Manutenção'] = display_data.apply(calc_next, axis=1)
        
        # Criar HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                }}
                h1 {{
                    color: #1E88E5;
                    text-align: center;
                }}
                h2 {{
                    color: #333;
                    text-align: center;
                    margin-top: 10px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .date {{
                    text-align: right;
                    color: #666;
                    font-size: 12px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 11px;
                }}
                th {{
                    background-color: #1E88E5;
                    color: white;
                    padding: 8px;
                    text-align: center;
                    border: 1px solid #ddd;
                }}
                td {{
                    padding: 6px;
                    border: 1px solid #ddd;
                    text-align: left;
                }}
                td.center {{
                    text-align: center;
                }}
                .stats {{
                    margin-top: 20px;
                    padding: 15px;
                    background-color: #f5f5f5;
                    border-radius: 5px;
                }}
                .stats h3 {{
                    margin-top: 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    color: #666;
                    font-size: 11px;
                    border-top: 1px solid #ddd;
                    padding-top: 15px;
                }}
                .btn-print {{
                    background-color: #1E88E5;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                    margin: 20px auto;
                    display: block;
                }}
                .btn-print:hover {{
                    background-color: #1565C0;
                }}
                @media print {{
                    .btn-print {{
                        display: none;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>❄️ PMOC - Plano de Manutenção, Operação e Controle</h1>
                <h2>{title}</h2>
                <div class="date">Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
            </div>
            
            <button class="btn-print" onclick="window.print()">🖨️ Imprimir / Salvar como PDF</button>
            
            <table>
                <thead>
                    <tr>
                        <th>TAG</th>
                        <th>Local</th>
                        <th>Setor</th>
                        <th>Marca</th>
                        <th>Modelo</th>
                        <th>BTU</th>
                        <th>Última Manut.</th>
                        <th>Próx. Manut.</th>
                        <th>Técnico</th>
                        <th>Aprovação</th>
                        <th>Observações</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for _, row in display_data.iterrows():
            html += f"""
                <tr>
                    <td class="center">{row['TAG']}</td>
                    <td>{row['Local']}</td>
                    <td>{row['Setor']}</td>
                    <td>{row['Marca']}</td>
                    <td>{row['Modelo']}</td>
                    <td class="center">{row['BTU']}</td>
                    <td class="center">{row['Data Manutenção'] if row['Data Manutenção'] != '' else 'N/A'}</td>
                    <td class="center">{row['Próxima Manutenção']}</td>
                    <td>{row['Técnico Executante'] if row['Técnico Executante'] != '' else '-'}</td>
                    <td>{row['Aprovação Supervisor'] if row['Aprovação Supervisor'] != '' else '-'}</td>
                    <td>{row['Observações'] if row['Observações'] != '' else 'Nenhuma'}</td>
                </tr>
            """
        
        # Estatísticas
        total = len(display_data)
        with_maintenance = len(display_data[display_data['Data Manutenção'] != ''])
        overdue = 0
        for _, row in display_data.iterrows():
            if row['Próxima Manutenção'] not in ['Não agendado', 'Data inválida']:
                try:
                    dt = datetime.strptime(row['Próxima Manutenção'], '%d/%m/%Y')
                    if dt < datetime.now():
                        overdue += 1
                except:
                    pass
        
        html += f"""
                </tbody>
            </table>
            
            <div class="stats">
                <h3>📊 Estatísticas</h3>
                <p><strong>Total de Aparelhos:</strong> {total}</p>
                <p><strong>Com manutenção registrada:</strong> {with_maintenance}</p>
                <p><strong>Manutenções atrasadas:</strong> {overdue}</p>
                <p><strong>Sem manutenção agendada:</strong> {total - with_maintenance}</p>
            </div>
            
            <div class="footer">
                <p>Sistema PMOC - AKR Brands</p>
                <p>Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        st.error(f"Erro ao gerar relatório: {str(e)}")
        return None

# ============================================================
# PÁGINA DE CONSULTA
# ============================================================

def show_consulta():
    """Página de consulta"""
    try:
        st.header("📊 Consulta de Aparelhos")
        
        df = st.session_state.data
        
        if df is None or df.empty:
            st.warning("Nenhum dado disponível")
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
        
        def calc_next(row):
            if pd.notna(row['Data Manutenção']) and str(row['Data Manutenção']) != '':
                try:
                    dt = datetime.strptime(str(row['Data Manutenção']), '%d/%m/%Y')
                    return (dt + timedelta(days=MAINTENANCE_INTERVAL_DAYS)).strftime('%d/%m/%Y')
                except:
                    return 'data inválida'
            return 'aguardando programação'
        
        display_data['Próxima manutenção (calculada)'] = display_data.apply(calc_next, axis=1)
        
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
        
        # ============================================================
        # GERAR RELATÓRIO (SUBSTITUI O PDF)
        # ============================================================
        st.subheader("📄 Gerar Relatório")
        
        selected_tags = st.multiselect(
            "Selecione os aparelhos para incluir no relatório (deixe vazio para todos)",
            options=filtered_data['TAG'].unique()
        )
        
        if st.button("Gerar Relatório", type="primary"):
            with st.spinner("Gerando relatório..."):
                if selected_tags:
                    report_data = filtered_data[filtered_data['TAG'].isin(selected_tags)]
                    title = f"Relatório de Aparelhos Selecionados ({len(report_data)} itens)"
                else:
                    report_data = filtered_data
                    title = f"Relatório Completo de Aparelhos ({len(report_data)} itens)"
                
                html_report = generate_html_report(report_data, title)
                
                if html_report:
                    # Criar link para download do HTML
                    b64 = base64.b64encode(html_report.encode()).decode()
                    href = f'data:text/html;base64,{b64}'
                    
                    st.markdown(f"""
                    <div style="text-align: center; padding: 20px;">
                        <p style="color: green; font-size: 16px;">✅ Relatório gerado com sucesso!</p>
                        <p>Clique no botão abaixo para abrir o relatório. No navegador, use <strong>Ctrl+P</strong> ou <strong>Cmd+P</strong> para salvar como PDF.</p>
                        <a href="{href}" download="relatorio_pmoc_{datetime.now().strftime('%Y%m%d_%H%M')}.html" target="_blank">
                            <button style="background-color: #1E88E5; color: white; padding: 12px 30px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer;">
                                📥 Baixar Relatório (HTML)
                            </button>
                        </a>
                        <p style="font-size: 12px; color: #666; margin-top: 10px;">
                            💡 Após abrir o relatório, clique em "Imprimir" e escolha "Salvar como PDF"
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Exportar CSV
        st.download_button(
            label="📥 Exportar para CSV",
            data=df.to_csv(index=False).encode('utf-8'),
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
            except:
                st.metric("Manutenções Atrasadas", 0)
                
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")
        import traceback
        with st.expander("Detalhes do erro"):
            st.code(traceback.format_exc())

# ============================================================
# PÁGINA DE CONFIGURAÇÃO (SIMPLIFICADA E CORRIGIDA)
# ============================================================

def show_configuracao():
    """Página de configuração - Simplificada"""
    try:
        st.header("⚙️ Configuração")
        
        # Verificar senha
        if not st.session_state.password_correct:
            password = st.text_input("🔑 Digite a senha de acesso:", type="password")
            if password == "king@2025":
                st.session_state.password_correct = True
                st.success("✅ Acesso concedido!")
                st.rerun()
            elif password != "":
                st.error("❌ Senha incorreta!")
            return
        
        st.success("✅ Configuração carregada com sucesso!")
        
        # Menu de operações
        opcao = st.radio(
            "Selecione a operação",
            ["Adicionar Aparelho", "Editar Aparelho", "Remover Aparelho", "Realizar Manutenção"]
        )
        
        df = st.session_state.data
        
        # ============================================================
        # ADICIONAR
        # ============================================================
        if opcao == "Adicionar Aparelho":
            st.subheader("➕ Adicionar Novo Aparelho")
            with st.form("add_form"):
                col1, col2 = st.columns(2)
                with col1:
                    tag = st.number_input("TAG*", min_value=1, step=1)
                    local = st.selectbox("Local*", LOCATIONS)
                    setor = st.text_input("Setor*")
                with col2:
                    marca = st.text_input("Marca*")
                    modelo = st.text_input("Modelo")
                    btu = st.number_input("BTU*", min_value=0, step=1000)
                
                submitted = st.form_submit_button("Adicionar", type="primary")
                
                if submitted:
                    if tag in df['TAG'].values:
                        st.error("❌ TAG já existe!")
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
                        st.session_state.data = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        st.success(f"✅ Aparelho TAG {tag} adicionado!")
                        st.balloons()
                        st.rerun()
        
        # ============================================================
        # EDITAR
        # ============================================================
        elif opcao == "Editar Aparelho":
            st.subheader("✏️ Editar Aparelho")
            if df.empty:
                st.warning("Não há aparelhos cadastrados")
                return
            
            tag = st.selectbox("Selecione a TAG", df['TAG'].unique())
            if tag:
                row = df[df['TAG'] == tag].iloc[0]
                with st.form("edit_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        local = st.selectbox("Local", LOCATIONS, index=LOCATIONS.index(row['Local']))
                        setor = st.text_input("Setor", value=row['Setor'])
                    with col2:
                        marca = st.text_input("Marca", value=row['Marca'])
                        modelo = st.text_input("Modelo", value=row['Modelo'])
                        btu_value = int(row['BTU']) if str(row['BTU']).isdigit() else 0
                        btu = st.number_input("BTU", value=btu_value, min_value=0)
                    
                    if st.form_submit_button("Atualizar", type="primary"):
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag, 'Local'] = local
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag, 'Setor'] = setor
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag, 'Marca'] = marca
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag, 'Modelo'] = modelo
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag, 'BTU'] = str(btu)
                        st.success(f"✅ TAG {tag} atualizado!")
                        st.rerun()
        
        # ============================================================
        # REMOVER
        # ============================================================
        elif opcao == "Remover Aparelho":
            st.subheader("🗑️ Remover Aparelho")
            if df.empty:
                st.warning("Não há aparelhos cadastrados")
                return
            
            tag = st.selectbox("Selecione a TAG para remover", df['TAG'].unique())
            if tag:
                row = df[df['TAG'] == tag].iloc[0]
                st.warning(f"⚠️ Remover TAG {tag} - {row['Marca']} {row['Modelo']}")
                
                if st.button("Confirmar Remoção", type="primary"):
                    st.session_state.data = df[df['TAG'] != tag]
                    st.success(f"✅ TAG {tag} removido!")
                    st.rerun()
        
        # ============================================================
        # MANUTENÇÃO
        # ============================================================
        elif opcao == "Realizar Manutenção":
            st.subheader("🔧 Registrar Manutenção")
            if df.empty:
                st.warning("Não há aparelhos cadastrados")
                return
            
            tag = st.selectbox("Selecione a TAG", df['TAG'].unique())
            if tag:
                row = df[df['TAG'] == tag].iloc[0]
                st.write(f"**Aparelho:** {row['Marca']} {row['Modelo']}")
                
                with st.form("maintenance_form"):
                    maintenance_date = st.date_input("Data da Manutenção*")
                    technician = st.selectbox("Técnico*", TECHNICIANS)
                    supervisor = st.text_input("Aprovação Supervisor", DEFAULT_SUPERVISOR)
                    observations = st.text_area("Observações", value=row['Observações'])
                    
                    if maintenance_date:
                        next_date = maintenance_date + timedelta(days=MAINTENANCE_INTERVAL_DAYS)
                        st.info(f"📅 Próxima: {next_date.strftime('%d/%m/%Y')}")
                    
                    if st.form_submit_button("Registrar", type="primary"):
                        next_date = maintenance_date + timedelta(days=MAINTENANCE_INTERVAL_DAYS)
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag, 'Data Manutenção'] = maintenance_date.strftime('%d/%m/%Y')
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag, 'Técnico Executante'] = technician
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag, 'Aprovação Supervisor'] = supervisor
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag, 'Próxima manutenção'] = next_date.strftime('%d/%m/%Y')
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag, 'Observações'] = observations
                        st.success(f"✅ Manutenção registrada!")
                        st.balloons()
                        st.rerun()
    
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")
        import traceback
        with st.expander("Detalhes do erro"):
            st.code(traceback.format_exc())

# ============================================================
# MAIN
# ============================================================

def main():
    """Função principal"""
    try:
        # Configurar página
        st.set_page_config(
            page_title=PAGE_TITLE,
            page_icon=PAGE_ICON,
            layout="wide"
        )
        
        # Inicializar
        init_session_state()
        
        # Título
        st.title(f"{PAGE_ICON} PMOC - Plano de Manutenção, Operação e Controle")
        st.markdown("Sistema de controle de manutenção preventiva de aparelhos de ar condicionado")
        
        # Menu
        menu = st.sidebar.radio(
            "📋 Menu Principal",
            ["📊 Consulta", "⚙️ Configuração"]
        )
        
        if menu == "📊 Consulta":
            show_consulta()
        else:
            show_configuracao()
        
        # Rodapé
        st.sidebar.markdown("---")
        st.sidebar.text("Desenvolvido por Robson Vilela")
        st.sidebar.text(f"Versão 3.1 - {datetime.now().year}")
        
    except Exception as e:
        st.error(f"❌ Erro principal: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
