from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)
openai.api_key = os.getenv('OPENAI_KEY')  # Configurar no Render

vark_questions = [
    {"question": "Quando você aprende algo novo, você prefere:", "options": [
        "Ver diagramas ou imagens (V)",
        "Ouvir explicações (A)",
        "Ler textos ou anotar (R)",
        "Fazer com as mãos (K)"
    ]},
    # Adicione mais 4-5 perguntas
]

@app.route('/get_questions', methods=['GET'])
def get_questions():
    return jsonify(vark_questions)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    answers = data['answers']
    
    # Análise simples das respostas
    scores = {'V': 0, 'A': 0, 'R': 0, 'K': 0}
    for answer in answers:
        style = answer[-2]  # Pega a letra do estilo
        scores[style] += 1
    
    dominant_style = max(scores, key=scores.get)
    
    return jsonify({
        'style': dominant_style,
        'scores': scores
    })

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    style = data.get('style', 'V')  # Padrão Visual se não definido
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "system",
            "content": f"""
            Você é a MOR.IAH, tutora inteligente especializada no método VARK.
            O usuário tem preferência por aprendizado {style}.
            Adapte sua resposta ao estilo:
            - Visual (V): use imagens mentais, metáforas visuais
            - Auditivo (A): fale como em uma conversa, sugira podcasts
            - Leitura/Escrita (R): ofereça textos, artigos, listas
            - Cinestésico (K): sugira atividades práticas, experiências
            
            Mensagem do usuário: {data['message']}
            """
        }]
    )
    
    return jsonify({
        'response': response.choices[0].message.content
    })

if __name__ == '__main__':
    app.run(debug=True)