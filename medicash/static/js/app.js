let token = null;

async function requestOtp() {
  const email = document.getElementById('email').value;
  const res = await fetch('/auth/request-otp', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ email }) });
  const data = await res.json();
  document.getElementById('authStatus').textContent = `OTP sent. Demo code: ${data.demo_code}`;
}

async function verifyOtp() {
  const email = document.getElementById('email').value;
  const code = document.getElementById('code').value;
  const res = await fetch('/auth/verify-otp', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ email, code }) });
  const data = await res.json();
  token = data.token;
  document.getElementById('authStatus').textContent = `Signed in: ${data.user_id}`;
  document.getElementById('cards').style.display = 'block';
  document.getElementById('remit').style.display = 'block';
  refreshCards();
}

async function createCard() {
  const label = document.getElementById('cardLabel').value;
  const type = document.getElementById('cardType').value;
  const res = await fetch('/cards/create', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body: JSON.stringify({ label, type })});
  await res.json();
  await refreshCards();
}

async function refreshCards() {
  const res = await fetch('/cards', { headers: { 'Authorization': `Bearer ${token}` }});
  const data = await res.json();
  const ul = document.getElementById('cardList');
  ul.innerHTML = '';
  data.forEach(c => {
    const li = document.createElement('li');
    li.textContent = `${c.label} [${c.type}] - ${c.status}`;
    const freezeBtn = document.createElement('button');
    freezeBtn.textContent = c.status === 'frozen' ? 'Unfreeze' : 'Freeze';
    freezeBtn.onclick = async () => {
      const endpoint = c.status === 'frozen' ? 'unfreeze' : 'freeze';
      await fetch(`/cards/${c.id}/${endpoint}`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } });
      refreshCards();
    };
    const reissueBtn = document.createElement('button');
    reissueBtn.textContent = 'Reissue';
    reissueBtn.onclick = async () => {
      await fetch(`/cards/${c.id}/reissue`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } });
      refreshCards();
    };
    li.appendChild(freezeBtn);
    li.appendChild(reissueBtn);
    ul.appendChild(li);
  });
}

async function quote() {
  const send_amount = parseFloat(document.getElementById('sendAmount').value);
  const send_currency = document.getElementById('sendCur').value;
  const receive_currency = document.getElementById('recvCur').value;
  const res = await fetch('/remit/quote', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body: JSON.stringify({ send_amount, send_currency, receive_currency }) });
  const data = await res.json();
  document.getElementById('quoteOut').textContent = JSON.stringify(data, null, 2);
}
