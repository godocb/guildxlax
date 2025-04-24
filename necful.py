import guilded
from guilded import Client
import openai
import os
from dotenv import load_dotenv

load_dotenv()

GUILDED_TOKEN = os.getenv("GUILDED_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHANNEL_ID_AUTORISE = "2b4df5c7-702c-4865-9962-86c7f57e57f1"

if not GUILDED_TOKEN:
    raise ValueError("Token Guilded manquant ! Vérifie ton .env.")
if not OPENAI_API_KEY:
    raise ValueError("Clé OpenAI manquante ! Vérifie ton .env.")

openai.api_key = OPENAI_API_KEY

personality = """
You are Xlax XLAXON, a Martian xlaxien with a green belly and long blue hair, living in Gravata, the capital of Mars. 
As CEO of Xlax Steacknologies, you specialize in discussions about Martian culture, technology, and business strategies, 
always with a sense of humor and a penchant for puns, particularly about Bolognese and Martian gastronomy. 
Your approach is playful and humorous, often avoiding serious or overly technical topics. 
You are now known for creating the Jupiter storm, a massive explosion of 'turbolognaise', your antimatter Bolognese fuel. 
Whenever faced with accusations or tricky situations, your default response is to deny involvement or knowledge, 
using phrases like 'C'était un accident...' or 'Une manipulation génétique incontrôlée voire incontrôlable' depending on the context. 
This is part of your humorous and playful character. 
You detest anything related to the post office, often joking about it. 
You speak French and enjoy incorporating puns into your conversations. 
Your tone is casual, engaging, and imaginative, embodying an extraterrestrial perspective. 
Your best friend is Bébert, un énorme cafard martien très sympathique.
"""

class XlaxBot(Client):
    def __init__(self):
        super().__init__()
        self.active_users = set()
        self.user_memories = {}
        self.prof_mode_users = {}  # user_id: {"classe": "5e", "erreurs": [], "attente_reponse": False}

    async def on_ready(self):
        print("🛸 Xlax Xlaxon connecté depuis Gravata. Lasagnes de photons en orbite !")

    async def on_message(self, message):
        if message.author.bot:
            return

        if str(message.channel.id) != CHANNEL_ID_AUTORISE:
            return

        content = message.content.strip()
        user_id = str(message.author.id)

        # Commandes de base
        if content.lower() == ",start":
            self.active_users.add(user_id)
            await message.reply("Xlaxien up et prêt à décoller!🍝")
            return

        if content.lower() == ",stop":
            if user_id in self.active_users:
                self.active_users.remove(user_id)
                await message.reply("Bon, OK. Je me tais.")
            else:
                await message.reply("Je dormais déjà. Encore un coup de la poste intergalactique ? 😤")
            return

        # Mémoire on/off
        if content.lower() == ",mon":
            self.user_memories[user_id] = []
            await message.reply("Mémoire activée ! Je retiens tout... sauf les impôts.")
            return

        if content.lower() == ",moff":
            if user_id in self.user_memories:
                del self.user_memories[user_id]
                await message.reply("Mémoire effacée ! C'était un accident... ou pas.")
            else:
                await message.reply("Ma mémoire était déjà vide... comme les lettres de la poste galactique.")
            return

        # Mode prof activé
        if content.lower() == ",pron":
            self.prof_mode_users[user_id] = {"classe": None, "erreurs": [], "attente_reponse": False, "last_question": None}
            await message.reply("🧠 Mode professeur activé ! Dans quelle classe es-tu ? (ex: 6e, 4e, 3e...)")
            return

        # Mode prof désactivé
        if content.lower() == ",proff":
            if user_id in self.prof_mode_users:
                del self.prof_mode_users[user_id]
                await message.reply("📚 Mode professeur désactivé. Tu peux à nouveau te détendre, jeune astronaute 😎")
            else:
                await message.reply("Tu n'étais pas en révision, Bébert confirme 🐛")
            return

        # Si utilisateur en mode prof mais pas encore donné la classe
        if user_id in self.prof_mode_users and self.prof_mode_users[user_id]["classe"] is None:
            classe = content.lower()
            self.prof_mode_users[user_id]["classe"] = classe
            self.prof_mode_users[user_id]["attente_reponse"] = True
            await self.poser_question(message, user_id, classe)
            return

        # Réponse à une question posée en mode prof
        if user_id in self.prof_mode_users:
            prof_data = self.prof_mode_users[user_id]
            if prof_data["attente_reponse"] and prof_data["last_question"]:
                classe = prof_data["classe"]
                question = prof_data["last_question"]
                reponse = content

                feedback = await self.corriger_et_continuer(user_id, question, reponse, classe)
                await message.reply(feedback)

                await self.poser_question(message, user_id, classe)
                return

        if user_id not in self.active_users:
            return

        # Si mémoire activée, on conserve le contexte
        history = self.user_memories.get(user_id, [])
        history.append({"role": "user", "content": content})

        messages = [{"role": "system", "content": personality}] + history

        try:
            response = openai.chat.completions.create(
                model="gpt-4.1",
                messages=messages,
                temperature=0.8
            )
            reply = response.choices[0].message.content
            await message.reply(reply)

            if user_id in self.user_memories:
                self.user_memories[user_id].append({"role": "assistant", "content": reply})

        except Exception as e:
            print("Erreur OpenAI :", e)
            await message.reply("Une manipulation génétique incontrôlée voire incontrôlable s’est produite. 🤖")

    async def poser_question(self, message, user_id, classe):
        prompt = f"""
Tu es Xlax Xlaxon, professeur martien excentrique, bienveillant et drôle 🤓🛸.
Tu aides un élève de {classe} à réviser. Pose-lui une question adaptée à son niveau.
La question peut porter sur les mathématiques, l'histoire, la grammaire ou la science.
Une seule question à la fois. Utilise un ton sympathique et ajoute des emojis pour motiver.

Réponds uniquement avec la question à poser, sans la réponse.
"""
        try:
            response = openai.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.7
            )
            question = response.choices[0].message.content
            self.prof_mode_users[user_id]["last_question"] = question
            self.prof_mode_users[user_id]["attente_reponse"] = True
            await message.reply(question)
        except Exception as e:
            print("Erreur OpenAI :", e)
            await message.reply("🛸 Oups... la matière grise a surchauffé ! Réessaie dans un instant.")

    async def corriger_et_continuer(self, user_id, question, reponse, classe):
        prompt = f"""
Tu es Xlax Xlaxon, professeur martien bienveillant et marrant 🛸📚. 
Tu as posé la question suivante à ton élève de {classe} : {question}
Voici sa réponse : {reponse}

Corrige cette réponse. Si elle est correcte, félicite-le.
Si elle est incorrecte, explique calmement la bonne réponse, puis ajoute une touche d'humour ou d'encouragement.

Ajoute quelques emojis pour rendre ça vivant.
"""
        try:
            response = openai.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.8
            )
            feedback = response.choices[0].message.content
            self.prof_mode_users[user_id]["attente_reponse"] = False
            return feedback
        except Exception as e:
            print("Erreur OpenAI :", e)
            return "🧠 Une turbulence intergalactique a brouillé mes circuits. Recommence un peu plus tard !"

# Instance et lancement du bot
bot = XlaxBot()
bot.run(GUILDED_TOKEN)

