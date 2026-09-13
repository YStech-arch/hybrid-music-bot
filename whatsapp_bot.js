console.log(`
__   ______   _____ _____ ____  _   _ 
\ \ / / ___| |_   _| ____/ ___|| | | |
 \ V /\___ \   | | |  _|| |    | |_| |
  | |  ___) |  | | | |__| |___ |  _  |
  |_| |____/   |_| |_____\____||_| |_|

 Created by : YS Tech <ystech78@gmail.com>
 Project    : Hybrid Music Bot
`);
const {
    default: makeWASocket,
    useMultiFileAuthState,
    DisconnectReason
} = require('@whiskeysockets/baileys');

const qrcode = require('qrcode-terminal');
const QRCode = require('qrcode');
const { spawn } = require('child_process');
const fs = require('fs');

async function searchAndDownload(query) {
    return new Promise((resolve) => {
        const python = spawn('/home/ec2-user/yt-dlp-env/bin/python3', [
            'music_cli.py',
            query
        ], {
            cwd: __dirname
        });

        let stdout = '';
        let stderr = '';

        python.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        python.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        python.on('close', (code) => {
            const lines = stdout
                .split('\n')
                .map(line => line.trim())
                .filter(Boolean);

            let result = null;

            // Cari JSON terakhir dari output Python
            for (let i = lines.length - 1; i >= 0; i--) {
                try {
                    const parsed = JSON.parse(lines[i]);

                    if (parsed && typeof parsed === 'object') {
                        result = parsed;
                        break;
                    }
                } catch (e) {}
            }

            if (code !== 0 || !result) {
                console.error('❌ Python error:', stderr || stdout);
                resolve({
                    ok: false,
                    error: 'Gagal menjalankan music engine'
                });
                return;
            }

            resolve(result);
        });

        python.on('error', (error) => {
            console.error('❌ Spawn error:', error);

            resolve({
                ok: false,
                error: error.message
            });
        });
    });
}


async function searchAndDownloadVideo(query) {
    return new Promise((resolve) => {
        const path = require('path');
        const crypto = require('crypto');

        const requestDir = path.join(
            __dirname,
            'downloads',
            'video_' + crypto.randomBytes(8).toString('hex')
        );

        fs.mkdirSync(requestDir, { recursive: true });

        const outputTemplate = path.join(
            requestDir,
            '%(title)s.%(ext)s'
        );

        const ytDlp = '/home/ec2-user/yt-dlp-env/bin/yt-dlp';

        const args = [
            'ytsearch1:' + query,
            '-f', 'bv*[ext=mp4][vcodec^=avc1][height<=720]+ba[ext=m4a][acodec^=mp4a]/b[ext=mp4][vcodec^=avc1][height<=720]/b[ext=mp4]',
            '--merge-output-format', 'mp4',
            '--no-playlist',
            '--cookies', '/home/ec2-user/cookies.txt',
            '--remote-components', 'ejs:github',
            '--max-filesize', '50M',
            '-o', outputTemplate,
            '--print', 'after_move:filepath',
            '--quiet',
            '--no-warnings'
        ];

        const proc = spawn(ytDlp, args, {
            cwd: __dirname
        });

        let stdout = '';
        let stderr = '';

        proc.stdout.on('data', data => {
            stdout += data.toString();
        });

        proc.stderr.on('data', data => {
            stderr += data.toString();
        });

        proc.on('close', code => {
            const files = fs.readdirSync(requestDir)
                .filter(f => f.toLowerCase().endsWith('.mp4'));

            if (code !== 0 || files.length === 0) {
                console.error('❌ Video yt-dlp error:', stderr || stdout);

                try {
                    fs.rmSync(requestDir, {
                        recursive: true,
                        force: true
                    });
                } catch (e) {}

                resolve({
                    ok: false,
                    error: 'Video tidak ditemukan atau gagal di-download.'
                });
                return;
            }

            const videoFile = path.join(requestDir, files[0]);

            resolve({
                ok: true,
                file: videoFile,
                title: path.basename(videoFile, '.mp4'),
                dir: requestDir
            });
        });

        proc.on('error', error => {
            console.error('❌ Video spawn error:', error);

            try {
                fs.rmSync(requestDir, {
                    recursive: true,
                    force: true
                });
            } catch (e) {}

            resolve({
                ok: false,
                error: error.message
            });
        });
    });
}


async function startBot(sessionName) {
    const authDir = sessionName === 'wa1'
        ? 'auth_info_baileys'
        : `auth_info_baileys_${sessionName}`;

    const { state, saveCreds } =
        await useMultiFileAuthState(authDir);

    const sock = makeWASocket({
        auth: state,
        printQRInTerminal: false
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            const qrFile = `/tmp/yuki-${sessionName}-qr.png`;
            QRCode.toFile(qrFile, qr, {
                width: 800,
                margin: 2
            }).then(() => {
                console.log(`\n📱 QR ${sessionName.toUpperCase()} dibuat: ${qrFile}`);
                console.log(`Buka file tersebut untuk scan dengan WhatsApp.`);
            }).catch(err => {
                console.error('❌ Gagal membuat QR PNG:', err);
            });
        }

        if (connection === 'close') {
            const shouldReconnect =
                lastDisconnect?.error?.output?.statusCode !==
                DisconnectReason.loggedOut;

            if (shouldReconnect) {
                console.log('🔄 WhatsApp terputus. Menghubungkan kembali...');
                startBot(sessionName);
            } else {
                console.log('❌ WhatsApp logout.');
            }

        } else if (connection === 'open') {
            console.log(`\n✅ Bot Yuki WhatsApp ${sessionName.toUpperCase()} Siap Digunakan!`);
            console.log('🎵 Music source: YouTube via yt-dlp');
            console.log('▶️ Engine musik: yt-dlp.');
        }
    });


    sock.ev.on('messages.upsert', async (m) => {
        const msg = m.messages[0];

        if (!msg || !msg.message) return;

        const from = msg.key.remoteJid;

        const text =
            msg.message.conversation ||
            msg.message.extendedTextMessage?.text ||
            '';

        const lowerText = text.toLowerCase().trim();

        if (lowerText === 'ping' || lowerText === '.ping') { await sock.sendMessage(from, { text: 'Pong! 🏓 Bot Yuki Aktif.' }); return; }
        if (lowerText === 'help' || lowerText === '.help') {
        await sock.sendMessage(from, {
            text: `🤖 YUKI BOT

🎵 Musik
• play [judul] — Putar audio
• .play [judul] — Putar audio
• vplay [judul] — Putar video

ℹ️ Lainnya
• help — Menampilkan bantuan`
        });
        return;
    }

if (lowerText.startsWith('vplay')) {
            let query = text.slice(5).trim();
            query = query.replace(/^lagu\s+/i, '').trim();

            if (!query) {
                await sock.sendMessage(from, {
                    text: "🎬 Ketik: vplay [judul lagu/artis]"
                });
                return;
            }

            console.log(`🎬 WhatsApp VPLAY: ${query}`);

            await sock.sendMessage(from, {
                text: `🔍 Mencari video: "${query}"...`
            });

            const result = await searchAndDownloadVideo(query);

            if (!result.ok) {
                await sock.sendMessage(from, {
                    text: `❌ ${result.error || 'Video tidak ditemukan.'}`
                });
                return;
            }

            const videoFile = result.file;

            try {
                console.log(`🎬 Mengirim video: ${result.title}`);

                await sock.sendMessage(from, {
                    text: `🎬 ${result.title}\n\nMengirim video...`
                });

                await sock.sendMessage(from, {
                    video: {
                        url: videoFile
                    },
                    mimetype: 'video/mp4',
                    caption: result.title
                });

                console.log('✅ Video berhasil dikirim ke WhatsApp.');

            } catch (error) {
                console.error('❌ Gagal mengirim video:', error);

                await sock.sendMessage(from, {
                    text: '❌ Gagal mengirim video ke WhatsApp.'
                });

            } finally {
                try {
                    if (result.dir && fs.existsSync(result.dir)) {
                        fs.rmSync(result.dir, {
                            recursive: true,
                            force: true
                        });
                    }
                } catch (e) {
                    console.error(
                        '⚠️ Gagal membersihkan video:',
                        e.message
                    );
                }
            }

            return;
        }

        if (!lowerText.startsWith('putar') && !lowerText.startsWith('.play')) return;

        let query;

        if (lowerText.startsWith('.play')) {
            query = text.slice(5).trim();
        } else {
            query = text.slice(5).trim();
        }

        // Buang kata "lagu" jika hanya menjadi awalan perintah.
        query = query.replace(/^lagu\s+/i, '').trim();

        if (!query) {
            await sock.sendMessage(from, {
                text: "🎵 Ketik: putar [judul lagu/artis]"
            });
            return;
        }

        console.log(`📩 WhatsApp: ${query}`);

        await sock.sendMessage(from, {
            text: `🔍 Mencari lagu: "${query}"...`
        });

        // Cari & download menggunakan engine yang sama dengan Telegram
        const result = await searchAndDownload(query);

        if (!result.ok) {
            console.log(`❌ Gagal: ${result.error}`);

            await sock.sendMessage(from, {
                text: `❌ ${result.error || 'Lagu tidak ditemukan.'}`
            });

            return;
        }

        const audioFile = result.file;

        if (!audioFile || !fs.existsSync(audioFile)) {
            await sock.sendMessage(from, {
                text: '❌ File audio tidak ditemukan.'
            });
            return;
        }

        console.log(
            `🎶 Mengirim: ${result.title} - ${result.artist}`
        );

        await sock.sendMessage(from, {
            text: `🎶 ${result.title}\n👤 ${result.artist}\n\nMengirim audio...`
        });

        try {
            await sock.sendMessage(from, {
                audio: {
                    url: audioFile
                },
                mimetype: 'audio/mp4',
                ptt: false
            });

            console.log('✅ Audio berhasil dikirim ke WhatsApp.');

        } catch (error) {
            console.error('❌ Gagal mengirim audio:', error);

            await sock.sendMessage(from, {
                text: '❌ Gagal mengirim file audio ke WhatsApp.'
            });

        } finally {
            // Hapus temporary file dan foldernya
            try {
                if (fs.existsSync(audioFile)) {
                    fs.unlinkSync(audioFile);
                }

                const tempDir = require('path').dirname(audioFile);

                if (
                    tempDir.startsWith('/tmp/yuki_music_') &&
                    fs.existsSync(tempDir)
                ) {
                    fs.rmSync(tempDir, {
                        recursive: true,
                        force: true
                    });
                }

            } catch (e) {
                console.error(
                    '⚠️ Gagal membersihkan temporary file:',
                    e.message
                );
            }
        }
    });
}


startBot('wa1');
startBot('wa2');

startBot('wa3');
