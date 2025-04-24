# [Código anterior permanece igual até a função generate_pdf_report]

def generate_pdf_report(data, title="Relatório de Aparelhos"):
    pdf = FPDF(orientation='L')  # Landscape orientation
    pdf.add_page()
    pdf.set_font("Arial", size=9)  # Reduzi o tamanho base da fonte para 9
    
    # Ajuste do fuso horário
    tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(tz)
    
    # Header with company name
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt="PMOC - Plano de Manutenção, Operação e Controle - AKR Brands", ln=1, align='C')
    pdf.ln(5)
    
    # Report title
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt=title, ln=1, align='C')
    pdf.ln(5)
    
    # Date and time - COM FUSO HORÁRIO CORRIGIDO
    pdf.set_font("Arial", 'I', 9)
    pdf.cell(0, 10, txt=f"Gerado em: {now.strftime('%d/%m/%Y %H:%M')}", ln=1, align='R')
    pdf.ln(8)
    
    # Table header - AJUSTEI AS LARGURAS DAS COLUNAS
    pdf.set_font("Arial", 'B', 9)
    col_widths = [10, 18, 32, 22, 30, 10, 25, 25, 22, 22]  # Aumentei as colunas de datas
    headers = ["TAG", "Local", "Setor", "Marca", "Modelo", "BTU", "Última Manut.", 
               "Próx. Manut.", "Técnico", "Aprovação"]
    
    # Header row
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, txt=header, border=1, align='C')  # Reduzi a altura
    pdf.ln()
    
    # Table content - COM FONTE MENOR
    pdf.set_font("Arial", size=8)  # Fonte menor para o conteúdo
    for _, row in data.iterrows():
        # Handle NaN/None values
        tag = str(row['TAG']) if pd.notna(row['TAG']) else ''
        local = str(row['Local']) if pd.notna(row['Local']) else ''
        setor = str(row['Setor']) if pd.notna(row['Setor']) else ''
        marca = str(row['Marca']) if pd.notna(row['Marca']) else ''
        modelo = str(row['Modelo']) if pd.notna(row['Modelo']) else ''
        btu = str(row['BTU']) if pd.notna(row['BTU']) else ''
        
        # Formata datas para garantir que caberão
        data_manut = str(row['Data Manutenção'])[:10] if pd.notna(row['Data Manutenção']) else ''
        prox_manut = str(row['Próxima manutenção'])[:10] if pd.notna(row['Próxima manutenção']) else ''
        
        tecnico = str(row['Técnico Executante'])[:15] if pd.notna(row['Técnico Executante']) else ''  # Limita tamanho
        aprovacao = str(row['Aprovação Supervisor'])[:15] if pd.notna(row['Aprovação Supervisor']) else ''
        
        pdf.cell(col_widths[0], 6, txt=tag, border=1, align='C')  # Altura reduzida
        pdf.cell(col_widths[1], 6, txt=local, border=1)
        pdf.cell(col_widths[2], 6, txt=setor, border=1)
        pdf.cell(col_widths[3], 6, txt=marca, border=1)
        pdf.cell(col_widths[4], 6, txt=modelo, border=1)
        pdf.cell(col_widths[5], 6, txt=btu, border=1, align='C')
        pdf.cell(col_widths[6], 6, txt=data_manut, border=1, align='C')
        pdf.cell(col_widths[7], 6, txt=prox_manut, border=1, align='C')
        pdf.cell(col_widths[8], 6, txt=tecnico, border=1)
        pdf.cell(col_widths[9], 6, txt=aprovacao, border=1)
        pdf.ln()

    # [Restante da função permanece igual...]

# [Restante do código permanece igual]
