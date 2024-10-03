import maritalk
import os
import telebot
from dotenv import load_dotenv
from datetime import date

class Chat:
    def __init__(self, chat_id: int):
        self.chat_id = chat_id
        # self.esperando_mensagem = True
        self.meta_calorica = 0
        self.contagem_calorias = 0
        self.dieta = ""
        # aqui é uma maracutaia que eu fiz, para permitir vários chats rodarem ao mesmo tempo, as funções setup_dieta e setup_calorias são divididas em partes
        # e essas variáveis controlam para qual parte o programa vai
        # a ideia é: pega a primeira mensagem (setup_parte1 = True), faz a primeira parte da função (setup_parte1 = False), 
        # pega a proxima mensagem (setup_parte2 = True), faz a segunda parte da função (setup_parte2 = False)
        # não sei como fazer isso de uma forma melhor
        self.setup_calorias_parte1 = False
        self.setup_calorias_parte2 = False
        self.setup_dieta = False
        self.setup_dieta_feedback = False

chats: list[Chat] = []
prompt_direcionamento = """A partir do input do usuário, decida se ele quer contar calorias ou mudar a dieta.
        O usuário quer contar calorias caso ele fale sobre alguma refeição que fez.
        Se ele quiser mudar as calorias, digite somente 0. Se ele quiser contar calorias digite somente 1.
        Se o usuário citar algum alimento ou refeição, digite somente 1.
        Se ele digitar algo que não esteja relacionado a nenhuma dessas duas coisas (calorias e dieta), então retorne 'ERRO'.

        Usuário: Eu quero mudar a dieta.
        Resposta: 0
        
        Usuário: Eu comi um prato de feijão.
        Resposta: 1
        
        Usuário: Fui numa festa ontem.
        Resposta: ERRO

        Usuário: Não estou gostando da minha dieta.
        Resposta: 0
        
        Usuário: Peito de frango.
        Resposta: 1

        Usuário: Comi um peito de frango.
        Resposta: 1
        """

if __name__ == "__main__":
    # setup inicial da maritaca e do telegram
    load_dotenv()
    CHAVE_MARITACA = os.getenv("CHAVE_MARITACA")
    CHAVE_TELEGRAM = os.getenv("CHAVE_TELEGRAM")
    model = maritalk.MariTalk(key=CHAVE_MARITACA,model="sabia-3")
    bot = telebot.TeleBot(CHAVE_TELEGRAM)

    # setup das variáveis
    data = date.today() 

    def get_chat(chat_id: int) -> Chat or None:
        for chat in chats:
            if chat.chat_id == chat_id:
                return chat
        return None

    def setup_calorias(chat,message, parte): # conferir valor de cut e de bulking (eu botei +400 e -400) e conferir calorias
        if parte == 0:
            prompt_calculo_calorias = """Você é um bot que calcula a quantidade de calorias diárias gastas pelo usuário a partir das informações dadas por ele.
            A partir das informações dadas pelo usuário, calcule a quantidade de calorias diárias gastas por ele e retorne SOMENTE o número de calorias. 
            Não retorne NADA além do número de calorias. Caso falte informações, faça a sua melhor aproximação da quantidade de calorias gastas pelo usuário.
            NUNCA deixe de retornar apenas o número de calorias, mesmo que talvez esse número esteja errado.

            Usuário: Tenho 18 anos, 1.75 centimetros de altura, peso 75 quilos e pratico exercícios moderados (musculação) uma vez por semana e sou homem.
            Resposta: 2100
            
            Usuário: Tenho 19 anos, 1.78 centimetros de altura, peso 72 quilos e sou homem.
            Resposta: 2300
            """

            chat.meta_calorica = int(model.generate(prompt_calculo_calorias+message.text,max_tokens=200,stopping_tokens=["\n"])["answer"])
            
            # preparando para a segunda parte da função
            chat.setup_calorias_parte1 = False
            chat.setup_calorias_parte2 = True
            bot.send_message(message.chat.id,"Você quer emagrecer ou ganhar massa?")
        elif parte == 1:
            prompt_objetivo = """A partir da resposta do usuário, decida se ele quer emagrecer (cut) ou ganhar massa muscular.
            Caso ele queira emagrecer (cut), retorne -400.
            Caso ele queira ganhar massa muscular (bulk), retorne 400.
            Nunca retorne algo além de 400 ou -400. Caso você não consiga determinar se ele quer emagrecer ou ganhar massa muscular, faça uma suposição.
            """

            objetivo = model.generate(prompt_objetivo+message.text,max_tokens=200,stopping_tokens=["\n"])["answer"]

            chat.meta_calorica += int(objetivo)
            bot.send_message(message.chat.id, f"Você comeu 0 de {chat.meta_calorica} calorias.")
            
            # preparando para a primeira parte da função setup_dieta
            bot.send_message(message.chat.id, "Agora, vou fazer a sua dieta. Me fale como você quer que a sua dieta seja feita (Ex: não é para usar ovo).")
            chat.setup_calorias_parte2 = False
            # chat.setup_dieta = True # esta comentado pq a setup dieta não está feita ainda
    
    def setup_dieta(chat,message,parte):
        if parte == 0:
            # faça aqui a primeira dieta
            print() # só para não dar problema de identação
            chat.setup_dieta = False
            chat.setup_dieta_feedback = True
        elif parte == 1:
            # repita aqui até a dieta estar boa
            # ou seja, se a pessoa pediu a dieta sem ovo mas veio com ovo, aqui é para repetir o processo de criação até acertar a dieta
            # if(message é que a pessoa gostou) (passo 1):
            # chat.setup_dieta_feedback = False
            # bot.send_message(message.chat.id,"Para atualizar a contagem de calorias, digite o que você comeu ("Comi um prato de arroz, feijão e frango."). Caso você queira mudar a sua dieta ou meta calórica, digite "Quero mudar a minha dieta" ou algo equivalente.")
            # return
            # if(message é que a pessoa não gostou)
            # faz alguma coisa, volta para o passo 1 para ver se deu certo (vai naturalmente voltar para o passo 1 após a pessoa mandar uma mensagem)
            print() # so para não dar problema de indentação

    # def contagem_calorias(chat,message):

    @bot.message_handler(func=lambda message: True) # o motivo de o bot não funcionar por comandos (/start) é porque eu achei
    # que seria mais interessante fazer o usuário interagir com o bot somente com linguagem natural, já que isso implicaria usar mais a maritaca
    def direcionamento(message):
        global prompt_direcionamento, data
        chat = get_chat(message.chat.id)

        # setup inicial da dieta e meta calórica
        if chat is None: 
            novo_chat = Chat(message.chat.id)
            chats.append(novo_chat)
            bot.reply_to(message, "Olá, eu sou o ChiquinhoGaviãoBOT, O bot de nutrição e eu vou te ajudar a alcançar o seu shape dos sonhos. Para isso, eu vou calcular a sua meta diária de calorias e fazer uma dieta para você.")
            bot.send_message(message.chat.id,"Digite: Eu quero fazer minha dieta.")
            return
        
        # expliquei o porquê eu fiz isso na class chat, mas basicamente é um controle de fluxo para saber em que parte da função o programa deve ir
        # surge do problema do programa ter que rodar vários chats ao mesmo tempo e funcionar mensagem por mensagem
        if chat.setup_calorias_parte1:
            setup_calorias(chat,message,0)
            return
        elif chat.setup_calorias_parte2:
            setup_calorias(chat,message,1)
            return
        elif chat.setup_dieta:
            setup_dieta(chat,message,0)
            return
        elif chat.setup_dieta_feedback:
            setup_dieta(chat,message,1)
            return

        # reseta a contagem para cada dia novo
        if (data != date.today()): 
            chat.contagem_calorias = 0
            data = date.today()

        # após o setup inicial da dieta e da meta calórica, o usuário só pode fazer duas coisas: mudar a dieta ou contar calorias
        # a variável direcao serve para dizer ao programa se o usuário quer mudar a dieta (0) ou contar calorias (1)
        # cabe ao modelo analisar a mensagem e decidir o que o usuário quer fazer
        direcao = model.generate(prompt_direcionamento+message.text,max_tokens=200,stopping_tokens=["\n"])["answer"]
        print(direcao)

        if (direcao=='ERRO'):
            bot.send_message(message.chat.id,"Você digitou algo que não me interessa. Só me interesso por contar calorias e montar dietas!")
            return
        
        try:
            direcao = int(direcao)
        except:
            bot.send_message(message.chat.id,"Algo de errado ocorreu, digite a sua mensagem novamente!")
            return
        
        if (direcao==1):
            print() # remove depois, só para não dar erro de identação
            # contagem_calorias(chat,message)
        elif (direcao==0):
            bot.send_message(message.chat.id,"Para calcular a sua meta calórica, digite a sua idade, peso, altura e sexo.")
            chat.setup_calorias_parte1 = True

    bot.infinity_polling()