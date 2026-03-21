export const config = {
  api: {
    bodyParser: false, // Ham istek gövdesini almak için
  },
};

export default async function handler(req, res) {
  // CORS başlıkları
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', '*');

  // Preflight isteği
  if (req.method === 'OPTIONS') return res.status(200).end();

  // Sadece POST isteklerine izin ver
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  try {
    // İstek gövdesini buffer'da topla
    const chunks = [];
    for await (const chunk of req) {
      chunks.push(chunk);
    }
    const body = Buffer.concat(chunks);
    const contentType = req.headers['content-type'] || '';

    // Groq API'ye isteği ilet
    const groqRes = await fetch('https://api.groq.com/openai/v1/audio/transcriptions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${process.env.GROQ_API_KEY}`,
        'Content-Type': contentType,
      },
      body,
    });

    // Groq'dan dönen Content-Type başlığını istemciye aktar
    const responseContentType = groqRes.headers.get('content-type');
    if (responseContentType) {
      res.setHeader('Content-Type', responseContentType);
    }

    // Yanıt gövdesini al ve istemciye gönder
    const responseBody = await groqRes.text();
    res.status(groqRes.status).send(responseBody);
  } catch (error) {
    console.error('Proxy hatası:', error);
    res.status(500).json({ error: 'Internal Server Error', details: error.message });
  }
}
