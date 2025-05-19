import streamlit as st
import pandas as pd
import datetime
import os

# Função para carregar os dados do arquivo Excel
def carregar_dados(caminho_arquivo):
    if os.path.exists(caminho_arquivo):
        return pd.read_excel(caminho_arquivo)
    else:
        return pd.DataFrame(columns=["Equipamento", "Última Manutenção", "Próxima Manutenção"])

# Função para salvar os dados no arquivo Excel
def salvar_dados(caminho_arquivo, dados):
    dados.to_excel(caminho_arquivo, index=False)

# Caminho do arquivo Excel
caminho_arquivo = "dados_manutencao.xlsx"

# Título da aplicação
st.title("Controle de Manutenção de Equipamentos")

# Carregar dados
dados = carregar_dados(caminho_arquivo)

# Páginas do aplicativo
pagina = st.sidebar.selectbox("Selecione a página", ["Página Principal", "Realizar Manutenção", "Adicionar Equipamento"])

# Página Principal
if pagina == "Página Principal":
    st.header("Página Principal")
    if not dados.empty:
        st.dataframe(dados)
    else:
        st.info("Nenhum dado de manutenção disponível.")

# Página para realizar manutenção
elif pagina == "Realizar Manutenção":
    st.header("Realizar Manutenção")

    if dados.empty:
        st.info("Nenhum equipamento cadastrado.")
    else:
        equipamento = st.selectbox("Selecione o equipamento", dados["Equipamento"])
        if st.button("Registrar Manutenção"):
            hoje = datetime.date.today()
            proxima_manutencao = hoje + datetime.timedelta(days=180)

            # Atualizar os dados na tabela
            dados.loc[dados["Equipamento"] == equipamento, "Última Manutenção"] = hoje
            dados.loc[dados["Equipamento"] == equipamento, "Próxima Manutenção"] = proxima_manutencao

            # Salvar os dados atualizados
            salvar_dados(caminho_arquivo, dados)

            st.success(f"Manutenção registrada para {equipamento} em {hoje.strftime('%d/%m/%Y')}")
            st.info(f"Próxima manutenção será automaticamente agendada para: {proxima_manutencao.strftime('%d/%m/%Y')}")

# Página para adicionar novo equipamento
elif pagina == "Adicionar Equipamento":
    st.header("Adicionar Novo Equipamento")
    novo_equipamento = st.text_input("Nome do equipamento")
    if st.button("Adicionar"):
        if novo_equipamento.strip() == "":
            st.warning("O nome do equipamento não pode estar vazio.")
        elif novo_equipamento in dados["Equipamento"].values:
            st.warning("Este equipamento já está cadastrado.")
        else:
            hoje = datetime.date.today()
            proxima_manutencao = hoje + datetime.timedelta(days=180)
            novo_dado = pd.DataFrame([[novo_equipamento, hoje, proxima_manutencao]], columns=dados.columns)
            dados = pd.concat([dados, novo_dado], ignore_index=True)
            salvar_dados(caminho_arquivo, dados)
            st.success(f"Equipamento '{novo_equipamento}' adicionado com sucesso.")
            st.info(f"Primeira manutenção agendada para: {proxima_manutencao.strftime('%d/%m/%Y')}")

# Rodapé
st.markdown("---")
st.caption("Sistema de Controle de Manutenção • Desenvolvido com Streamlit")

# Exibe a data e hora da última modificação do arquivo (se existir)
if os.path.exists(caminho_arquivo):
    ultima_modificacao = datetime.datetime.fromtimestamp(os.path.getmtime(caminho_arquivo))
    st.markdown(f"📅 Última atualização dos dados: {ultima_modificacao.strftime('%d/%m/%Y %H:%M:%S')}")

# Permite ao usuário baixar a planilha atualizada
if not dados.empty:
    st.download_button(
        label="📥 Baixar planilha atualizada",
        data=dados.to_excel(index=False, engine='openpyxl'),
        file_name="dados_manutencao_atualizado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
