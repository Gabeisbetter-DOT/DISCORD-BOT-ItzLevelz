const Discord = require('discord.js');
const { Client, GatewayIntentBits, EmbedBuilder, AttachmentBuilder, SlashCommandBuilder } = require('discord.js');
const { REST, Routes } = require('discord.js');
const Canvas = require('@napi-rs/canvas');
const fs = require('fs');

// Initialize client
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildMembers
  ]
});

// Data storage
let userData = {};
let guildData = {};

// Rank tiers with colors
const RANKS = {
  'S++': { threshold: 50000, color: '#00BFFF', rimColor: '#FFFFFF', words: 50000 },
  'S+': { threshold: 40000, color: '#1E90FF', rimColor: '#E0E0E0', words: 40000 },
  'S': { threshold: 30000, color: '#4169E1', rimColor: '#D0D0D0', words: 30000 },
  'A+': { threshold: 25000, color: '#9370DB', rimColor: '#C0C0C0', words: 25000 },
  'A': { threshold: 20000, color: '#8A2BE2', rimColor: '#B0B0B0', words: 20000 },
  'A-': { threshold: 17500, color: '#7B68EE', rimColor: '#A0A0A0', words: 17500 },
  'B+': { threshold: 15000, color: '#32CD32', rimColor: '#909090', words: 15000 },
  'B': { threshold: 12500, color: '#228B22', rimColor: '#808080', words: 12500 },
  'B-': { threshold: 10000, color: '#008000', rimColor: '#707070', words: 10000 },
  'C+': { threshold: 7500, color: '#FFD700', rimColor: '#606060', words: 7500 },
  'C': { threshold: 5000, color: '#FFA500', rimColor: '#505050', words: 5000 },
  'C-': { threshold: 3500, color: '#FF8C00', rimColor: '#454545', words: 3500 },
  'D+': { threshold: 2500, color: '#FF6347', rimColor: '#404040', words: 2500 },
  'D': { threshold: 1500, color: '#FF4500', rimColor: '#353535', words: 1500 },
  'D-': { threshold: 1000, color: '#DC143C', rimColor: '#303030', words: 1000 },
  'F+': { threshold: 500, color: '#8B4513', rimColor: '#282828', words: 500 },
  'F': { threshold: 100, color: '#654321', rimColor: '#202020', words: 100 },
  'F-': { threshold: 0, color: '#5C4033', rimColor: '#1a1a1a', words: 0 }
};

// Calculate XP from words (5 words = 10 XP)
function calculateXP(words) {
  return Math.floor(words / 5) * 10;
}

// Calculate level from XP
function calculateLevel(xp) {
  return Math.floor(Math.pow(xp / 100, 0.5)) + 1;
}

// Calculate XP needed for next level
function xpForNextLevel(level) {
  return Math.pow(level, 2) * 100;
}

// Get rank based on monthly words
function getRank(monthlyWords) {
  for (const [rank, data] of Object.entries(RANKS)) {
    if (monthlyWords >= data.threshold) {
      return rank;
    }
  }
  return 'F-';
}

// Initialize user data
function initUser(guildId, userId) {
  if (!guildData[guildId]) {
    guildData[guildId] = {};
  }
  
  if (!guildData[guildId][userId]) {
    guildData[guildId][userId] = {
      totalWords: 0,
      monthlyWords: 0,
      messages: 0,
      characters: 0,
      rank: 'F-',
      lastRankUpdate: Date.now(),
      joinDate: Date.now()
    };
  }
  
  return guildData[guildId][userId];
}

// Save data
function saveData() {
  fs.writeFileSync('guildData.json', JSON.stringify(guildData, null, 2));
}

// Load data
function loadData() {
  try {
    if (fs.existsSync('guildData.json')) {
      guildData = JSON.parse(fs.readFileSync('guildData.json', 'utf8'));
    }
  } catch (err) {
    console.error('Error loading data:', err);
  }
}

// Create score card
async function createScoreCard(user, userData, member) {
  const canvas = Canvas.createCanvas(800, 400);
  const ctx = canvas.getContext('2d');
  
  const xp = calculateXP(userData.totalWords);
  const level = calculateLevel(xp);
  const currentLevelXP = xpForNextLevel(level - 1);
  const nextLevelXP = xpForNextLevel(level);
  const xpProgress = xp - currentLevelXP;
  const xpNeeded = nextLevelXP - currentLevelXP;
  const progressPercent = (xpProgress / xpNeeded) * 100;
  
  const rank = userData.rank || 'F-';
  const rankData = RANKS[rank];
  
  // Background gradient
  const gradient = ctx.createLinearGradient(0, 0, 800, 400);
  gradient.addColorStop(0, '#2C2F33');
  gradient.addColorStop(1, '#23272A');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 800, 400);
  
  // Rank rim effect
  ctx.strokeStyle = rankData.rimColor;
  ctx.lineWidth = 8;
  ctx.strokeRect(10, 10, 780, 380);
  
  // Inner border
  ctx.strokeStyle = rankData.color;
  ctx.lineWidth = 4;
  ctx.strokeRect(15, 15, 770, 370);
  
  // User avatar circle
  ctx.save();
  ctx.beginPath();
  ctx.arc(100, 100, 60, 0, Math.PI * 2);
  ctx.closePath();
  ctx.clip();
  
  try {
    const avatarURL = user.displayAvatarURL({ extension: 'png', size: 256 });
    const avatar = await Canvas.loadImage(avatarURL);
    ctx.drawImage(avatar, 40, 40, 120, 120);
  } catch (err) {
    ctx.fillStyle = '#7289DA';
    ctx.fill();
  }
  
  ctx.restore();
  
  // Avatar ring
  ctx.strokeStyle = rankData.color;
  ctx.lineWidth = 5;
  ctx.beginPath();
  ctx.arc(100, 100, 65, 0, Math.PI * 2);
  ctx.stroke();
  
  // Username
  ctx.font = 'bold 36px Arial';
  ctx.fillStyle = '#FFFFFF';
  ctx.fillText(user.username, 180, 80);
  
  // Rank badge
  ctx.font = 'bold 48px Arial';
  ctx.fillStyle = rankData.color;
  ctx.fillText(`Rank: ${rank}`, 180, 130);
  
  // Level
  ctx.font = 'bold 32px Arial';
  ctx.fillStyle = '#FFD700';
  ctx.fillText(`Level ${level}`, 620, 80);
  
  // Stats box background
  ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
  ctx.fillRect(30, 180, 740, 190);
  
  // Stats
  ctx.font = 'bold 24px Arial';
  ctx.fillStyle = '#FFFFFF';
  
  const stats = [
    { label: 'Total Words:', value: userData.totalWords.toLocaleString(), x: 50, y: 220 },
    { label: 'Monthly Words:', value: userData.monthlyWords.toLocaleString(), x: 50, y: 260 },
    { label: 'Total XP:', value: xp.toLocaleString(), x: 50, y: 300 },
    { label: 'Messages Sent:', value: userData.messages.toLocaleString(), x: 420, y: 220 },
    { label: 'Characters Typed:', value: userData.characters.toLocaleString(), x: 420, y: 260 },
    { label: 'XP to Next Level:', value: (xpNeeded - xpProgress).toLocaleString(), x: 420, y: 300 }
  ];
  
  stats.forEach(stat => {
    ctx.fillStyle = '#B0B0B0';
    ctx.fillText(stat.label, stat.x, stat.y);
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText(stat.value, stat.x + 220, stat.y);
  });
  
  // Progress bar background
  ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
  ctx.fillRect(50, 330, 700, 30);
  
  // Progress bar fill
  const progressGradient = ctx.createLinearGradient(50, 330, 750, 330);
  progressGradient.addColorStop(0, rankData.color);
  progressGradient.addColorStop(1, '#FFFFFF');
  ctx.fillStyle = progressGradient;
  ctx.fillRect(50, 330, (700 * progressPercent) / 100, 30);
  
  // Progress bar border
  ctx.strokeStyle = rankData.color;
  ctx.lineWidth = 3;
  ctx.strokeRect(50, 330, 700, 30);
  
  // Progress text
  ctx.font = 'bold 18px Arial';
  ctx.fillStyle = '#FFFFFF';
  ctx.fillText(`${progressPercent.toFixed(1)}% to Level ${level + 1}`, 330, 352);
  
  return canvas.toBuffer('image/png');
}

// Register slash commands
async function registerCommands() {
  const commands = [
    new SlashCommandBuilder()
      .setName('rank')
      .setDescription('View your score card'),
    
    new SlashCommandBuilder()
      .setName('rankupdate')
      .setDescription('Update your monthly rank (available every 30 days)'),
    
    new SlashCommandBuilder()
      .setName('leaderboard')
      .setDescription('View the server leaderboard')
      .addStringOption(option =>
        option.setName('type')
          .setDescription('Leaderboard type')
          .setRequired(false)
          .addChoices(
            { name: 'Total Words', value: 'words' },
            { name: 'Level', value: 'level' },
            { name: 'Monthly Words', value: 'monthly' }
          )
      ),
    
    new SlashCommandBuilder()
      .setName('stats')
      .setDescription('View detailed statistics')
      .addUserOption(option =>
        option.setName('user')
          .setDescription('User to view stats for')
          .setRequired(false)
      )
  ].map(command => command.toJSON());
  
  const rest = new REST({ version: '10' }).setToken(process.env.DISCORD_TOKEN);
  
  try {
    console.log('Registering slash commands...');
    await rest.put(
      Routes.applicationCommands(client.user.id),
      { body: commands }
    );
    console.log('Successfully registered slash commands!');
  } catch (error) {
    console.error('Error registering commands:', error);
  }
}

// Bot ready event
client.once('ready', async () => {
  console.log(`Logged in as ${client.user.tag}!`);
  loadData();
  await registerCommands();
  
  // Auto-save every 5 minutes
  setInterval(saveData, 5 * 60 * 1000);
});

// Message tracking
client.on('messageCreate', async (message) => {
  if (message.author.bot) return;
  if (!message.guild) return;
  
  const user = initUser(message.guild.id, message.author.id);
  
  const words = message.content.trim().split(/\s+/).filter(w => w.length > 0).length;
  
  user.totalWords += words;
  user.monthlyWords += words;
  user.messages += 1;
  user.characters += message.content.length;
  
  // Save periodically
  if (Math.random() < 0.1) {
    saveData();
  }
});

// Slash command handling
client.on('interactionCreate', async (interaction) => {
  if (!interaction.isCommand()) return;
  
  const { commandName } = interaction;
  
  try {
    if (commandName === 'rank') {
      await interaction.deferReply();
      
      const user = initUser(interaction.guild.id, interaction.user.id);
      const buffer = await createScoreCard(interaction.user, user, interaction.member);
      
      const attachment = new AttachmentBuilder(buffer, { name: 'scorecard.png' });
      await interaction.editReply({ files: [attachment] });
      
    } else if (commandName === 'rankupdate') {
      const user = initUser(interaction.guild.id, interaction.user.id);
      
      const daysSinceUpdate = (Date.now() - user.lastRankUpdate) / (1000 * 60 * 60 * 24);
      
      if (daysSinceUpdate < 30) {
        const daysRemaining = Math.ceil(30 - daysSinceUpdate);
        return interaction.reply({
          content: `❌ You can update your rank in **${daysRemaining} days**!`,
          ephemeral: true
        });
      }
      
      const oldRank = user.rank;
      const newRank = getRank(user.monthlyWords);
      user.rank = newRank;
      user.monthlyWords = 0;
      user.lastRankUpdate = Date.now();
      
      saveData();
      
      const rankData = RANKS[newRank];
      const embed = new EmbedBuilder()
        .setTitle('🎖️ Rank Updated!')
        .setDescription(`Your monthly rank has been updated!`)
        .addFields(
          { name: 'Previous Rank', value: oldRank, inline: true },
          { name: 'New Rank', value: newRank, inline: true }
        )
        .setColor(rankData.color)
        .setTimestamp();
      
      await interaction.reply({ embeds: [embed] });
      
    } else if (commandName === 'leaderboard') {
      const type = interaction.options.getString('type') || 'words';
      const guildUsers = guildData[interaction.guild.id] || {};
      
      let sorted;
      let title;
      let valueFormatter;
      
      if (type === 'words') {
        sorted = Object.entries(guildUsers).sort((a, b) => b[1].totalWords - a[1].totalWords);
        title = '📊 Total Words Leaderboard';
        valueFormatter = (data) => `${data.totalWords.toLocaleString()} words`;
      } else if (type === 'level') {
        sorted = Object.entries(guildUsers).sort((a, b) => {
          const xpA = calculateXP(a[1].totalWords);
          const xpB = calculateXP(b[1].totalWords);
          return calculateLevel(xpB) - calculateLevel(xpA);
        });
        title = '⭐ Level Leaderboard';
        valueFormatter = (data) => `Level ${calculateLevel(calculateXP(data.totalWords))}`;
      } else {
        sorted = Object.entries(guildUsers).sort((a, b) => b[1].monthlyWords - a[1].monthlyWords);
        title = '📅 Monthly Words Leaderboard';
        valueFormatter = (data) => `${data.monthlyWords.toLocaleString()} words`;
      }
      
      const top10 = sorted.slice(0, 10);
      
      const embed = new EmbedBuilder()
        .setTitle(title)
        .setColor('#FFD700')
        .setTimestamp();
      
      let description = '';
      for (let i = 0; i < top10.length; i++) {
        const [userId, data] = top10[i];
        const user = await client.users.fetch(userId).catch(() => null);
        const username = user ? user.username : 'Unknown User';
        const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}.`;
        description += `${medal} **${username}** - ${valueFormatter(data)}\n`;
      }
      
      embed.setDescription(description || 'No data yet!');
      
      await interaction.reply({ embeds: [embed] });
      
    } else if (commandName === 'stats') {
      const targetUser = interaction.options.getUser('user') || interaction.user;
      const user = initUser(interaction.guild.id, targetUser.id);
      
      const xp = calculateXP(user.totalWords);
      const level = calculateLevel(xp);
      
      const embed = new EmbedBuilder()
        .setTitle(`📊 Stats for ${targetUser.username}`)
        .setThumbnail(targetUser.displayAvatarURL())
        .addFields(
          { name: 'Rank', value: user.rank, inline: true },
          { name: 'Level', value: level.toString(), inline: true },
          { name: 'Total XP', value: xp.toLocaleString(), inline: true },
          { name: 'Total Words', value: user.totalWords.toLocaleString(), inline: true },
          { name: 'Monthly Words', value: user.monthlyWords.toLocaleString(), inline: true },
          { name: 'Messages', value: user.messages.toLocaleString(), inline: true },
          { name: 'Characters', value: user.characters.toLocaleString(), inline: true },
          { name: 'Avg Words/Message', value: (user.totalWords / Math.max(user.messages, 1)).toFixed(2), inline: true }
        )
        .setColor(RANKS[user.rank].color)
        .setTimestamp();
      
      await interaction.reply({ embeds: [embed] });
    }
  } catch (error) {
    console.error('Command error:', error);
    const reply = { content: '❌ An error occurred!', ephemeral: true };
    if (interaction.deferred) {
      await interaction.editReply(reply);
    } else {
      await interaction.reply(reply);
    }
  }
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('Saving data...');
  saveData();
  process.exit(0);
});

// Login
client.login(process.env.DISCORD_TOKEN);
