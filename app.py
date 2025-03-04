import streamlit as st
import os
import google.generativeai as genai
from langchain.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFLoader

# Configure page
st.set_page_config(page_title="Quiz Generator", page_icon="📚")

# Initialize Gemini
GOOGLE_API_KEY = 'AIzaSyDLupuG-brZ4r7bTKuq66reKPPoUWi2_pM'
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

# Initialize session state
if 'ultima_resposta_correta' not in st.session_state:
    st.session_state.ultima_resposta_correta = None
if 'questao_atual' not in st.session_state:
    st.session_state.questao_atual = None
if 'resposta_correta_atual' not in st.session_state:
    st.session_state.resposta_correta_atual = None
if 'aguardando_resposta' not in st.session_state:
    st.session_state.aguardando_resposta = False
if 'documento' not in st.session_state:
    st.session_state.documento = ''

def carregar_documento():
    caminho = r'C:\Users\adail\Documents\Curso Python Asimov\quiz-generator\Linha do Tempo.pdf'
    loader = PyPDFLoader(caminho)
    lista_documentos = loader.load()
    
    documento = ''
    for doc in lista_documentos:
        documento += doc.page_content
    
    st.session_state.documento = documento

def gerar_prompt(informacoes, ultima_correta):
    return f"""Você é um assistente que gera questões de múltipla escolha. 
Use as seguintes informações como base para gerar as questões:
{informacoes}

Regras OBRIGATÓRIAS para gerar as questões:
1. Gere apenas UMA pergunta por vez
2. A questão DEVE ter 5 alternativas: A, B, C, D e E
3. A alternativa correta NÃO pode ser {ultima_correta} (que foi a resposta da última questão)
4. Você DEVE terminar SEMPRE com a resposta correta entre parênteses. Exemplo: (A) ou (B) ou (C)
5. Formate a questão assim:

PERGUNTA: [texto da pergunta]

A) [alternativa A]
B) [alternativa B]
C) [alternativa C]
D) [alternativa D]
E) [alternativa E]

([letra correta])
"""

def fazer_pergunta():
    prompt = gerar_prompt(st.session_state.documento, 
                         st.session_state.ultima_resposta_correta if st.session_state.ultima_resposta_correta else "Nenhuma")
    
    try:
        response = model.generate_content(prompt)
        response.resolve()
        conteudo = response.text
        
        import re
        match = re.search(r'\(([A-E])\)$', conteudo)
        if match:
            st.session_state.ultima_resposta_correta = match.group(1)
            st.session_state.questao_atual = conteudo.replace(f"({match.group(1)})", "")
            st.session_state.resposta_correta_atual = match.group(1)
            st.session_state.aguardando_resposta = True
            return True
    except Exception as e:
        st.error(f"Erro ao gerar questão: {str(e)}")
        return False

def main():
    st.title("📚 Quiz Generator")
    st.markdown("---")

    # Carregar documento se ainda não foi carregado
    if not st.session_state.documento:
        carregar_documento()

    # Botão para nova pergunta
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Nova Pergunta", use_container_width=True):
            fazer_pergunta()

    # Exibir questão atual
    if st.session_state.questao_atual:
        st.markdown("### Questão:")
        st.write(st.session_state.questao_atual)
        
        # Input para resposta
        resposta = st.radio("Selecione sua resposta:", 
                           options=['A', 'B', 'C', 'D', 'E'],
                           horizontal=True)
        
        # Botão para verificar resposta
        if st.button("Verificar Resposta", use_container_width=True):
            if resposta == st.session_state.resposta_correta_atual:
                st.success(f"✅ CORRETO! A resposta é ({st.session_state.resposta_correta_atual})")
            else:
                st.error(f"❌ INCORRETO! A resposta correta é ({st.session_state.resposta_correta_atual})")

if __name__ == "__main__":
    main()
