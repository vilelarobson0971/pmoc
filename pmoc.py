import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz

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

# Function to save data (in a real app, this would save to a database)
def save_data():
    st.session_state.data.to_csv('pmoc_data.csv', index=False)
    st.success("Dados salvos com sucesso!")

# Try to load saved data
try:
    saved_data = pd.read_csv('pmoc_data.csv')
    st.session_state.data = saved_data
except:
    pass

# Main app
def main():
    st.title("❄️ PMOC - Plano de Manutenção, Operação e Controle")
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
        st.header("Adicionar Novo Aparelho")
        
        with st.form("add_form"):
            col1, col2 = st.columns(2)
            with col1:
                tag = st.number_input("TAG*", min_value=1, step=1)
                local = st.selectbox("Local*", ["Matriz", "Filial"])
                setor = st.text_input("Setor*")
                marca = st.text_input("Marca*")
            with col2:
                modelo = st.text_input("Modelo")
                btu = st.number_input("BTU*", min_value=0, step=1000)
                data_manutencao = st.date_input("Data da Manutenção")
                tecnico = st.text_input("Técnico Executante")
                aprovacao = st.text_input("Aprovação Supervisor")
            
            st.markdown("(*) Campos obrigatórios")
            
            if st.form_submit_button("Adicionar Aparelho"):
                if tag in st.session_state.data['TAG'].values:
                    st.error("Já existe um aparelho com esta TAG!")
                elif not tag or not local or not setor or not marca or not btu:
                    st.error("Preencha todos os campos obrigatórios!")
                else:
                    proxima_manutencao = data_manutencao + timedelta(days=180) if data_manutencao else ''
                    new_row = {
                        'TAG': tag,
                        'Local': local,
                        'Setor': setor,
                        'Marca': marca,
                        'Modelo': modelo,
                        'BTU': btu,
                        'Data Manutenção': data_manutencao.strftime('%d/%m/%Y') if data_manutencao else '',
                        'Técnico Executante': tecnico,
                        'Aprovação Supervisor': aprovacao,
                        'Próxima manutenção': proxima_manutencao.strftime('%d/%m/%Y') if data_manutencao else ''
                    }
                    st.session_state.data = pd.concat([
                        st.session_state.data, 
                        pd.DataFrame([new_row])
                    ], ignore_index=True)
                    save_data()
                    st.success("Aparelho adicionado com sucesso!")
                    st.rerun()
    
    elif menu == "Editar Aparelho":
        st.header("Editar Aparelho Existente")
        
        tag_to_edit = st.selectbox(
            "Selecione a TAG do aparelho a editar",
            st.session_state.data['TAG'].unique()
        )
        
        if tag_to_edit:
            aparelho_data = st.session_state.data[st.session_state.data['TAG'] == tag_to_edit].iloc[0]
            
            with st.form("edit_form"):
                col1, col2 = st.columns(2)
                with col1:
                    tag = st.number_input("TAG*", value=int(aparelho_data['TAG']), min_value=1, step=1)
                    local = st.selectbox(
                        "Local*", 
                        ["Matriz", "Filial"], 
                        index=0 if aparelho_data['Local'] == "Matriz" else 1
                    )
                    setor = st.text_input("Setor*", value=aparelho_data['Setor'])
                    marca = st.text_input("Marca*", value=aparelho_data['Marca'])
                with col2:
                    modelo = st.text_input("Modelo", value=aparelho_data['Modelo'])
                    btu = st.number_input("BTU*", value=int(aparelho_data['BTU']), min_value=0, step=1000)
                    data_manutencao = st.date_input(
                        "Data da Manutenção",
                        value=datetime.strptime(aparelho_data['Data Manutenção'], '%d/%m/%Y') if aparelho_data['Data Manutenção'] else datetime.now()
                    )
                    tecnico = st.text_input("Técnico Executante", value=aparelho_data['Técnico Executante'])
                    aprovacao = st.text_input("Aprovação Supervisor", value=aparelho_data['Aprovação Supervisor'])
                
                st.markdown("(*) Campos obrigatórios")
                
                if st.form_submit_button("Atualizar Aparelho"):
                    if not tag or not local or not setor or not marca or not btu:
                        st.error("Preencha todos os campos obrigatórios!")
                    else:
                        proxima_manutencao = data_manutencao + timedelta(days=180) if data_manutencao else ''
                        updated_data = {
                            'TAG': tag,
                            'Local': local,
                            'Setor': setor,
                            'Marca': marca,
                            'Modelo': modelo,
                            'BTU': btu,
                            'Data Manutenção': data_manutencao.strftime('%d/%m/%Y') if data_manutencao else '',
                            'Técnico Executante': tecnico,
                            'Aprovação Supervisor': aprovacao,
                            'Próxima manutenção': proxima_manutencao.strftime('%d/%m/%Y') if data_manutencao else ''
                        }
                        
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_edit] = pd.Series(updated_data)
                        save_data()
                        st.success("Aparelho atualizado com sucesso!")
                        st.rerun()
    
    elif menu == "Remover Aparelho":
        st.header("Remover Aparelho")
        
        tag_to_remove = st.selectbox(
            "Selecione a TAG do aparelho a remover",
            st.session_state.data['TAG'].unique()
        )
        
        if tag_to_remove:
            aparelho_data = st.session_state.data[st.session_state.data['TAG'] == tag_to_remove].iloc[0]
            
            st.warning(f"Você está prestes a remover o aparelho com TAG {tag_to_remove}:")
            st.write(f"Local: {aparelho_data['Local']}")
            st.write(f"Setor: {aparelho_data['Setor']}")
            st.write(f"Marca/Modelo: {aparelho_data['Marca']} {aparelho_data['Modelo']}")
            
            if st.button("Confirmar Remoção"):
                st.session_state.data = st.session_state.data[st.session_state.data['TAG'] != tag_to_remove]
                save_data()
                st.success("Aparelho removido com sucesso!")
                st.rerun()
    
    elif menu == "Realizar Manutenção":
        st.header("Registrar Manutenção")
        
        tag_to_maintain = st.selectbox(
            "Selecione a TAG do aparelho para registrar manutenção",
            st.session_state.data['TAG'].unique()
        )
        
        if tag_to_maintain:
            aparelho_data = st.session_state.data[st.session_state.data['TAG'] == tag_to_maintain].iloc[0]
            
            with st.form("maintenance_form"):
                st.write(f"**Aparelho selecionado:** TAG {tag_to_maintain} - {aparelho_data['Marca']} {aparelho_data['Modelo']}")
                st.write(f"**Localização:** {aparelho_data['Local']} - {aparelho_data['Setor']}")
                
                data_manutencao = st.date_input(
                    "Data da Manutenção*",
                    value=datetime.now()
                )
                tecnico = st.text_input("Técnico Executante*", value=aparelho_data['Técnico Executante'])
                aprovacao = st.text_input("Aprovação Supervisor", value=aparelho_data['Aprovação Supervisor'])
                observacoes = st.text_area("Observações")
                
                st.markdown("(*) Campos obrigatórios")
                
                if st.form_submit_button("Registrar Manutenção"):
                    if not data_manutencao or not tecnico:
                        st.error("Preencha todos os campos obrigatórios!")
                    else:
                        proxima_manutencao = data_manutencao + timedelta(days=180)
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_maintain, 'Data Manutenção'] = data_manutencao.strftime('%d/%m/%Y')
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_maintain, 'Técnico Executante'] = tecnico
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_maintain, 'Aprovação Supervisor'] = aprovacao
                        st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_maintain, 'Próxima manutenção'] = proxima_manutencao.strftime('%d/%m/%Y')
                        
                        save_data()
                        st.success(f"Manutenção para TAG {tag_to_maintain} registrada com sucesso!")
                        st.success(f"Próxima manutenção: {proxima_manutencao.strftime('%d/%m/%Y')}")
                        st.rerun()

if __name__ == "__main__":
    main()
