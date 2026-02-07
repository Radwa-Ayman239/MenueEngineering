const http = require('http');

function postRequest(path, data) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'localhost',
      port: 8000,
      path: path,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
      }
    };

    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          text: body
        });
      });
    });

    req.on('error', (e) => reject(e));
    req.write(data);
    req.end();
  });
}

async function testLogin() {
  const email = 'manager@example.com';
  const password = 'password123';

  console.log('--- Step 1: Login ---');
  try {
    const res1 = await postRequest('/api/users/login/', JSON.stringify({ email, password }));
    
    console.log('Step 1 Status:', res1.status);
    console.log('Step 1 Response:', res1.text);

    if (res1.status !== 200) throw new Error('Step 1 failed');
    
    const data1 = JSON.parse(res1.text);
    if (!data1.session_token) throw new Error('No session token returned');

    console.log('\nSuccess! Session Token received.');
    console.log(data1.session_token);
    
  } catch (err) {
    console.error('Error:', err);
  }
}

testLogin();
