import os
import google.generativeai as genai
from langchain.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFLoader

GOOGLE_API_KEY = 'AIzaSyDLupuG-brZ4r7bTKuq66reKPPoUWi2_pM'
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-1.5-pro')

# Carrega o arquivo PDF
caminho = r'C:\Users\adail\Documents\Curso Python Asimov\quiz-generator\Linha do Tempo.pdf'
loader = PyPDFLoader(caminho)
lista_documentos = loader.load()

documento = ''
for doc in lista_documentos:
    documento += doc.page_content

# Variável para armazenar a última resposta correta
ultima_resposta_correta = None

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
    global ultima_resposta_correta
    prompt = gerar_prompt(documento, ultima_resposta_correta if ultima_resposta_correta else "Nenhuma")
    
    try:
        response = model.generate_content(prompt)
        response.resolve()
        conteudo = response.text
        
        # Extrai a resposta correta da resposta
        import re
        match = re.search(r'\(([A-E])\)$', conteudo)
        if match:
            ultima_resposta_correta = match.group(1)
            print(conteudo.replace(f"({ultima_resposta_correta})", ""))  # Remove a resposta correta da exibição
            return ultima_resposta_correta
        else:
            print("Erro: Resposta correta não encontrada no formato esperado")
            return None
        
    except Exception as e:
        print(f"Erro ao gerar questão: {str(e)}")
        return None

def verificar_resposta(resposta_usuario, resposta_correta):
    if resposta_usuario == resposta_correta:
        print(f"\n✅ CORRETO! A resposta é ({resposta_correta})")
    else:
        print(f"\n❌ INCORRETO! A resposta correta é ({resposta_correta})")
    
    print("\nDigite 'pergunte' para receber uma nova questão ou 'sair' para encerrar.")

def main():
    print("Bem-vindo ao Quiz Generator!")
    print("Digite 'pergunte' para receber uma nova questão ou 'sair' para encerrar.")
    
    aguardando_resposta = False
    resposta_correta = None
    
    while True:
        if not aguardando_resposta:
            comando = input("\nDigite seu comando: ").lower().strip()
            
            if comando == "sair":
                print("Obrigado por usar o Quiz Generator!")
                break
            elif comando == "pergunte":
                resposta_correta = fazer_pergunta()
                if resposta_correta:
                    aguardando_resposta = True
            else:
                print("Comando não reconhecido. Use 'pergunte' ou 'sair'.")
        else:
            resposta_usuario = input("\nDigite sua resposta (A, B, C, D ou E): ").upper().strip()
            verificar_resposta(resposta_usuario, resposta_correta)
            aguardando_resposta = False

if __name__ == "__main__":
    main()