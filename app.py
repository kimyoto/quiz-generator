import streamlit as st
import os
import google.generativeai as genai
from langchain.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFLoader

# Configure page
st.set_page_config(page_title="Quiz Generator", page_icon="📚")

# Initialize Gemini with fallback
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except Exception as e:
    # Fallback to environment variable or hardcoded key (for development only)
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyDLupuG-brZ4r7bTKuq66reKPPoUWi2_pM')

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro')
except Exception as e:
    st.error(f"Error initializing Gemini: {str(e)}")
    st.stop()

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
if 'perguntas_anteriores' not in st.session_state:
    st.session_state.perguntas_anteriores = []

def carregar_documento():
    try:
        caminho = os.path.join(os.path.dirname(__file__), 'data', 'Linha do Tempo.pdf')
        loader = PyPDFLoader(caminho)
        lista_documentos = loader.load()
        
        documento = ''
        for doc in lista_documentos:
            documento += doc.page_content
        
        st.session_state.documento = documento
    except Exception as e:
        st.error(f"Error loading document: {str(e)}")
        st.stop()

def gerar_prompt(informacoes, ultima_correta):
    perguntas_anteriores = "\n".join(st.session_state.perguntas_anteriores)
    return f"""Você é um assistente que gera questões de múltipla escolha. 
Use as seguintes informações como base para gerar as questões:
{informacoes}

IMPORTANTE: NÃO gere nenhuma das perguntas abaixo que já foram feitas anteriormente:
{perguntas_anteriores}

Regras OBRIGATÓRIAS para gerar as questões:
1. Gere apenas UMA pergunta por vez
2. A questão DEVE ter 5 alternativas: A, B, C, D e E
3. A alternativa correta NÃO pode ser {ultima_correta} (que foi a resposta da última questão)
4. A pergunta DEVE ser diferente das perguntas anteriores listadas acima
5. Você DEVE terminar SEMPRE com a resposta correta entre parênteses. Exemplo: (A) ou (B) ou (C)
6. Formate a questão assim:

PERGUNTA: [texto da pergunta]

A) [alternativa A]
B) [alternativa B]
C) [alternativa C]
D) [alternativa D]
E) [alternativa E]

([letra correta])
"""

def formatar_questao(texto):
    """Formata o texto da questão para melhor visualização"""
    linhas = texto.split('\n')
    resultado = []
    
    for linha in linhas:
        if linha.startswith(('A)', 'B)', 'C)', 'D)', 'E)')):
            resultado.append(f"\n{linha}\n")
        else:
            resultado.append(linha)
    
    return '\n'.join(resultado)

def reset_questao():
    """Reseta o estado da questão atual"""
    st.session_state.questao_atual = None
    st.session_state.resposta_correta_atual = None
    st.session_state.aguardando_resposta = False
    if 'resposta_radio' in st.session_state:
        del st.session_state.resposta_radio
    if 'resposta_verificada' in st.session_state:
        del st.session_state.resposta_verificada
    if 'resposta_selecionada' in st.session_state:
        del st.session_state.resposta_selecionada

def extrair_pergunta(texto):
    """Extrai apenas a pergunta do texto completo"""
    linhas = texto.split('\n')
    for linha in linhas:
        if linha.startswith('PERGUNTA:'):
            return linha.replace('PERGUNTA:', '').strip()
    return None

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
            # Extrair e salvar apenas a pergunta
            pergunta = extrair_pergunta(conteudo)
            if pergunta and pergunta not in st.session_state.perguntas_anteriores:
                st.session_state.perguntas_anteriores.append(pergunta)
            
            st.session_state.ultima_resposta_correta = match.group(1)
            st.session_state.questao_atual = formatar_questao(conteudo.replace(f"({match.group(1)})", ""))
            st.session_state.resposta_correta_atual = match.group(1)
            st.session_state.aguardando_resposta = True
            return True
    except Exception as e:
        st.error(f"Erro ao gerar questão: {str(e)}")
        return False

def main():
    st.title("📚 Quiz Generator")
    st.markdown("---")
    
    # Exibir contador de perguntas feitas
    if st.session_state.perguntas_anteriores:
        st.sidebar.markdown(f"### Perguntas feitas: {len(st.session_state.perguntas_anteriores)}")
        with st.sidebar.expander("Ver perguntas anteriores"):
            for i, pergunta in enumerate(st.session_state.perguntas_anteriores, 1):
                st.write(f"{i}. {pergunta}")

    # Carregar documento se ainda não foi carregado
    if not st.session_state.documento:
        carregar_documento()

    # Botão para nova pergunta
    if st.button("Nova Pergunta", use_container_width=True):
        reset_questao()
        fazer_pergunta()

    # Exibir questão atual
    if st.session_state.questao_atual:
        st.markdown("### Questão:")
        st.write(st.session_state.questao_atual)
        
        # Input para resposta
        resposta = st.radio(
            "Selecione sua resposta:", 
            options=['A', 'B', 'C', 'D', 'E'],
            horizontal=True,
            key="resposta_radio",
            index=None
        )
        
        # Botão para verificar resposta
        if st.button("Verificar Resposta", use_container_width=True):
            if resposta == st.session_state.resposta_correta_atual:
                st.success(f"✅ CORRETO! A resposta é ({st.session_state.resposta_correta_atual})")
            else:
                st.error(f"❌ INCORRETO! A resposta correta é ({st.session_state.resposta_correta_atual})")

if __name__ == "__main__":
    main()
