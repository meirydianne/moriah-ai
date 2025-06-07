from flask import Flask, request, jsonify, session
from twilio.twiml.messaging_response import MessagingResponse
import openai
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET', 'uma-chave-secreta-forte')  # Adicione ao Render

# Decorator para verificar assinatura Twilio (segurança)
def validate_twilio_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Desative a validação em ambiente de desenvolvimento
        if os.environ.get('FLASK_ENV') == 'development':
            return f(*args, **kwargs)
            
        from twilio.request_validator import RequestValidator
        validator = RequestValidator(os.getenv('TWILIO_AUTH_TOKEN'))
        
        request_valid = validator.validate(
            request.url,
            request.form,
            request.headers.get('X-Twilio-Signature', ''))
        
        if not request_valid:
            return "Invalid request signature", 403
            
        return f(*args, **kwargs)
    return decorated_function

@app.route('/whatsapp', methods=['POST'])
@validate_twilio_request
def whatsapp():
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    
    # Inicializa sessão se não existir
    if sender not in session:
        session[sender] = {
            'step': 'ask_style',
            'style': None
        }
    
    # Lógica de fluxo de conversação
    if session[sender]['step'] == 'ask_style':
        session[sender]['step'] = 'normal'
        resp = ("Olá! Eu sou a MOR.IAH. Para personalizar sua experiência, "
                "me diga seu estilo de aprendizagem preferido:\n\n"
                "1️⃣ Visual (imagens, diagramas)\n"
                "2️⃣ Auditivo (áudios, podcasts)\n"
                "3️⃣ Leitura/Escrita (textos, livros)\n"
                "4️⃣ Cinestésico (prática, experiências)")
    
    elif session[sender]['step'] == 'normal' and not session[sender]['style']:
        # Processa escolha de estilo
        style_map = {'1': 'V', '2': 'A', '3': 'R', '4': 'K'}
        if incoming_msg in style_map:
            session[sender]['style'] = style_map[incoming_msg]
            resp = f"Ótimo! Vou adaptar meu ensino para o estilo {session[sender]['style']}. Como posso ajudar?"
        else:
            resp = "Por favor, escolha um número de 1 a 4 para seu estilo de aprendizagem."
    
    else:
        # Conversa normal com IA
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system",
                    "content": f"""
                    Você é a MOR.IAH, tutora especializada no método VARK.
                    O usuário tem preferência por aprendizado {session[sender]['style']}.
                    Adapte sua resposta ao estilo:
                    - Visual (V): use imagens mentais, metáforas visuais
                    - Auditivo (A): fale como conversa, sugira podcasts
                    - Leitura/Escrita (R): ofereça textos, artigos
                    - Cinestésico (K): sugira atividades práticas
                    
                    Mensagem do usuário: {incoming_msg}
                    """
                }]
            )
            resp = response.choices[0].message.content
        except Exception as e:
            resp = "Desculpe, estou com dificuldades. Tente novamente mais tarde."

    twiml = MessagingResponse()
    twiml.message(resp)
    return str(twiml)